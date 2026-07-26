"""
TRINETRA — Background Watch Scheduler

Runs a periodic background loop (every 60 seconds by default) that
checks the ``watches`` table for targets due for re-scanning and
dispatches ``scan_watch`` tasks via the Taskiq broker.

In development mode (no Redis / no separate worker) the tasks are
executed **inline** so that the system works without a worker process.
For production, the Docker Compose setup includes a dedicated
Taskiq worker container.
"""

import asyncio
import logging

from app.tasks.watch_tasks import check_due_watches

logger = logging.getLogger("trinetra.scheduler")

POLL_INTERVAL_SECONDS = 60  # check every 60 s


async def run_watcher_forever() -> None:
    """Entry-point: run the watcher loop for the lifetime of the app.

    Called from FastAPI's ``lifespan`` hook.  The loop periodically
    invokes the scheduler logic and sleeps between iterations.
    """
    logger.info(
        "Watch scheduler started (polling every %ds)", POLL_INTERVAL_SECONDS
    )

    # Small initial delay to let the app finish booting
    await asyncio.sleep(5)

    while True:
        try:
            result = await check_due_watches()
            if result.get("watches_due", 0) > 0:
                logger.info("Watch scheduler: %s", result["message"])
        except asyncio.CancelledError:
            logger.info("Watch scheduler stopped (shutdown)")
            break
        except Exception as exc:
            logger.warning("Watch scheduler error: %s", exc)

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


# ── Scheduler lifecycle helpers ───────────────────────────────

_watcher_task: asyncio.Task[None] | None = None


def start_scheduler() -> None:
    """Start the background watcher asyncio task."""
    global _watcher_task
    if _watcher_task is None or _watcher_task.done():
        _watcher_task = asyncio.create_task(run_watcher_forever())


async def stop_scheduler() -> None:
    """Cancel the background watcher task gracefully."""
    global _watcher_task
    if _watcher_task and not _watcher_task.done():
        _watcher_task.cancel()
        try:
            await _watcher_task
        except asyncio.CancelledError:
            pass
        _watcher_task = None
