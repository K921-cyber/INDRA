"""
TRINETRA — Watch Retry Logic Tests

Tests for the retry mechanism in ``app.tasks.watch_tasks`` covering:
* scan_watch — successful scan, retry on SQLite lock errors, non-lock errors
* _save_watch_results — saving results, change detection, alert creation
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from sqlalchemy import text

from app.services import watch_service
from app.services.database import async_session_factory
from app.tasks.watch_tasks import (
    scan_watch,
    _save_watch_results,
    _parse_gui_data,
    _summarize_diff,
)


# ── Helpers ───────────────────────────────────────────────


def _make_plugin_result(
    plugin_id: str = "http-headers",
    plugin_name: str = "HTTP Headers",
    category: str = "infrastructure",
    gui_data: dict | None = None,
    status: str = "completed",
) -> dict:
    """Build a fake plugin result dict (matches PluginResult.to_dict())."""
    return {
        "plugin_id": plugin_id,
        "plugin_name": plugin_name,
        "category": category,
        "target": "example.com",
        "status": status,
        "freshness": "moments",
        "timestamp": "2025-01-01T00:00:00+00:00",
        "gui_data": gui_data or {"Status": "completed", "Headers": 5},
        "terminal_data": "Header scan complete",
        "error": None,
    }


# ======================== scan_watch: Success ========================


class TestScanWatchSuccess:
    @pytest.mark.asyncio
    async def test_scan_watch_with_empty_results(self, db_session):
        """scan_watch completes successfully with no plugin results."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")

        # Mock orchestrator to return empty results
        with patch("app.tasks.watch_tasks._get_orch") as mock_get_orch:
            mock_orch = MagicMock()
            mock_orch.run_all = AsyncMock(return_value=[])
            mock_orch.plugin_registry = MagicMock()
            mock_get_orch.return_value = mock_orch

            result = await scan_watch(
                watch_id=w["id"],
                target="example.com",
                target_type="domain",
            )

        assert result["watch_id"] == w["id"]
        assert result["target"] == "example.com"
        assert result["plugins_run"] == 0
        assert "timestamp" in result

    @pytest.mark.asyncio
    async def test_scan_watch_saves_results(self, db_session):
        """scan_watch saves plugin results to the database."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")
        fake_result = _make_plugin_result()

        with patch("app.tasks.watch_tasks._get_orch") as mock_get_orch:
            mock_orch = MagicMock()
            # run_all returns a list of dicts (matching PluginResult.to_dict())
            mock_orch.run_all = AsyncMock(return_value=[fake_result])
            mock_orch.plugin_registry = MagicMock()
            mock_get_orch.return_value = mock_orch

            result = await scan_watch(
                watch_id=w["id"],
                target="example.com",
                target_type="domain",
            )

        assert result["plugins_run"] == 1

        # Verify the scan result was saved
        async with async_session_factory() as db:
            rows = (await db.execute(
                text("SELECT * FROM scan_results WHERE target = :target"),
                {"target": "example.com"},
            )).all()
            assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_scan_watch_updates_last_checked(self, db_session):
        """scan_watch updates the last_checked_at timestamp."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")

        with patch("app.tasks.watch_tasks._get_orch") as mock_get_orch:
            mock_orch = MagicMock()
            mock_orch.run_all = AsyncMock(return_value=[])
            mock_orch.plugin_registry = MagicMock()
            mock_get_orch.return_value = mock_orch

            await scan_watch(
                watch_id=w["id"],
                target="example.com",
                target_type="domain",
            )

        # Verify last_checked_at was updated
        updated = await watch_service.get_watch(w["id"])
        assert updated["last_checked_at"] is not None


# ======================== scan_watch: Retry Logic ========================


