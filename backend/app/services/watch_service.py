"""
TRINETRA — Watch Service

Provides CRUD helpers for the ``watches`` and ``alerts`` tables.
All functions accept / return plain dicts and use raw SQL via the
``database`` module so that no ORM models are required.
"""

import json
from typing import Optional
from sqlalchemy import text
from app.services.database import async_session_factory, q, _using_sqlite, parse_plugin_ids


# ── Watches CRUD ─────────────────────────────────────────────


async def create_watch(
    target: str,
    target_type: str,
    plugin_ids: Optional[list[str]] = None,
    interval_seconds: int = 3600,
    webhook_url: Optional[str] = None,
    email: Optional[str] = None,
) -> dict:
    """Create a new watch entry in the database."""
    async with async_session_factory() as db:
        # SQLite stores plugin_ids as JSON string; PG uses native ARRAY
        ids_param: str | list[str] = (
            json.dumps(plugin_ids or [])
            if _using_sqlite
            else (plugin_ids or [])
        )
        result = await db.execute(
            text(q("create_watch")),
            {
                "target": target,
                "target_type": target_type,
                "plugin_ids": ids_param,
                "interval_seconds": interval_seconds,
                "webhook_url": webhook_url or "",
                "email": email or "",
            },
        )
        await db.commit()

        if _using_sqlite:
            # SQLite doesn't support RETURNING; fetch by lastrowid
            last_id = result.lastrowid
            row = (await db.execute(
                text(q("get_watch")), {"id": last_id}
            )).first()
        else:
            row = result.first()

        if row is None:
            return {}
        w = dict(row._mapping)
        w["plugin_ids"] = parse_plugin_ids(w.get("plugin_ids"), _using_sqlite)
        w["is_active"] = bool(w.get("is_active", True))
        return w


async def list_watches() -> list[dict]:
    """Return all watches ordered by creation date (newest first)."""
    async with async_session_factory() as db:
        rows = (await db.execute(text(q("list_watches")))).all()
        watches = []
        for r in rows:
            w = dict(r._mapping)
            w["plugin_ids"] = parse_plugin_ids(w.get("plugin_ids"), _using_sqlite)
            watches.append(w)
        return watches


async def get_watch(watch_id: int) -> Optional[dict]:
    """Get a single watch by ID."""
    async with async_session_factory() as db:
        row = (
            await db.execute(text(q("get_watch")), {"id": watch_id})
        ).first()
        if row is None:
            return None
        w = dict(row._mapping)
        w["plugin_ids"] = parse_plugin_ids(w.get("plugin_ids"), _using_sqlite)
        return w


async def delete_watch(watch_id: int) -> bool:
    """Delete a watch. Returns True if a row was removed."""
    async with async_session_factory() as db:
        result = await db.execute(
            text(q("delete_watch")), {"id": watch_id}
        )
        await db.commit()
        return result.rowcount > 0


async def toggle_watch(watch_id: int) -> Optional[dict]:
    """Toggle a watch's ``is_active`` flag. Returns updated state."""
    async with async_session_factory() as db:
        await db.execute(
            text(q("toggle_watch")), {"id": watch_id}
        )
        await db.commit()
        # Re-fetch to get current state (SQLite has no RETURNING)
        row = (await db.execute(
            text(q("get_watch")), {"id": watch_id}
        )).first()
        if row is None:
            return None
        w = dict(row._mapping)
        w["plugin_ids"] = parse_plugin_ids(w.get("plugin_ids"), _using_sqlite)
        return {"id": w["id"], "is_active": bool(w.get("is_active", False))}


# ── Alerts ───────────────────────────────────────────────────


async def list_alerts(limit: int = 50) -> list[dict]:
    """Return the most recent alerts."""
    async with async_session_factory() as db:
        rows = (
            await db.execute(
                text(q("list_alerts")), {"limit": limit}
            )
        ).all()
        return [dict(r._mapping) for r in rows]


async def list_alerts_for_watch(watch_id: int) -> list[dict]:
    """Return alerts for a specific watch."""
    async with async_session_factory() as db:
        rows = (
            await db.execute(
                text(q("list_alerts_for_watch")),
                {"watch_id": watch_id},
            )
        ).all()
        return [dict(r._mapping) for r in rows]
