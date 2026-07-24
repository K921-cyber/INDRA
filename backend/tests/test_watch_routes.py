"""
TRINETRA — Watch API Route Tests

Tests for the REST endpoints defined in ``app.api.watch_routes``.
Uses FastAPI's ``TestClient`` with the in-memory SQLite database
provided by the ``db_session`` fixture.
"""

import json
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.main import app
from app.services.database import q


# ── Client fixture ───────────────────────────────────────


@pytest.fixture
def client(db_session):
    """Provide a TestClient that uses the monkeypatched database.

    The ``db_session`` fixture patches the app's ``async_session_factory``,
    so all requests made through ``TestClient`` will use our in-memory DB.
    """
    with TestClient(app) as c:
        yield c


# ======================== POST /api/watches ========================


class TestCreateWatch:
    def test_create_basic(self, client):
        """A basic watch is created and returns the correct fields."""
        resp = client.post("/api/watches", json={"target": "example.com"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["target"] == "example.com"
        assert data["target_type"] == "domain"  # auto-detected
        assert data["is_active"] is True
        assert data["plugin_ids"] == []
        assert data["interval_seconds"] == 3600
        assert "id" in data
        assert "created_at" in data

    def test_create_with_all_fields(self, client):
        """All optional fields are accepted and returned."""
        resp = client.post(
            "/api/watches",
            json={
                "target": "example.org",
                "target_type": "domain",
                "plugin_ids": ["http-headers", "ssl-health"],
                "interval_seconds": 7200,
                "webhook_url": "https://hooks.example.com/w",
                "email": "admin@example.com",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["target"] == "example.org"
        assert data["plugin_ids"] == ["http-headers", "ssl-health"]
        assert data["interval_seconds"] == 7200
        assert data["webhook_url"] == "https://hooks.example.com/w"
        assert data["email"] == "admin@example.com"

    def test_create_rejects_forbidden_chars(self, client):
        """A target with shell metacharacters is rejected with 400."""
        resp = client.post(
            "/api/watches",
            json={"target": "!@#$%^&*()"},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "forbidden" in data.get("detail", {}).get("error", str(data)).lower()

    def test_create_validates_required_target(self, client):
        """Omitting the required 'target' field returns 422."""
        resp = client.post("/api/watches", json={})
        assert resp.status_code == 422

    def test_create_strips_whitespace(self, client):
        """Target whitespace is stripped."""
        resp = client.post("/api/watches", json={"target": "  example.com  "})
        assert resp.status_code == 200
        assert resp.json()["target"] == "example.com"


# ======================== GET /api/watches ========================


class TestListWatches:
    def test_list_empty(self, client):
        """GET /api/watches returns an empty list when no watches exist."""
        resp = client.get("/api/watches")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_returns_all(self, client):
        """GET /api/watches returns all watches."""
        client.post("/api/watches", json={"target": "a.com"})
        client.post("/api/watches", json={"target": "b.com"})

        resp = client.get("/api/watches")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2


# ======================== GET /api/watches/{id} ========================


class TestGetWatch:
    def test_get_existing(self, client):
        """GET /api/watches/{id} returns the watch."""
        created = client.post("/api/watches", json={"target": "example.com"}).json()
        resp = client.get(f"/api/watches/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["target"] == "example.com"

    def test_get_nonexistent_returns_404(self, client):
        """GET /api/watches/9999 returns 404."""
        resp = client.get("/api/watches/9999")
        assert resp.status_code == 404


# ======================== DELETE /api/watches/{id} ========================


class TestDeleteWatch:
    def test_delete_existing(self, client):
        """DELETE /api/watches/{id} deletes the watch."""
        created = client.post("/api/watches", json={"target": "example.com"}).json()
        resp = client.delete(f"/api/watches/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["status"] == "deleted"

        # Verify it's gone
        get_resp = client.get(f"/api/watches/{created['id']}")
        assert get_resp.status_code == 404

    def test_delete_nonexistent_returns_404(self, client):
        """DELETE /api/watches/9999 returns 404."""
        resp = client.delete("/api/watches/9999")
        assert resp.status_code == 404


# ======================== POST /api/watches/{id}/toggle ========================


class TestToggleWatch:
    def test_toggle_active_state(self, client):
        """POST /api/watches/{id}/toggle flips is_active."""
        created = client.post("/api/watches", json={"target": "example.com"}).json()
        assert created["is_active"] is True

        # Toggle off
        resp = client.post(f"/api/watches/{created['id']}/toggle")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is False

        # Toggle back on
        resp = client.post(f"/api/watches/{created['id']}/toggle")
        assert resp.status_code == 200
        assert resp.json()["is_active"] is True

    def test_toggle_nonexistent_returns_404(self, client):
        """POST /api/watches/9999/toggle returns 404."""
        resp = client.post("/api/watches/9999/toggle")
        assert resp.status_code == 404


# ======================== GET /api/watches/alerts ========================


@pytest.mark.asyncio
async def test_alerts_empty(client):
    """GET /api/watches/alerts returns an empty list when no alerts."""
    resp = client.get("/api/watches/alerts")
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_alerts_listed(client, db_session):
    """GET /api/watches/alerts returns alerts."""
    # Create a watch via API
    w = client.post("/api/watches", json={"target": "example.com"}).json()

    # Insert an alert directly into the test DB
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

    resp = client.get("/api/watches/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 1
    assert data[0]["summary"] == "Test alert"


# ======================== GET /api/watches/{id}/alerts ========================


@pytest.mark.asyncio
async def test_alerts_for_watch(client, db_session):
    """GET /api/watches/{id}/alerts returns alerts scoped to that watch."""
    w = client.post("/api/watches", json={"target": "example.com"}).json()

    await db_session.execute(
        text(q("create_alert")),
        {
            "watch_id": w["id"],
            "target": "example.com",
            "plugin_id": "http-headers",
            "old_data": json.dumps({"a": 1}),
            "new_data": json.dumps({"a": 2}),
            "summary": "Scoped alert",
        },
    )
    await db_session.commit()

    resp = client.get(f"/api/watches/{w['id']}/alerts")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["summary"] == "Scoped alert"


@pytest.mark.asyncio
async def test_alerts_for_watch_not_found(client):
    """GET /api/watches/9999/alerts returns 404 when watch not found."""
    resp = client.get("/api/watches/9999/alerts")
    assert resp.status_code == 404
