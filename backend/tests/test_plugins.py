"""
TRINETRA — Plugin System Unit Tests

Tests for:
* OSINTPlugin base class
* PluginResult data class
* PluginRegistry auto-discovery
* OrchestratorService parallel execution
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone, timedelta

from app.plugins.base import OSINTPlugin, PluginResult
from app.plugins.registry import PluginRegistry, plugin_registry
from app.services.orchestrator import OrchestratorService


# ======================== PluginResult Tests ========================


class TestPluginResult:
    """Tests for the PluginResult data class."""

    def test_basic_creation(self):
        """PluginResult can be created with required fields."""
        result = PluginResult(
            plugin_id="test-plugin",
            plugin_name="Test Plugin",
            category="infrastructure",
            target="example.com",
        )
        assert result.plugin_id == "test-plugin"
        assert result.plugin_name == "Test Plugin"
        assert result.category == "infrastructure"
        assert result.target == "example.com"
        assert result.status == "completed"
        assert result.gui_data == {}
        assert result.terminal_data == ""
        assert result.error is None

    def test_freshness_computation_moments(self):
        """Data less than 60 seconds old is 'moments'."""
        result = PluginResult(
            plugin_id="test",
            plugin_name="Test",
            category="infrastructure",
            target="example.com",
            timestamp=datetime.now(timezone.utc),
        )
        assert result.freshness == "moments"

    def test_freshness_computation_minutes(self):
        """Data 1-60 minutes old is 'minutes'."""
        result = PluginResult(
            plugin_id="test",
            plugin_name="Test",
            category="infrastructure",
            target="example.com",
            timestamp=datetime.now(timezone.utc) - timedelta(minutes=30),
        )
        assert result.freshness == "minutes"

    def test_freshness_computation_hours(self):
        """Data 1-24 hours old is 'hours'."""
        result = PluginResult(
            plugin_id="test",
            plugin_name="Test",
            category="infrastructure",
            target="example.com",
            timestamp=datetime.now(timezone.utc) - timedelta(hours=5),
        )
        assert result.freshness == "hours"

    def test_freshness_computation_days(self):
        """Data 1-7 days old is 'days'."""
        result = PluginResult(
            plugin_id="test",
            plugin_name="Test",
            category="infrastructure",
            target="example.com",
            timestamp=datetime.now(timezone.utc) - timedelta(days=3),
        )
        assert result.freshness == "days"

    def test_freshness_computation_weeks(self):
        """Data older than 7 days is 'weeks'."""
        result = PluginResult(
            plugin_id="test",
            plugin_name="Test",
            category="infrastructure",
            target="example.com",
            timestamp=datetime.now(timezone.utc) - timedelta(days=14),
        )
        assert result.freshness == "weeks"

    def test_to_dict(self):
        """to_dict() returns a serializable dictionary."""
        ts = datetime.now(timezone.utc)
        result = PluginResult(
            plugin_id="test-plugin",
            plugin_name="Test Plugin",
            category="threat",
            target="192.168.1.1",
            status="failed",
            gui_data={"ports": [80, 443]},
            terminal_data="Port 80: open",
            error="Connection timeout",
            timestamp=ts,
        )
        d = result.to_dict()
        assert d["plugin_id"] == "test-plugin"
        assert d["plugin_name"] == "Test Plugin"
        assert d["category"] == "threat"
        assert d["target"] == "192.168.1.1"
        assert d["status"] == "failed"
        assert d["gui_data"] == {"ports": [80, 443]}
        assert d["terminal_data"] == "Port 80: open"
        assert d["error"] == "Connection timeout"
        assert d["timestamp"] == ts.isoformat()

    def test_custom_timestamp_preserved(self):
        """Custom timestamp is preserved, not overridden."""
        custom_ts = datetime(2024, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        result = PluginResult(
            plugin_id="test",
            plugin_name="Test",
            category="infrastructure",
            target="example.com",
            timestamp=custom_ts,
        )
        assert result.timestamp == custom_ts


# ======================== OSINTPlugin Tests ========================


class TestOSINTPlugin:
    """Tests for the OSINTPlugin abstract base class."""

    def test_cannot_instantiate_directly(self):
        """Cannot instantiate OSINTPlugin directly - it's abstract."""
        with pytest.raises(TypeError):
            OSINTPlugin()

    def test_concrete_plugin_with_run(self):
        """A concrete plugin implementing run() can be instantiated."""

        class TestPlugin(OSINTPlugin):
            plugin_id = "test-plugin"
            name = "Test Plugin"
            category = "infrastructure"
            description = "A test plugin"
            input_types = ["domain"]

            async def run(self, target: str) -> PluginResult:
                return PluginResult(
                    plugin_id=self.plugin_id,
                    plugin_name=self.name,
                    category=self.category,
                    target=target,
                    gui_data={"test": True},
                )

        plugin = TestPlugin()
        assert plugin.plugin_id == "test-plugin"
        assert plugin.name == "Test Plugin"

    @pytest.mark.asyncio
    async def test_run_safe_success(self):
        """run_safe() catches no exceptions on success."""

        class SuccessPlugin(OSINTPlugin):
            plugin_id = "success"
            name = "Success"
            category = "infrastructure"

            async def run(self, target: str) -> PluginResult:
                return PluginResult(
                    plugin_id=self.plugin_id,
                    plugin_name=self.name,
                    category=self.category,
                    target=target,
                    gui_data={"status": "ok"},
                )

        plugin = SuccessPlugin()
        result = await plugin.run_safe("example.com")
        assert result.status == "completed"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_run_safe_exception_handling(self):
        """run_safe() catches exceptions and returns failed result."""

        class FailingPlugin(OSINTPlugin):
            plugin_id = "failing"
            name = "Failing"
            category = "infrastructure"

            async def run(self, target: str) -> PluginResult:
                raise ConnectionError("Connection refused")

        plugin = FailingPlugin()
        result = await plugin.run_safe("example.com")
        assert result.status == "failed"
        assert "Connection refused" in result.error
        assert result.plugin_id == "failing"

    def test_auto_plugin_id_from_classname(self):
        """plugin_id defaults to lowercase class name if not set."""

        class MyCustomPlugin(OSINTPlugin):
            name = "Custom"
            category = "infrastructure"

            async def run(self, target: str) -> PluginResult:
                pass

        plugin = MyCustomPlugin()
        assert plugin.plugin_id == "mycustomplugin"


