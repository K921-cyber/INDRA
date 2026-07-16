"""
TRINETRA — Test Fixtures

Provides an in-memory SQLite database for integration-style
testing of the watch service, alert detection, and API routes.
All tests use a fresh database per session to avoid cross-test
contamination.

IMPORTANT: ``DATABASE_URL`` is set to in-memory SQLite at the
module level (before any app imports) so that the app's own
``async_session_factory`` connects to an in-memory DB.  Test
tables are created on that same engine so that service functions
transparently use the test database without monkeypatching.
"""

import os
import tempfile

# Use a temporary file-based SQLite database for tests.
# With NullPool, each async_session_factory() call creates a new connection,
# and in-memory SQLite databases are per-connection.  A file-based DB
# persists across all connections so tables are visible everywhere.
_test_db_fd, _test_db_path = tempfile.mkstemp(suffix=".db", prefix="trinetra_test_")
os.close(_test_db_fd)  # Close the fd — aiosqlite will open it itself
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{_test_db_path}"

import json  # noqa: E402
from typing import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
import pytest_asyncio  # noqa: E402
from sqlalchemy import text  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

# ── Force the app's database module to initialise with the  ──
#    in-memory URL set above.
from app.services import database as db_mod  # noqa: E402

# Grab the engine that was created when database.py was imported.
_test_engine = db_mod.engine


# ── DDL statements (mirrors _ensure_db_tables in main.py) ──

DDL_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS scan_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target TEXT NOT NULL,
        target_type TEXT NOT NULL,
        plugin_id TEXT NOT NULL,
        plugin_name TEXT NOT NULL,
        category TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'completed',
        gui_data TEXT DEFAULT '{}',
        terminal_data TEXT DEFAULT '',
        freshness TEXT DEFAULT 'fresh',
        error TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS watches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        target TEXT NOT NULL,
        target_type TEXT NOT NULL,
        plugin_ids TEXT DEFAULT '[]',
        interval_seconds INTEGER DEFAULT 3600,
        webhook_url TEXT,
        email TEXT,
        is_active INTEGER DEFAULT 1,
        last_checked_at TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        watch_id INTEGER REFERENCES watches(id) ON DELETE CASCADE,
        target TEXT NOT NULL,
        plugin_id TEXT NOT NULL,
        old_data TEXT DEFAULT '{}',
        new_data TEXT DEFAULT '{}',
        summary TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_watches_active ON watches(is_active, last_checked_at)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_scan_results_target ON scan_results(target)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_alerts_watch_id ON alerts(watch_id)
    """,
]


# ── Session-scoped: create tables once ───────────────────


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _create_tables():
    """Create all test tables on the app's engine at session start."""
    async with _test_engine.begin() as conn:
        for ddl in DDL_STATEMENTS:
            await conn.execute(text(ddl))
    yield
    # Session-end cleanup: drop tables and remove temp DB file
    async with _test_engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS alerts"))
        await conn.execute(text("DROP TABLE IF EXISTS scan_results"))
        await conn.execute(text("DROP TABLE IF EXISTS watches"))
    # Clean up the temp file
    try:
        os.unlink(_test_db_path)
    except OSError:
        pass


# ── Per-test: clean DB session ───────────────────────────


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a clean session from the app's engine.

    The session is rolled back after each test so that test data
    never leaks between tests.
    """
    # Clean all tables before the test so that data written
    # by service functions (which use their own sessions) does
    # not leak between tests.
    async with db_mod.async_session_factory() as s:
        for table in ("alerts", "scan_results", "watches"):
            await s.execute(text(f"DELETE FROM {table}"))
        await s.commit()

    async with db_mod.async_session_factory() as s:
        yield s
        await s.rollback()


# ── Helper: insert a test watch ─────────────────────────


async def insert_watch(
    session: AsyncSession,
    target: str = "example.com",
    target_type: str = "domain",
    plugin_ids: list[str] | None = None,
    interval_seconds: int = 3600,
    is_active: int = 1,
) -> dict:
    """Insert a watch directly and return its row as a dict."""
    result = await session.execute(
        text("""
            INSERT INTO watches (target, target_type, plugin_ids, interval_seconds, webhook_url, email)
            VALUES (:target, :target_type, :plugin_ids, :interval_seconds, :webhook_url, :email)
        """),
        {
            "target": target,
            "target_type": target_type,
            "plugin_ids": json.dumps(plugin_ids or []),
            "interval_seconds": interval_seconds,
            "webhook_url": "",
            "email": "",
        },
    )
    await session.commit()

    last_id = result.lastrowid
    row = (await session.execute(
        text(db_mod.q("get_watch")), {"id": last_id}
    )).first()
    assert row is not None, "Failed to insert test watch"
    w = dict(row._mapping)
    w["plugin_ids"] = json.loads(w.get("plugin_ids") or "[]")
    w["is_active"] = bool(w.get("is_active"))
    return w


# ── Helper: insert a test scan result ───────────────────


async def insert_scan(
    session: AsyncSession,
    target: str = "example.com",
    target_type: str = "domain",
    plugin_id: str = "http-headers",
    plugin_name: str = "HTTP Headers",
    category: str = "infrastructure",
    gui_data: dict | None = None,
    terminal_data: str = "",
    status: str = "completed",
    freshness: str = "moments",
):
    """Insert a scan result directly."""
    await session.execute(
        text(db_mod.q("save_scan")),
        {
            "target": target,
            "target_type": target_type,
            "plugin_id": plugin_id,
            "plugin_name": plugin_name,
            "category": category,
            "status": status,
            "gui_data": json.dumps(gui_data or {}),
            "terminal_data": terminal_data,
            "freshness": freshness,
        },
    )
    await session.commit()
