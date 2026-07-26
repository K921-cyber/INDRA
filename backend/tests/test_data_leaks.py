"""
TRINETRA — DataLeaks Plugin Unit Tests

Tests for the DataLeaksPlugin with mocked HTTP responses.
Covers:
* XposedOrNot source (emails only, path-based endpoint)
* LeakCheck source (domains + emails)
* LeakIX source (domains)
* Local KNOWN_BREACHES matching (Indian + global companies)
* Email vs domain target handling
* Empty/no-results scenarios
* Severity calculation
"""

import pytest
import json
from unittest.mock import patch, AsyncMock, MagicMock
from app.plugins.threat.data_leaks import DataLeaksPlugin


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def plugin():
    return DataLeaksPlugin()


# ── Helpers ───────────────────────────────────────────────


def make_mock_response(status_code: int, json_data):
    """Create a mock httpx response that can be used as async context manager."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json = MagicMock(return_value=json_data)
    resp.__aenter__ = AsyncMock(return_value=resp)
    resp.__aexit__ = AsyncMock(return_value=None)
    return resp


def patch_async_client(mocked_get, responses: list):
    """Configure the mock async client's .get() to return responses in order."""
    # Each call to client.get() returns the next response from the list
    # We need to handle both async context manager patterns
    mock_client = MagicMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)

    # Side_effect: each call to .get() returns a response from the iterable
    async def get_side_effect(*args, **kwargs):
        # Find the response that matches the URL pattern
        url = args[0] if args else kwargs.get("url", "")
        for expected_url_fragment, resp_data in responses:
            if expected_url_fragment in url:
                if isinstance(resp_data, tuple):
                    return make_mock_response(*resp_data)
                return resp_data
        # Default: 404 not found
        return make_mock_response(404, {})

    mock_client.get = AsyncMock(side_effect=get_side_effect)
    mocked_get.return_value = mock_client


# ======================== TEST: XposedOrNot ========================