# ======================== PluginRegistry Tests ========================


class TestPluginRegistry:
    """Tests for the PluginRegistry auto-discovery system."""

    def test_registry_singleton(self):
        """plugin_registry is a singleton instance."""
        from app.plugins.registry import plugin_registry as pr1
        from app.plugins.registry import plugin_registry as pr2
        assert pr1 is pr2

    def test_discover_populates_plugins(self):
        """discover() populates the registry with plugins."""
        registry = PluginRegistry()
        registry.discover()
        assert registry.count > 0

    def test_get_plugin_by_id(self):
        """get() returns a plugin by its ID."""
        registry = PluginRegistry()
        registry.discover()
        # Test with a known plugin ID
        plugin = registry.get("name-servers")
        assert plugin is not None
        assert plugin.plugin_id == "name-servers"

    def test_get_nonexistent_plugin(self):
        """get() returns None for non-existent plugin IDs."""
        registry = PluginRegistry()
        registry.discover()
        plugin = registry.get("nonexistent-plugin-12345")
        assert plugin is None

    def test_get_by_category(self):
        """get_by_category() returns plugins in a specific category."""
        registry = PluginRegistry()
        registry.discover()
        infra_plugins = registry.get_by_category("infrastructure")
        assert len(infra_plugins) > 0
        for p in infra_plugins:
            assert p.category == "infrastructure"

    def test_get_for_target(self):
        """get_for_target() returns plugins matching target type."""
        registry = PluginRegistry()
        registry.discover()
        domain_plugins = registry.get_for_target("example.com", "domain")
        assert len(domain_plugins) > 0
        for p in domain_plugins:
            assert "domain" in p.input_types

    def test_plugins_property(self):
        """plugins property returns list of all plugins."""
        registry = PluginRegistry()
        registry.discover()
        plugins = registry.plugins
        assert isinstance(plugins, list)
        assert len(plugins) > 0

    def test_count_property(self):
        """count property returns the number of plugins."""
        registry = PluginRegistry()
        registry.discover()
        assert registry.count == len(registry.plugins)


# ======================== OrchestratorService Tests ========================