class TestScanWatchRetry:
    @pytest.mark.asyncio
    async def test_retry_on_database_locked(self, db_session):
        """scan_watch retries when _save_watch_results raises 'database is locked'."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")

        call_count = 0

        async def _failing_then_ok(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("database is locked")
            # Succeed on 3rd call (do nothing — just don't raise)

        with patch("app.tasks.watch_tasks._get_orch") as mock_get_orch:
            mock_orch = MagicMock()
            mock_orch.run_all = AsyncMock(return_value=[])
            mock_orch.plugin_registry = MagicMock()
            mock_get_orch.return_value = mock_orch

            with patch("app.tasks.watch_tasks._save_watch_results", side_effect=_failing_then_ok), \
                 patch("app.tasks.watch_tasks.asyncio.sleep", new_callable=AsyncMock):
                result = await scan_watch(
                    watch_id=w["id"],
                    target="example.com",
                    target_type="domain",
                )

        assert result["watch_id"] == w["id"]
        assert call_count == 3  # Failed twice, succeeded on 3rd

    @pytest.mark.asyncio
    async def test_retry_on_busy_error(self, db_session):
        """scan_watch retries on 'busy' error messages."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")

        call_count = 0

        async def _busy_then_ok(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("database is busy")
            # Succeed on 2nd call

        with patch("app.tasks.watch_tasks._get_orch") as mock_get_orch:
            mock_orch = MagicMock()
            mock_orch.run_all = AsyncMock(return_value=[])
            mock_orch.plugin_registry = MagicMock()
            mock_get_orch.return_value = mock_orch

            with patch("app.tasks.watch_tasks._save_watch_results", side_effect=_busy_then_ok), \
                 patch("app.tasks.watch_tasks.asyncio.sleep", new_callable=AsyncMock):
                result = await scan_watch(
                    watch_id=w["id"],
                    target="example.com",
                    target_type="domain",
                )

        assert result["watch_id"] == w["id"]
        assert call_count == 2

    @pytest.mark.asyncio
    async def test_non_lock_error_raises_immediately(self, db_session):
        """Non-SQLite-lock errors should raise immediately without retry."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")

        call_count = 0

        async def _non_lock_error(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise ValueError("Something completely different went wrong")

        with patch("app.tasks.watch_tasks._get_orch") as mock_get_orch:
            mock_orch = MagicMock()
            mock_orch.run_all = AsyncMock(return_value=[])
            mock_orch.plugin_registry = MagicMock()
            mock_get_orch.return_value = mock_orch

            with patch("app.tasks.watch_tasks._save_watch_results", side_effect=_non_lock_error):
                with pytest.raises(ValueError, match="Something completely different"):
                    await scan_watch(
                        watch_id=w["id"],
                        target="example.com",
                        target_type="domain",
                    )

        assert call_count == 1  # No retries for non-lock errors

    @pytest.mark.asyncio
    async def test_max_retries_exhausted_raises(self, db_session):
        """After 3 failed attempts with lock errors, the exception is re-raised."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")

        call_count = 0

        async def _always_locked(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            raise Exception("database is locked")

        with patch("app.tasks.watch_tasks._get_orch") as mock_get_orch:
            mock_orch = MagicMock()
            mock_orch.run_all = AsyncMock(return_value=[])
            mock_orch.plugin_registry = MagicMock()
            mock_get_orch.return_value = mock_orch

            with patch("app.tasks.watch_tasks._save_watch_results", side_effect=_always_locked), \
                 patch("app.tasks.watch_tasks.asyncio.sleep", new_callable=AsyncMock):
                with pytest.raises(Exception, match="database is locked"):
                    await scan_watch(
                        watch_id=w["id"],
                        target="example.com",
                        target_type="domain",
                    )

        assert call_count == 3  # 3 total attempts (0, 1, 2)

    @pytest.mark.asyncio
    async def test_plugin_ids_selective_scan(self, db_session):
        """scan_watch runs only the specified plugin IDs."""
        w = await watch_service.create_watch(
            target="example.com",
            target_type="domain",
            plugin_ids=["http-headers"],
        )

        with patch("app.tasks.watch_tasks._get_orch") as mock_get_orch:
            mock_orch = MagicMock()

            # Mock plugin registry
            mock_plugin = MagicMock()
            mock_plugin.input_types = ["domain"]
            mock_plugin.run_safe = AsyncMock(return_value=MagicMock(
                to_dict=MagicMock(return_value=_make_plugin_result()),
            ))
            mock_orch.plugin_registry.get.return_value = mock_plugin
            mock_get_orch.return_value = mock_orch

            result = await scan_watch(
                watch_id=w["id"],
                target="example.com",
                target_type="domain",
                plugin_ids=["http-headers"],
            )

        assert result["plugins_run"] == 1
        mock_plugin.run_safe.assert_called_once_with("example.com")


# ======================== _save_watch_results ========================


class TestSaveWatchResults:
    @pytest.mark.asyncio
    async def test_saves_scan_results(self, db_session):
        """_save_watch_results stores scan results in the database."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")
        results = [_make_plugin_result()]

        await _save_watch_results(w["id"], "example.com", "domain", results)

        async with async_session_factory() as db:
            rows = (await db.execute(
                text("SELECT * FROM scan_results WHERE target = :target"),
                {"target": "example.com"},
            )).all()
            assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_no_alert_on_first_scan(self, db_session):
        """First scan should not create alerts (nothing to compare against)."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")
        results = [_make_plugin_result(gui_data={"Key": "Value"})]

        await _save_watch_results(w["id"], "example.com", "domain", results)

        alerts = await watch_service.list_alerts_for_watch(w["id"])
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_alert_on_changed_data(self, db_session):
        """Second scan with different data should create an alert."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")

        # First scan
        results_v1 = [_make_plugin_result(gui_data={"Key": "OldValue"})]
        await _save_watch_results(w["id"], "example.com", "domain", results_v1)

        # Second scan with changed data
        results_v2 = [_make_plugin_result(gui_data={"Key": "NewValue"})]
        await _save_watch_results(w["id"], "example.com", "domain", results_v2)

        alerts = await watch_service.list_alerts_for_watch(w["id"])
        assert len(alerts) == 1
        assert "Key" in alerts[0]["summary"]
        assert "OldValue" in alerts[0]["summary"] or "old" in alerts[0]["summary"].lower()

    @pytest.mark.asyncio
    async def test_no_alert_on_same_data(self, db_session):
        """Second scan with identical data should NOT create an alert."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")

        gui_data = {"Key": "SameValue", "Count": 42}
        results_v1 = [_make_plugin_result(gui_data=gui_data)]
        await _save_watch_results(w["id"], "example.com", "domain", results_v1)

        # Same data
        results_v2 = [_make_plugin_result(gui_data=gui_data)]
        await _save_watch_results(w["id"], "example.com", "domain", results_v2)

        alerts = await watch_service.list_alerts_for_watch(w["id"])
        assert len(alerts) == 0

    @pytest.mark.asyncio
    async def test_multiple_plugin_results(self, db_session):
        """Multiple plugin results are all saved."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")
        results = [
            _make_plugin_result(plugin_id="http-headers", plugin_name="HTTP Headers"),
            _make_plugin_result(plugin_id="ssl-health", plugin_name="SSL Health"),
            _make_plugin_result(plugin_id="dns-records", plugin_name="DNS Records", category="infrastructure"),
        ]

        await _save_watch_results(w["id"], "example.com", "domain", results)

        async with async_session_factory() as db:
            rows = (await db.execute(
                text("SELECT * FROM scan_results WHERE target = :target"),
                {"target": "example.com"},
            )).all()
            assert len(rows) == 3

    @pytest.mark.asyncio
    async def test_empty_results_is_noop(self, db_session):
        """Empty results list completes without error."""
        w = await watch_service.create_watch(target="example.com", target_type="domain")
        await _save_watch_results(w["id"], "example.com", "domain", [])
        # No crash = success


# ======================== Change Detection ========================


class TestChangeDetection:
    def test_parse_gui_data_dict(self):
        """Dict input passes through."""
        data = {"key": "value"}
        assert _parse_gui_data(data) is data

    def test_parse_gui_data_json_string(self):
        """JSON string is parsed."""
        assert _parse_gui_data('{"key": "value"}') == {"key": "value"}

    def test_parse_gui_data_invalid(self):
        """Invalid input returns empty dict."""
        assert _parse_gui_data(None) == {}
        assert _parse_gui_data(42) == {}
        assert _parse_gui_data("not json") == {}

    def test_summarize_diff_no_changes(self):
        """Identical data produces 'No significant changes'."""
        summary = _summarize_diff({"a": 1}, {"a": 1}, "TestPlugin")
        assert "No significant changes" in summary
        assert "TestPlugin" in summary

    def test_summarize_diff_with_changes(self):
        """Changed data produces a change summary."""
        summary = _summarize_diff({"a": "old"}, {"a": "new"}, "TestPlugin")
        assert "1 change(s)" in summary
        assert "old" in summary
        assert "new" in summary

    def test_summarize_diff_new_key_added(self):
        """New key in current data is detected."""
        summary = _summarize_diff({}, {"new_key": "value"}, "TestPlugin")
        assert "1 change(s)" in summary
        assert "new_key" in summary