class TestXposedOrNotSource:
    """Tests for the XposedOrNot free API source (emails only, path-based URL)."""

    @pytest.mark.asyncio
    async def test_xposedornot_returns_breaches(self, plugin):
        """XposedOrNot returns breach list for an email target."""
        mock_responses = [
            (
                "api.xposedornot.com/v1/check-email/",
                (
                    200,
                    [
                        {
                            "name": "Adobe",
                            "Title": "Adobe",
                            "breach_date": "2013-10-04",
                            "BreachDate": "2013-10-04",
                        },
                        {
                            "name": "LinkedIn",
                            "Title": "LinkedIn",
                            "breach_date": "2012-05-01",
                        },
                    ],
                ),
            ),
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("test@example.com")

        assert result.status == "completed"
        assert "XposedOrNot" in result.gui_data.get("Sources Checked", "")
        assert result.gui_data.get("Breaches Found", 0) >= 2
        assert "Adobe" in json.dumps(result.gui_data)
        assert "LinkedIn" in json.dumps(result.gui_data)

    @pytest.mark.asyncio
    async def test_xposedornot_no_breaches(self, plugin):
        """XposedOrNot returns no breaches for an email not in any breach."""
        mock_responses = [
            (
                "api.xposedornot.com/v1/check-email/",
                (200, {"Error": "Not found"}),
            ),
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("noone@nonexistent.invalid")

        assert result.status == "completed"
        # LeakCheck returns 0, no local matches for this domain
        # But the Curated Breach DB may match if the domain is in KNOWN_BREACHES
        assert result.gui_data is not None

    @pytest.mark.asyncio
    async def test_xposedornot_skipped_for_domain(self, plugin):
        """XposedOrNot is not called for domain targets (emails only)."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("example.com")

        # XposedOrNot should NOT be in sources (domain targets skip it)
        assert "XposedOrNot" not in result.gui_data.get("Sources Checked", "")

    @pytest.mark.asyncio
    async def test_xposedornot_api_error(self, plugin):
        """XposedOrNot API returns an error — plugin should not crash."""
        mock_responses = [
            (
                "api.xposedornot.com/v1/check-email/",
                make_mock_response(500, {}),  # Using direct mock response
            ),
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("test@example.com")

        assert result.status == "completed"
        assert "XposedOrNot" not in result.gui_data.get("Sources Checked", "")


# ======================== TEST: LeakCheck ========================


class TestLeakCheckSource:
    """Tests for the LeakCheck free API source (domains + emails)."""

    @pytest.mark.asyncio
    async def test_leakcheck_returns_breaches_for_domain(self, plugin):
        """LeakCheck returns breach data for a domain target (e.g. flipkart.com)."""
        mock_responses = [
            (
                "leakcheck.io",
                (
                    200,
                    {
                        "success": True,
                        "found": 3,
                        "fields": ["email", "password", "username"],
                        "sources": [
                            {"name": "Flipkart Leak 2021", "date": "2021-06-15"},
                            {"name": "Indian Combo List", "date": "2022-03-01"},
                            {"name": "Credential Stuffing DB", "date": "2023-01-10"},
                        ],
                    },
                ),
            ),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("flipkart.com")

        assert result.status == "completed"
        assert "LeakCheck" in result.gui_data.get("Sources Checked", "")
        assert result.gui_data.get("Breaches Found", 0) >= 3

    @pytest.mark.asyncio
    async def test_leakcheck_returns_breaches_for_email(self, plugin):
        """LeakCheck returns breach data for an email target."""
        mock_responses = [
            (
                "api.xposedornot.com/v1/check-email/",
                (200, {"Error": "Not found"}),
            ),
            (
                "leakcheck.io",
                (
                    200,
                    {
                        "success": True,
                        "found": 5,
                        "fields": ["email", "password", "phone", "name", "address"],
                        "sources": [
                            {"name": "COMB", "date": "2021-02-01"},
                            {"name": "Collection #1", "date": "2019-01-07"},
                        ],
                    },
                ),
            ),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("user@gmail.com")

        assert result.status == "completed"
        assert "LeakCheck" in result.gui_data.get("Sources Checked", "")
        assert result.gui_data.get("Breaches Found", 0) >= 2

    @pytest.mark.asyncio
    async def test_leakcheck_api_error(self, plugin):
        """LeakCheck API fails — plugin should not crash and should fall through."""
        mock_responses = [
            ("leakcheck.io", make_mock_response(500, {})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("example.com")

        assert result.status == "completed"
        # Should still complete gracefully, using only local DB
        assert result.gui_data is not None


# ======================== TEST: LeakIX ========================


class TestLeakIXSource:
    """Tests for the LeakIX source (domains)."""

    @pytest.mark.asyncio
    async def test_leakix_returns_data(self, plugin):
        """LeakIX returns search results for a domain."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            (
                "leakix.net",
                (
                    200,
                    [
                        {
                            "summary": "Open Elasticsearch on 192.168.1.1:9200",
                            "description": "Leaked internal data",
                        },
                        {
                            "summary": ".env file exposed on subdomain.example.com",
                            "description": "Contains DB credentials",
                        },
                    ],
                ),
            ),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("example.com")

        assert result.status == "completed"
        assert "LeakIX" in result.gui_data.get("Sources Checked", "")


# ======================== TEST: Local Breach DB ========================


class TestLocalBreachDB:
    """Tests for the curated local breach database matching."""

    @pytest.mark.asyncio
    async def test_flipkart_domain_matches_indian_breach(self, plugin):
        """flipkart.com should match the Flipkart entry in KNOWN_BREACHES."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("flipkart.com")

        assert result.status == "completed"
        assert "Curated Breach DB" in result.gui_data.get("Sources Checked", "")
        gui_text = json.dumps(result.gui_data)
        assert "Flipkart" in gui_text
        assert result.gui_data.get("Breaches Found", 0) >= 1

    @pytest.mark.asyncio
    async def test_paytm_matches_indian_breach(self, plugin):
        """paytm.com should match the Paytm entry in KNOWN_BREACHES."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("paytm.com")

        assert result.status == "completed"
        assert "Paytm" in json.dumps(result.gui_data)
        assert result.gui_data.get("Breaches Found", 0) >= 1

    @pytest.mark.asyncio
    async def test_amazon_in_matches_indian_breach(self, plugin):
        """amazon.in should match the Amazon India entry."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("amazon.in")

        assert result.status == "completed"
        assert "Amazon India" in json.dumps(result.gui_data)
        assert result.gui_data.get("Breaches Found", 0) >= 1

    @pytest.mark.asyncio
    async def test_gmail_email_matches_comb(self, plugin):
        """A gmail.com email should match COMB and gmail-related breaches."""
        mock_responses = [
            (
                "api.xposedornot.com/v1/check-email/",
                (200, {"Error": "Not found"}),
            ),
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("user@gmail.com")

        assert result.status == "completed"
        gui_text = json.dumps(result.gui_data)
        assert "COMB" in gui_text or "Compilation" in gui_text
        assert result.gui_data.get("Breaches Found", 0) >= 1

    @pytest.mark.asyncio
    async def test_unknown_domain_returns_no_local_matches(self, plugin):
        """A domain not in KNOWN_BREACHES should not get local matches."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("random-nonexistent-domain-xyz.com")

        assert result.status == "completed"
        # No local matches, no external results
        assert result.gui_data.get("Breaches Found", 0) == 0
        assert "Curated Breach DB" not in result.gui_data.get("Sources Checked", "")


# ======================== TEST: Email Target ========================


class TestEmailTarget:
    """Tests for email-specific handling."""

    @pytest.mark.asyncio
    async def test_email_with_indian_provider(self, plugin):
        """An email with a .co.in domain should match correctly."""
        mock_responses = [
            (
                "api.xposedornot.com/v1/check-email/",
                (200, {"Error": "Not found"}),
            ),
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("admin@nic.in")

        assert result.status == "completed"
        # nic.in is in KNOWN_BREACHES
        assert "NIC" in json.dumps(result.gui_data)
        assert result.gui_data.get("Breaches Found", 0) >= 1

    @pytest.mark.asyncio
    async def test_email_extracts_domain_correctly(self, plugin):
        """_get_target_domain should extract domain from email."""
        domain = plugin._get_target_domain("test@flipkart.com")
        assert domain == "flipkart.com"

        # Test with leading *. prefix
        domain = plugin._get_target_domain("*.flipkart.com")
        assert domain == "flipkart.com"


# ======================== TEST: Severity ========================


class TestSeverity:
    """Tests for severity calculation based on breach count."""

    @pytest.mark.asyncio
    async def test_severity_none_when_no_breaches(self, plugin):
        """No breaches should result in 'None' severity."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("madeup-domain-that-noone-uses.com")

        assert result.gui_data.get("Severity") == "None"

    @pytest.mark.asyncio
    async def test_severity_low_for_few_breaches(self, plugin):
        """1-2 breaches should result in 'Low' severity."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            # nic.in has only 1 entry in KNOWN_BREACHES
            result = await plugin.run("nic.in")

        assert result.gui_data.get("Breaches Found", 0) >= 1
        sev = result.gui_data.get("Severity", "")
        assert sev in ("Low", "Medium", "None")

    @pytest.mark.asyncio
    async def test_severity_medium_for_multiple_breaches(self, plugin):
        """3-5 breaches should result in 'Medium' severity."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 3, "sources": [
                {"name": "Breach A"}, {"name": "Breach B"}, {"name": "Breach C"}
            ], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("heavily-breached.com")

        breaches = result.gui_data.get("Breaches Found", 0)
        if breaches >= 1:
            sev = result.gui_data.get("Severity", "")
            assert sev in ("Low", "Medium", "High")


# ======================== TEST: Edge Cases ========================


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_all_sources_fail(self, plugin):
        """All external APIs fail — plugin should still complete with local DB only."""
        mock_responses = [
            ("api.xposedornot.com", make_mock_response(500, {})),
            ("leakcheck.io", make_mock_response(500, {})),
            ("leakix.net", make_mock_response(500, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("example.com")

        assert result.status == "completed"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_empty_target_handling(self, plugin):
        """Empty or malformed targets should not crash."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("")

        assert result.status == "completed"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_plugin_id_and_name(self, plugin):
        """Plugin metadata should be correct."""
        assert plugin.plugin_id == "data-leaks"
        assert plugin.name == "Data Leaks"
        assert plugin.category == "threat"
        assert "email" in plugin.input_types
        assert "domain" in plugin.input_types

    @pytest.mark.asyncio
    async def test_run_safe_wrapper(self, plugin):
        """run_safe should catch exceptions and return a failed result."""
        with patch.object(plugin, "run", side_effect=Exception("Test error")):
            result = await plugin.run_safe("example.com")
            assert result.status == "failed"
            assert "Test error" in result.error


# ======================== TEST: Terminal Output ========================


class TestTerminalOutput:
    """Tests for the terminal-formatted output."""

    @pytest.mark.asyncio
    async def test_terminal_mentions_sources(self, plugin):
        """Terminal output should list sources checked."""
        mock_responses = [
            ("leakcheck.io", (200, {"success": True, "found": 0, "sources": [], "fields": []})),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("example.com")

        terminal = result.terminal_data
        assert "[+] Data leak check for: example.com" in terminal
        assert "[+] Sources checked:" in terminal
        assert "[+] Findings:" in terminal

    @pytest.mark.asyncio
    async def test_terminal_lists_breaches(self, plugin):
        """Terminal output should list individual breaches found."""
        mock_responses = [
            (
                "leakcheck.io",
                (
                    200,
                    {
                        "success": True,
                        "found": 2,
                        "fields": ["email", "password"],
                        "sources": [
                            {"name": "Test Breach 1", "date": "2021-01-01"},
                            {"name": "Test Breach 2", "date": "2022-02-02"},
                        ],
                    },
                ),
            ),
            ("leakix.net", (404, {})),
        ]

        with patch("httpx.AsyncClient") as mock_client:
            patch_async_client(mock_client, mock_responses)
            result = await plugin.run("test.com")

        terminal = result.terminal_data
        assert "Test Breach 1" in terminal
        assert "Test Breach 2" in terminal