class TestOrchestratorService:
    """Tests for the OrchestratorService parallel execution."""

    @pytest.mark.asyncio
    async def test_run_all_returns_results(self):
        """run_all() returns a list of plugin results."""
        orchestrator = OrchestratorService()
        # Mock the registry to return controlled plugins
        with patch.object(orchestrator.plugin_registry, 'get_for_target') as mock_get:
            mock_plugin = AsyncMock()
            mock_plugin.run_safe.return_value = PluginResult(
                plugin_id="test",
                plugin_name="Test",
                category="infrastructure",
                target="example.com",
                gui_data={"test": True},
            )
            mock_get.return_value = [mock_plugin]

            results = await orchestrator.run_all("example.com", "domain")
            assert len(results) == 1
            assert results[0]["plugin_id"] == "test"

    @pytest.mark.asyncio
    async def test_run_all_no_matching_plugins(self):
        """run_all() returns empty list when no plugins match."""
        orchestrator = OrchestratorService()
        with patch.object(orchestrator.plugin_registry, 'get_for_target') as mock_get:
            mock_get.return_value = []
            results = await orchestrator.run_all("example.com", "unknown")
            assert results == []

    @pytest.mark.asyncio
    async def test_run_all_stream_yields_messages(self):
        """run_all_stream() yields start, result, and complete messages."""
        orchestrator = OrchestratorService()
        with patch.object(orchestrator.plugin_registry, 'get_for_target') as mock_get:
            mock_plugin = AsyncMock()
            mock_plugin.plugin_id = "test-plugin"
            mock_plugin.run_safe.return_value = PluginResult(
                plugin_id="test-plugin",
                plugin_name="Test",
                category="infrastructure",
                target="example.com",
            )
            mock_get.return_value = [mock_plugin]

            messages = []
            async for msg in orchestrator.run_all_stream("example.com", "domain"):
                messages.append(msg)

            # Should have start, result, complete
            assert len(messages) == 3
            assert messages[0]["type"] == "start"
            assert messages[1]["type"] == "result"
            assert messages[2]["type"] == "complete"

    @pytest.mark.asyncio
    async def test_run_single_plugin(self):
        """run_single() runs a specific plugin by ID."""
        orchestrator = OrchestratorService()
        with patch.object(orchestrator.plugin_registry, 'get') as mock_get:
            mock_plugin = AsyncMock()
            mock_plugin.run_safe.return_value = PluginResult(
                plugin_id="test",
                plugin_name="Test",
                category="infrastructure",
                target="example.com",
            )
            mock_get.return_value = mock_plugin

            result = await orchestrator.run_single("example.com", "test")
            assert result is not None
            assert result.plugin_id == "test"

    @pytest.mark.asyncio
    async def test_run_single_nonexistent_plugin(self):
        """run_single() returns None for non-existent plugin IDs."""
        orchestrator = OrchestratorService()
        with patch.object(orchestrator.plugin_registry, 'get') as mock_get:
            mock_get.return_value = None
            result = await orchestrator.run_single("example.com", "nonexistent")
            assert result is None

    def test_get_plugin_status(self):
        """get_plugin_status() returns plugin counts by category."""
        orchestrator = OrchestratorService()
        status = orchestrator.get_plugin_status()
        assert "total" in status
        assert "categories" in status
        assert "infrastructure" in status["categories"]
        assert "threat" in status["categories"]
        assert "advanced" in status["categories"]


# ======================== AutoDetect Tests ========================


class TestAutoDetect:
    """Tests for the target type auto-detection."""

    def test_detect_ip(self):
        from app.core.detector import AutoDetect
        assert AutoDetect.detect("192.168.1.1") == "ip"
        assert AutoDetect.detect("10.0.0.1") == "ip"
        assert AutoDetect.detect("8.8.8.8") == "ip"

    def test_detect_email(self):
        from app.core.detector import AutoDetect
        assert AutoDetect.detect("user@example.com") == "email"
        assert AutoDetect.detect("test@test.co.uk") == "email"

    def test_detect_domain(self):
        from app.core.detector import AutoDetect
        assert AutoDetect.detect("example.com") == "domain"
        assert AutoDetect.detect("sub.example.co.uk") == "domain"

    def test_detect_phone(self):
        from app.core.detector import AutoDetect
        assert AutoDetect.detect("+1234567890") == "phone"
        assert AutoDetect.detect("123-456-7890") == "phone"

    def test_detect_name(self):
        from app.core.detector import AutoDetect
        assert AutoDetect.detect("John Doe") == "name"
        assert AutoDetect.detect("随便什么") == "name"

    def test_detect_full_returns_confidence(self):
        from app.core.detector import AutoDetect
        result = AutoDetect.detect_full("example.com")
        assert "detected_type" in result
        assert "confidence" in result
        assert result["confidence"] > 0

    def test_get_display_label(self):
        from app.core.detector import AutoDetect
        assert "Domain" in AutoDetect.get_display_label("domain")
        assert "IP" in AutoDetect.get_display_label("ip")
        assert "Email" in AutoDetect.get_display_label("email")


# ======================== Sanitizer Tests ========================


class TestSanitizer:
    """Tests for input sanitization."""

    def test_sanitize_valid_domain(self):
        from app.core.sanitizer import sanitize_target
        result = sanitize_target("example.com")
        assert result == "example.com"

    def test_sanitize_strips_whitespace(self):
        from app.core.sanitizer import sanitize_target
        result = sanitize_target("  example.com  ")
        assert result == "example.com"

    def test_sanitize_rejects_too_long(self):
        from app.core.sanitizer import sanitize_target, InputValidationError
        with pytest.raises(InputValidationError):
            sanitize_target("a" * 300)

    def test_sanitize_rejects_control_chars(self):
        from app.core.sanitizer import sanitize_target, InputValidationError
        with pytest.raises(InputValidationError):
            sanitize_target("example\x00.com")

    def test_validate_valid_domain(self):
        from app.core.sanitizer import validate_target
        is_valid, target_type, error = validate_target("example.com")
        assert is_valid is True
        assert target_type == "domain"

    def test_validate_valid_email(self):
        from app.core.sanitizer import validate_target
        is_valid, target_type, error = validate_target("user@example.com")
        assert is_valid is True
        assert target_type == "email"
