"""
TRINETRA — Alert Detection Unit Tests

Tests for the pure functions that power alert detection:

* ``_parse_gui_data``  — parses gui_data from DB (dict or JSON string)
* ``_summarize_diff``  — builds human-readable change summaries
* ``_parse_json_field`` — parses old/new alert data (dict or JSON string)
* ``parse_plugin_ids`` — parses plugin_ids from DB (list or JSON string)

These functions are deterministic and have no I/O, so they do not
need the ``db_session`` fixture.
"""

import json
import pytest

from app.tasks.watch_tasks import _parse_gui_data, _summarize_diff
from app.api.watch_routes import _parse_json_field
from app.services.database import parse_plugin_ids


# ======================== _parse_gui_data ========================


class TestParseGuiData:
    def test_dict_passthrough(self):
        """When the input is already a dict, return it as-is."""
        data = {"key": "value", "count": 42}
        assert _parse_gui_data(data) is data

    def test_json_string(self):
        """A valid JSON string is decoded into a dict."""
        data = '{"key": "value", "count": 42}'
        result = _parse_gui_data(data)
        assert result == {"key": "value", "count": 42}

    def test_empty_json_object(self):
        """An empty JSON object string returns an empty dict."""
        assert _parse_gui_data("{}") == {}

    def test_invalid_json_string(self):
        """An invalid JSON string returns an empty dict."""
        assert _parse_gui_data("{bad json}") == {}

    def test_none_input(self):
        """None input returns an empty dict."""
        assert _parse_gui_data(None) == {}

    def test_empty_string(self):
        """An empty string returns an empty dict."""
        assert _parse_gui_data("") == {}

    def test_nested_json(self):
        """Deeply nested JSON is decoded correctly."""
        data = '{"outer": {"inner": [1, 2, 3]}, "flag": true}'
        result = _parse_gui_data(data)
        assert result == {"outer": {"inner": [1, 2, 3]}, "flag": True}

    def test_int_input(self):
        """Non-string, non-dict input (e.g. int) returns empty dict."""
        assert _parse_gui_data(42) == {}

    def test_list_input(self):
        """List input returns empty dict (not a dict or JSON string)."""
        assert _parse_gui_data([1, 2, 3]) == {}


# ======================== _summarize_diff ========================


class TestSummarizeDiff:
    def test_no_changes(self):
        """When old and new are identical, report no changes."""
        old = {"key": "value", "count": 1}
        new = {"key": "value", "count": 1}
        summary = _summarize_diff(old, new, "Test Plugin")
        assert "No significant changes" in summary
        assert "Test Plugin" in summary

    def test_single_change(self):
        """A single changed value is reported."""
        old = {"key": "old_value"}
        new = {"key": "new_value"}
        summary = _summarize_diff(old, new, "Test Plugin")
        assert "1 change(s)" in summary
        assert "old_value" in summary
        assert "new_value" in summary

    def test_multiple_changes(self):
        """Multiple changed keys are reported, limited to 5."""
        old = {f"key{i}": f"old{i}" for i in range(10)}
        new = {f"key{i}": f"new{i}" for i in range(10)}
        summary = _summarize_diff(old, new, "Many Plugin")
        assert "10 change(s)" in summary
        # Should mention at least the first 5
        for i in range(5):
            assert f"key{i}" in summary

    def test_key_added(self):
        """Keys present in new but not old are reported."""
        old = {"existing": "value"}
        new = {"existing": "value", "added": "new_key"}
        summary = _summarize_diff(old, new, "Add Plugin")
        assert "1 change(s)" in summary
        assert "added" in summary

    def test_key_removed(self):
        """Keys present in old but not new are reported."""
        old = {"existing": "value", "removed": "gone"}
        new = {"existing": "value"}
        summary = _summarize_diff(old, new, "Remove Plugin")
        assert "1 change(s)" in summary
        assert "removed" in summary

    def test_value_truncation(self):
        """Values longer than 80 chars are truncated."""
        long_val = "x" * 200
        old = {"key": "short"}
        new = {"key": long_val}
        summary = _summarize_diff(old, new, "Truncate Plugin")
        assert "x" * 80 in summary
        assert "x" * 81 not in summary

    def test_none_values(self):
        """None values are handled gracefully."""
        old = {"key": None}
        new = {"key": "value"}
        summary = _summarize_diff(old, new, "None Plugin")
        assert "(none)" in summary

    def test_integer_values(self):
        """Integer values are converted to strings."""
        old = {"score": 10}
        new = {"score": 20}
        summary = _summarize_diff(old, new, "Int Plugin")
        assert "10" in summary
        assert "20" in summary

    def test_plugin_name_in_summary(self):
        """The plugin name is always included in the summary."""
        summary = _summarize_diff({"a": 1}, {"a": 2}, "MySpecialPlugin")
        assert "MySpecialPlugin" in summary


# ======================== _parse_json_field ========================


class TestParseJsonField:
    def test_dict_passthrough(self):
        """Dict input is returned as-is."""
        data = {"key": "value"}
        assert _parse_json_field(data) is data

    def test_json_string(self):
        """Valid JSON string is decoded."""
        assert _parse_json_field('{"a": 1}') == {"a": 1}

    def test_invalid_json(self):
        """Invalid JSON string returns empty dict."""
        assert _parse_json_field("not json") == {}

    def test_none_input(self):
        """None returns empty dict."""
        assert _parse_json_field(None) == {}

    def test_empty_string(self):
        """Empty string returns empty dict."""
        assert _parse_json_field("") == {}


# ======================== parse_plugin_ids ========================


class TestParsePluginIds:
    def test_list_passthrough(self):
        """A list input is returned as-is."""
        ids = ["http-headers", "ssl-health"]
        assert parse_plugin_ids(ids) is ids

    def test_json_string(self):
        """A JSON-encoded list string is decoded."""
        assert parse_plugin_ids('["a", "b"]') == ["a", "b"]

    def test_empty_json_array(self):
        """An empty JSON array returns an empty list."""
        assert parse_plugin_ids("[]") == []

    def test_none_input(self):
        """None returns an empty list."""
        assert parse_plugin_ids(None) == []

    def test_invalid_json_string(self):
        """An invalid JSON string falls back to comma splitting."""
        result = parse_plugin_ids("[a, b]")
        assert result == ["a", "b"]

    def test_single_item_json(self):
        """A single-item JSON array is decoded."""
        assert parse_plugin_ids('["only-one"]') == ["only-one"]

    def test_using_sqlite_flag_ignored_when_list(self):
        """When the raw value is a list, the using_sqlite flag is irrelevant."""
        ids = ["plugin-1"]
        assert parse_plugin_ids(ids, using_sqlite=True) is ids
        assert parse_plugin_ids(ids, using_sqlite=False) is ids

    def test_empty_string_returns_empty_list(self):
        """An empty string returns an empty list."""
        assert parse_plugin_ids("") == []
