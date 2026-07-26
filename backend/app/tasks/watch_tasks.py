"""
TRINETRA — Background Watch Tasks

Taskiq-decorated functions that execute watch re-checks.
Each task is dispatched by the scheduler and picked up
by a Taskiq worker (or runs inline in dev mode).
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from sqlalchemy import text
from app.tasks.broker import broker, _is_inmemory
from app.services.database import async_session_factory, q, _using_sqlite, parse_plugin_ids
from app.services.orchestrator import OrchestratorService
from taskiq.message import TaskiqMessage

logger = logging.getLogger("trinetra.watch_tasks")

# ── Shared orchestrator (lazily created, thread/async-safe because
#     the registry is populated once at startup) ──────────────────
_orch: OrchestratorService | None = None


def _get_orch() -> OrchestratorService:
    global _orch
    if _orch is None:
        _orch = OrchestratorService()
    return _orch


# ── Task: scan a single watch target ──────────────────────────────


@broker.task(task_name="scan_watch")
async def scan_watch(
    watch_id: int,
    target: str,
    target_type: str,
    plugin_ids: list[str] | None = None,
) -> dict:
    """Run OSINT plugins against a watched target and detect changes.

    This is the core background task executed by Taskiq workers.
    It compares fresh results with the most recent scan and creates
    alerts for any differences found.
    """
    orch = _get_orch()
    results: list[dict] = []

    if plugin_ids:
        # Run only the specified plugins
        for pid in plugin_ids:
            plugin = orch.plugin_registry.get(pid)
            if plugin and target_type in plugin.input_types:
                r = await plugin.run_safe(target)
                if r:
                    results.append(r.to_dict())
    else:
        # Run all matching plugins
        results = await orch.run_all(target, target_type)

    # Save results and detect changes — retry on transient SQLite lock errors
    max_retries = 3
    for attempt in range(max_retries):
        try:
            await _save_watch_results(watch_id, target, target_type, results)
            break
        except Exception as e:
            error_msg = str(e).lower()
            if "database is locked" in error_msg or "busy" in error_msg:
                if attempt < max_retries - 1:
                    wait = 2 ** attempt
                    logger.warning(
                        "SQLite lock contention on watch %d (attempt %d/%d), retrying in %ds",
                        watch_id, attempt + 1, max_retries, wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        "SQLite lock contention on watch %d after %d attempts: %s",
                        watch_id, max_retries, e,
                    )
                    raise
            else:
                raise

    return {
        "watch_id": watch_id,
        "target": target,
        "plugins_run": len(results),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


async def _save_watch_results(
    watch_id: int,
    target: str,
    target_type: str,
    results: list[dict],
) -> None:
    """Save scan results and create alerts for detected changes."""
    async with async_session_factory() as db:
        for r in results:
            gui_json = json.dumps(r.get("gui_data", {}))

            # Fetch the *previous* scan for this plugin + target
            # (MUST happen BEFORE saving the new scan, otherwise we'd compare
            #  the new data against itself — the row we just inserted)
            prev_row = (
                await db.execute(
                    text(q("get_latest_scan")),
                    {
                        "target": target,
                        "plugin_id": r["plugin_id"],
                    },
                )
            ).first()

            # Save new scan result
            await db.execute(
                text(q("save_scan")),
                {
                    "target": target,
                    "target_type": target_type,
                    "plugin_id": r["plugin_id"],
                    "plugin_name": r["plugin_name"],
                    "category": r["category"],
                    "status": r["status"],
                    "gui_data": gui_json if _using_sqlite else gui_json,
                    "terminal_data": r.get("terminal_data", ""),
                    "freshness": r.get("freshness", "moments"),
                },
            )

            # Detect changes (skip first scan — nothing to compare)
            if prev_row is not None:
                prev_gui_raw = prev_row._mapping.get("gui_data")
                prev_gui = _parse_gui_data(prev_gui_raw)
                current_gui = r.get("gui_data", {})
                if prev_gui and prev_gui != current_gui:
                    summary = _summarize_diff(prev_gui, current_gui, r["plugin_name"])
                    old_json = json.dumps(prev_gui)
                    new_json = json.dumps(current_gui)
                    await db.execute(
                        text(q("create_alert")),
                        {
                            "watch_id": watch_id,
                            "target": target,
                            "plugin_id": r["plugin_id"],
                            "old_data": old_json if _using_sqlite else old_json,
                            "new_data": new_json if _using_sqlite else new_json,
                            "summary": summary,
                        },
                    )

        # Update last_checked timestamp
        await db.execute(text(q("update_last_checked")), {"id": watch_id})
        await db.commit()

    logger.info("Saved %d results for watch %d (%s)", len(results), watch_id, target)


def _parse_gui_data(raw) -> dict:
    """Parse gui_data from DB — could be a dict (PG) or a JSON string (SQLite)."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}


def _summarize_diff(
    old: dict,
    new: dict,
    plugin_name: str,
) -> str:
    """Build a human-readable summary of what changed between two results."""
    changes: list[str] = []
    all_keys = set(old.keys()) | set(new.keys())

    for key in sorted(all_keys):
        old_val = old.get(key)
        new_val = new.get(key)
        if old_val != new_val:
            old_str = str(old_val)[:80] if old_val is not None else "(none)"
            new_str = str(new_val)[:80] if new_val is not None else "(none)"
            changes.append(f"{key}: {old_str} → {new_str}")

    if not changes:
        return f"{plugin_name}: No significant changes detected."

    return f"{plugin_name}: {len(changes)} change(s) — " + "; ".join(changes[:5])


# ── Task: periodic check for due watches ───────────────────────


@broker.task(task_name="check_due_watches")
async def check_due_watches() -> dict:
    """Find all watches that are due for a re-check and enqueue scan tasks.

    This is the main scheduler task — it runs every 60 seconds,
    queries the ``watches`` table for active watches whose
    ``last_checked_at`` is past the configured interval, and
    dispatches individual ``scan_watch`` tasks for each.
    """
    async with async_session_factory() as db:
        rows = (await db.execute(text(q("due_watches")))).all()

    if not rows:
        return {"watches_due": 0, "message": "No watches due"}

    enqueued = 0
    for row in rows:
        w = dict(row._mapping)
        plugin_ids = parse_plugin_ids(w.get("plugin_ids"), _using_sqlite)
        args = [w["id"], w["target"], w["target_type"], plugin_ids]

        if _is_inmemory:
            # InMemoryBroker executes tasks inline — call directly
            await scan_watch(*args)
        else:
            # ListQueueBroker.kick() takes a BrokerMessage (async)
            msg = broker.formatter.dumps(TaskiqMessage(
                task_id="",
                task_name="scan_watch",
                args=tuple(args),
                kwargs={},
                labels={},
            ))
            await broker.kick(msg)
        enqueued += 1

    return {
        "watches_due": enqueued,
        "message": f"Enqueued {enqueued} watch scan(s)",
    }
