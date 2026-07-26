"""
TRINETRA — Taskiq Broker Setup

Configures a Taskiq async broker backed by Redis (production) or
in-memory (development). The broker distributes background tasks
(watch re-checks, alert generation) to worker processes.

Worker startup (Docker):
    taskiq worker app.tasks.broker:broker app.tasks.watch_tasks
"""

from app.core.config import settings

# Determine which broker to use
_redis_available = bool(settings.redis_url)


def _create_broker():
    if _redis_available:
        from taskiq_redis import ListQueueBroker, RedisAsyncResultBackend

        broker = ListQueueBroker(
            url=settings.redis_url,  # type: ignore
            result_backend=RedisAsyncResultBackend(
                settings.redis_url,  # type: ignore
            ),
        )
    else:
        # Fallback: in-memory broker for local dev
        from taskiq import InMemoryBroker

        broker = InMemoryBroker()

    return broker


broker = _create_broker()
_is_inmemory = not _redis_available
