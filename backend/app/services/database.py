"""
TRINETRA — Async Database Service

Provides async SQLAlchemy engine + session factory and
**DB-backend-aware** raw SQL helpers. Two sets of queries
are maintained — one for PostgreSQL (production / Docker)
and one for SQLite (local dev).

Usage:
    async with get_session() as db:
        result = await db.execute(text(RAW_SQL_PG["create_watch"]), {...})
"""

import logging
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, StaticPool
from app.core.config import settings

logger = logging.getLogger("trinetra.db")

# ── Engine ────────────────────────────────────────────────

_using_sqlite = settings.database_url.startswith("sqlite")
# Use NullPool for SQLite so each session gets its own connection.
# Combined with WAL journal mode, this prevents "database is locked"
# errors when concurrent requests (API + watch scheduler) access the DB.
poolclass = NullPool

engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    poolclass=poolclass,
    connect_args={"timeout": 30} if _using_sqlite else {},
)


# Enable WAL journal mode and busy_timeout for SQLite
if _using_sqlite:
    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=30000")  # 30s
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
    logger.info("SQLite WAL mode + busy_timeout=30s + NullPool enabled")

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncSession:  # type: ignore[misc]
    """Yield an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


# ── SQL Queries (DB-backend-aware) ─────────────────────────
# For SQLite: plugin_ids stored as JSON array string (TEXT),
#             last_checked_at as ISO-8601 text,
#             is_active as 0/1 INTEGER.
# For PostgreSQL: native ARRAY, TIMESTAMPTZ, BOOLEAN.
#
# The check_due_watches logic uses epoch-seconds math for SQLite
# instead of INTERVAL syntax.

# ── PostgreSQL queries ───────────────────────────────────

RAW_SQL_PG: dict[str, str] = {
    "create_watch": """
        INSERT INTO watches (target, target_type, plugin_ids, interval_seconds, webhook_url, email)
        VALUES (:target, :target_type, :plugin_ids, :interval_seconds, :webhook_url, :email)
        RETURNING id, target, target_type, plugin_ids, interval_seconds, webhook_url, email, is_active, last_checked_at, created_at
    """,
    "list_watches": """
        SELECT id, target, target_type, plugin_ids, interval_seconds, webhook_url, email,
               is_active, last_checked_at, created_at
        FROM watches ORDER BY created_at DESC
    """,
    "get_watch": """
        SELECT id, target, target_type, plugin_ids, interval_seconds, webhook_url, email,
               is_active, last_checked_at, created_at
        FROM watches WHERE id = :id
    """,
    "delete_watch": "DELETE FROM watches WHERE id = :id",
    "toggle_watch": """
        UPDATE watches SET is_active = NOT is_active WHERE id = :id
        RETURNING id, is_active
    """,
    "update_last_checked": "UPDATE watches SET last_checked_at = NOW() WHERE id = :id",
    "due_watches": """
        SELECT id, target, target_type, plugin_ids, interval_seconds, webhook_url, email,
               is_active, last_checked_at, created_at
        FROM watches
        WHERE is_active = TRUE
          AND (last_checked_at IS NULL
               OR last_checked_at <= NOW() - (interval_seconds * INTERVAL '1 second'))
    """,
    "list_alerts": """
        SELECT id, watch_id, target, plugin_id, old_data, new_data, summary, created_at
        FROM alerts ORDER BY created_at DESC LIMIT :limit
    """,
    "list_alerts_for_watch": """
        SELECT id, watch_id, target, plugin_id, old_data, new_data, summary, created_at
        FROM alerts WHERE watch_id = :watch_id ORDER BY created_at DESC
    """,
    "create_alert": """
        INSERT INTO alerts (watch_id, target, plugin_id, old_data, new_data, summary)
        VALUES (:watch_id, :target, :plugin_id, CAST(:old_data AS jsonb), CAST(:new_data AS jsonb), :summary)
        RETURNING id, watch_id, target, plugin_id, old_data, new_data, summary, created_at
    """,
    "get_latest_scan": """
        SELECT id, target, plugin_id, plugin_name, gui_data, terminal_data, created_at
        FROM scan_results
        WHERE target = :target AND plugin_id = :plugin_id
        ORDER BY created_at DESC LIMIT 1
    """,
    "save_scan": """
        INSERT INTO scan_results (target, target_type, plugin_id, plugin_name, category, status, gui_data, terminal_data, freshness)
        VALUES (:target, :target_type, :plugin_id, :plugin_name, :category, :status, CAST(:gui_data AS jsonb), :terminal_data, :freshness)
    """,
}

# ── SQLite queries ────────────────────────────────────────

RAW_SQL_SQLITE: dict[str, str] = {
    "create_watch": """
        INSERT INTO watches (target, target_type, plugin_ids, interval_seconds, webhook_url, email)
        VALUES (:target, :target_type, :plugin_ids, :interval_seconds, :webhook_url, :email)
    """,
    "list_watches": """
        SELECT id, target, target_type, plugin_ids, interval_seconds, webhook_url, email,
               is_active, last_checked_at, created_at
        FROM watches ORDER BY created_at DESC
    """,
    "get_watch": """
        SELECT id, target, target_type, plugin_ids, interval_seconds, webhook_url, email,
               is_active, last_checked_at, created_at
        FROM watches WHERE id = :id
    """,
    "delete_watch": "DELETE FROM watches WHERE id = :id",
    "toggle_watch": "UPDATE watches SET is_active = CAST(NOT is_active AS INTEGER) WHERE id = :id",
    "update_last_checked": "UPDATE watches SET last_checked_at = datetime('now') WHERE id = :id",
    "due_watches": """
        SELECT id, target, target_type, plugin_ids, interval_seconds, webhook_url, email,
               is_active, last_checked_at, created_at
        FROM watches
        WHERE is_active = 1
          AND (last_checked_at IS NULL
               OR CAST(strftime('%s', 'now') AS INTEGER) - CAST(strftime('%s', last_checked_at) AS INTEGER) >= interval_seconds)
    """,
    "list_alerts": """
        SELECT id, watch_id, target, plugin_id, old_data, new_data, summary, created_at
        FROM alerts ORDER BY created_at DESC LIMIT :limit
    """,
    "list_alerts_for_watch": """
        SELECT id, watch_id, target, plugin_id, old_data, new_data, summary, created_at
        FROM alerts WHERE watch_id = :watch_id ORDER BY created_at DESC
    """,
    "create_alert": """
        INSERT INTO alerts (watch_id, target, plugin_id, old_data, new_data, summary)
        VALUES (:watch_id, :target, :plugin_id, :old_data, :new_data, :summary)
    """,
    "get_latest_scan": """
        SELECT id, target, plugin_id, plugin_name, gui_data, terminal_data, created_at
        FROM scan_results
        WHERE target = :target AND plugin_id = :plugin_id
        ORDER BY created_at DESC LIMIT 1
    """,
    "save_scan": """
        INSERT INTO scan_results (target, target_type, plugin_id, plugin_name, category, status, gui_data, terminal_data, freshness)
        VALUES (:target, :target_type, :plugin_id, :plugin_name, :category, :status, :gui_data, :terminal_data, :freshness)
    """,
}


# ── Query selector ────────────────────────────────────────

def _get_sql() -> dict[str, str]:
    """Return the correct SQL dict for the current DB backend."""
    return RAW_SQL_SQLITE if _using_sqlite else RAW_SQL_PG


def q(name: str) -> str:
    """Get a named SQL query for the current DB backend."""
    return _get_sql()[name]


# ── Helpers ───────────────────────────────────────────────

def parse_plugin_ids(raw, using_sqlite: bool | None = None) -> list[str]:
    """Parse plugin_ids from DB row into a list of strings.

    PostgreSQL returns a Python list natively. SQLite returns
    a JSON-encoded string (e.g. ``'[\"foo\",\"bar\"]'``) stored as TEXT.
    """
    if raw is None:
        return []
    if isinstance(raw, list):
        return raw
    if isinstance(raw, str):
        import json
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            # Fallback: comma-separated
            return [p.strip() for p in raw.strip("[]").split(",") if p.strip()]
    return []
