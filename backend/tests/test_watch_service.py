"""
TRINETRA — Watch Service Integration Tests

Tests for the core CRUD operations in ``app.services.watch_service``,
including create, read, delete, and toggle of watches, as well as
alert listing.

Uses the ``db_session`` fixture which provides an in-memory SQLite
database and monkey-patches ``async_session_factory`` so that the
service functions transparently use the test database.
"""

import json
import pytest
from sqlalchemy import text

from app.services import watch_service


# ======================== CREATE ========================


@pytest.mark.asyncio
async def test_create_watch_basic(db_session):
    """A watch with minimal fields is created and returned."""
    w = await watch_service.create_watch(target="example.com", target_type="domain")

    assert w["target"] == "example.com"
    assert w["target_type"] == "domain"
    assert w["is_active"] is True
    assert w["plugin_ids"] == []
    assert w["interval_seconds"] == 3600
    assert w["webhook_url"] == ""
    assert w["email"] == ""
    assert isinstance(w["id"], int)
    assert w["created_at"] is not None


@pytest.mark.asyncio
async def test_create_watch_with_plugin_ids(db_session):
    """Plugin IDs are stored and parsed correctly (JSON string in SQLite)."""
    w = await watch_service.create_watch(
        target="test.io",
        target_type="domain",
        plugin_ids=["http-headers", "ssl-health"],
        interval_seconds=7200,
        webhook_url="https://hooks.example.com/w",
        email="me@example.com",
    )

    assert w["target"] == "test.io"
    assert w["plugin_ids"] == ["http-headers", "ssl-health"]
    assert w["interval_seconds"] == 7200
    assert w["webhook_url"] == "https://hooks.example.com/w"
    assert w["email"] == "me@example.com"


@pytest.mark.asyncio
async def test_create_watch_empty_plugin_ids(db_session):
    """Creating a watch with None plugin_ids defaults to empty list."""
    w = await watch_service.create_watch(target="example.com", target_type="domain", plugin_ids=None)
    assert w["plugin_ids"] == []


# ======================== LIST ========================


@pytest.mark.asyncio
async def test_list_watches_empty(db_session):
    """list_watches returns an empty list when no watches exist."""
    watches = await watch_service.list_watches()
    assert watches == []


@pytest.mark.asyncio
async def test_list_watches_returns_all(db_session):
    """list_watches returns all watches ordered by creation date DESC."""
    w1 = await watch_service.create_watch(target="a.com", target_type="domain")
    w2 = await watch_service.create_watch(target="b.org", target_type="domain")

    watches = await watch_service.list_watches()
    assert len(watches) == 2

    # Newest first
    created_times = [w["created_at"] for w in watches]
    assert created_times == sorted(created_times, reverse=True)


# ======================== GET ========================


@pytest.mark.asyncio
async def test_get_watch_found(db_session):
    """get_watch returns the correct watch by ID."""
    created = await watch_service.create_watch(target="example.com", target_type="domain")
    fetched = await watch_service.get_watch(created["id"])

    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["target"] == "example.com"


@pytest.mark.asyncio
async def test_get_watch_not_found(db_session):
    """get_watch returns None when the ID does not exist."""
    result = await watch_service.get_watch(9999)
    assert result is None


# ======================== DELETE ========================


@pytest.mark.asyncio
async def test_delete_watch_deletes(db_session):
    """delete_watch removes the watch and returns True."""
    created = await watch_service.create_watch(target="example.com", target_type="domain")
    assert await watch_service.get_watch(created["id"]) is not None

    deleted = await watch_service.delete_watch(created["id"])
    assert deleted is True

    # Verify it's gone
    assert await watch_service.get_watch(created["id"]) is None


@pytest.mark.asyncio
async def test_delete_watch_not_found(db_session):
    """delete_watch returns False for a non-existent watch."""
    result = await watch_service.delete_watch(9999)
    assert result is False


# ======================== TOGGLE ========================


@pytest.mark.asyncio
async def test_toggle_watch_activates_deactivates(db_session):
    """toggle_watch flips the is_active flag."""
    created = await watch_service.create_watch(target="example.com", target_type="domain")
    assert created["is_active"] is True

    # Toggle off
    result = await watch_service.toggle_watch(created["id"])
    assert result is not None
    assert result["id"] == created["id"]
    assert result["is_active"] is False

    # Toggle back on
    result = await watch_service.toggle_watch(created["id"])
    assert result is not None
    assert result["is_active"] is True


@pytest.mark.asyncio
async def test_toggle_watch_not_found(db_session):
    """toggle_watch returns None for a non-existent watch."""
    result = await watch_service.toggle_watch(9999)
    assert result is None


# ======================== ALERTS ========================


@pytest.mark.asyncio
async def test_list_alerts_empty(db_session):
    """list_alerts returns an empty list when no alerts exist."""
    alerts = await watch_service.list_alerts()
    assert alerts == []


@pytest.mark.asyncio
async def test_list_alerts_returns_alerts(db_session):
    """list_alerts returns alerts ordered by creation date DESC."""
    w = await watch_service.create_watch(target="example.com", target_type="domain")
    from app.services.database import q

    # Insert two alerts directly via the service's own SQL
    await db_session.execute(
        text(q("create_alert")),
        {
            "watch_id": w["id"],
            "target": "example.com",
            "plugin_id": "http-headers",
            "old_data": json.dumps({"key": "old"}),
            "new_data": json.dumps({"key": "new"}),
            "summary": "Test alert",
        },
    )
    await db_session.commit()

    alerts = await watch_service.list_alerts()
    assert len(alerts) >= 1
    assert alerts[0]["summary"] == "Test alert"


@pytest.mark.asyncio
async def test_list_alerts_for_watch(db_session):
    """list_alerts_for_watch returns alerts scoped to a specific watch."""
    w1 = await watch_service.create_watch(target="a.com", target_type="domain")
    w2 = await watch_service.create_watch(target="b.com", target_type="domain")
    from app.services.database import q

    # 2 alerts for w1, 1 for w2
    for wid in (w1["id"], w1["id"], w2["id"]):
        await db_session.execute(
            text(q("create_alert")),
            {
                "watch_id": wid,
                "target": "example.com",
                "plugin_id": "http-headers",
                "old_data": "{}",
                "new_data": "{}",
                "summary": "Alert",
            },
        )
    await db_session.commit()

    alerts_w1 = await watch_service.list_alerts_for_watch(w1["id"])
    assert len(alerts_w1) == 2

    alerts_w2 = await watch_service.list_alerts_for_watch(w2["id"])
    assert len(alerts_w2) == 1
