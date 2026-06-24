"""
TRINETRA — Reverse DNS Plugin Unit Tests

Tests for the ReverseDNSPlugin with mocked socket and dnspython calls.
Covers:
* Domain input with successful resolution and PTR records
* IP input with PTR records
* No PTR records found
* Resolution failure (NXDOMAIN / unresolvable)
* PTR lookup timeout / error
* Plugin metadata
* run_safe wrapper
* Terminal and GUI output formatting
"""

import pytest
from unittest.mock import patch, MagicMock
from app.plugins.infrastructure.reverse_dns import ReverseDNSPlugin


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture
def plugin():
    return ReverseDNSPlugin()


# ── Helpers ───────────────────────────────────────────────


def make_ptr_answers(*records: str):
    """Build a mock dns.resolver.Answer that yields the given PTR records."""
    mock_answer = MagicMock()
    mock_records = []
    for r in records:
        m = MagicMock()
        m.__str__.return_value = r
        mock_records.append(m)
    mock_answer.__iter__.return_value = iter(mock_records)
    return mock_answer


# ======================== TEST: Domain Input ========================


class TestDomainInput:
    """Tests for domain target resolution and PTR lookup."""

    @pytest.mark.asyncio
    async def test_domain_resolves_and_finds_ptr(self, plugin):
        """Domain resolves to an IP and returns PTR records."""
        mock_ptr_answer = make_ptr_answers("mail.example.com.", "www.example.com.")

        with (
            patch("socket.gethostbyname", return_value="93.184.216.34") as mock_gethost,
            patch("dns.reversename.from_address", return_value="34.216.184.93.in-addr.arpa") as mock_rev,
            patch("dns.resolver.resolve", return_value=mock_ptr_answer) as mock_resolve,
        ):
            result = await plugin.run("example.com")

        assert result.status == "completed"
        assert result.target == "example.com"
        assert result.gui_data["Target"] == "example.com"
        assert result.gui_data["Resolved IP"] == "93.184.216.34"
        assert "mail.example.com" in result.gui_data["PTR Records"]
        assert "www.example.com" in result.gui_data["PTR Records"]

        mock_gethost.assert_called_once_with("example.com")
        mock_rev.assert_called_once_with("93.184.216.34")
        mock_resolve.assert_called_once()

    @pytest.mark.asyncio
    async def test_domain_with_single_ptr(self, plugin):
        """Domain with a single PTR record."""
        mock_ptr_answer = make_ptr_answers("server-1.example.com.")

        with (
            patch("socket.gethostbyname", return_value="192.0.2.1"),
            patch("dns.reversename.from_address", return_value="1.2.0.192.in-addr.arpa"),
            patch("dns.resolver.resolve", return_value=mock_ptr_answer),
        ):
            result = await plugin.run("server.example.com")

        assert result.status == "completed"
        assert result.gui_data["PTR Records"] == "server-1.example.com."

    @pytest.mark.asyncio
    async def test_domain_no_ptr_records(self, plugin):
        """Domain resolves to an IP but has no PTR records (empty results)."""
        mock_ptr_answer = make_ptr_answers()  # Empty iterator

        with (
            patch("socket.gethostbyname", return_value="10.0.0.1"),
            patch("dns.reversename.from_address", return_value="1.0.0.10.in-addr.arpa"),
            patch("dns.resolver.resolve", return_value=mock_ptr_answer),
        ):
            result = await plugin.run("no-ptr.example.com")

        assert result.status == "completed"
        assert result.gui_data["Resolved IP"] == "10.0.0.1"
        assert result.gui_data["PTR Records"] == "None"

    @pytest.mark.asyncio
    async def test_domain_unresolvable(self, plugin):
        """Domain cannot be resolved (e.g. NXDOMAIN) — graceful error handling."""
        with patch("socket.gethostbyname", side_effect=OSError("Name or service not known")):
            result = await plugin.run("nonexistent.invalid")

        assert result.status == "completed"
        assert result.gui_data["Target"] == "nonexistent.invalid"
        assert result.gui_data["Resolved IP"] == "N/A"
        assert result.gui_data["PTR Records"] == "Error / Not found"
        assert "Error" in result.terminal_data
        assert "Name or service not known" in result.terminal_data


# ======================== TEST: IP Input ========================


class TestIPInput:
    """Tests for IP address target handling."""

    @pytest.mark.asyncio
    async def test_ip_resolves_to_ptr(self, plugin):
        """Direct IP input resolves to PTR records."""
        mock_ptr_answer = make_ptr_answers("host-93-184-216-34.example.com.")

        with (
            patch("socket.gethostbyname", return_value="93.184.216.34") as mock_gethost,
            patch("dns.reversename.from_address", return_value="34.216.184.93.in-addr.arpa") as mock_rev,
            patch("dns.resolver.resolve", return_value=mock_ptr_answer) as mock_resolve,
        ):
            result = await plugin.run("93.184.216.34")

        assert result.status == "completed"
        assert result.gui_data["Target"] == "93.184.216.34"
        assert result.gui_data["Resolved IP"] == "93.184.216.34"
        assert "host-93-184-216-34.example.com" in result.gui_data["PTR Records"]

        # gethostbyname on an IP returns it unchanged
        mock_gethost.assert_called_once_with("93.184.216.34")
        mock_rev.assert_called_once_with("93.184.216.34")
        mock_resolve.assert_called_once()

    @pytest.mark.asyncio
    async def test_ip_with_multiple_ptr(self, plugin):
        """IP with multiple PTR records (common for shared hosting)."""
        mock_ptr_answer = make_ptr_answers(
            "server-1.example.com.",
            "server-2.example.com.",
            "mail.example.com.",
        )

        with (
            patch("socket.gethostbyname", return_value="198.51.100.10"),
            patch("dns.reversename.from_address", return_value="10.100.51.198.in-addr.arpa"),
            patch("dns.resolver.resolve", return_value=mock_ptr_answer),
        ):
            result = await plugin.run("198.51.100.10")

        assert result.status == "completed"
        ptr_records = result.gui_data["PTR Records"]
        assert "server-1.example.com." in ptr_records
        assert "server-2.example.com." in ptr_records
        assert "mail.example.com." in ptr_records
        # Should be comma-joined
        assert ptr_records.count(", ") == 2

    @pytest.mark.asyncio
    async def test_ip_no_ptr_records(self, plugin):
        """IP with no PTR records returns 'None found'."""
        # Simulate an NXDOMAIN or NoAnswer from dns.resolver
        with (
            patch("socket.gethostbyname", return_value="192.168.1.1"),
            patch("dns.reversename.from_address", return_value="1.1.168.192.in-addr.arpa"),
            patch("dns.resolver.resolve", side_effect=Exception("The DNS query does not exist")),
        ):
            result = await plugin.run("192.168.1.1")

        assert result.status == "completed"
        assert result.gui_data["Resolved IP"] == "192.168.1.1"
        assert result.gui_data["PTR Records"] == "Error / Not found"
        assert "The DNS query does not exist" in result.terminal_data


# ======================== TEST: Error Handling ========================


class TestErrorHandling:
    """Tests for various error scenarios."""

    @pytest.mark.asyncio
    async def test_ptr_lookup_timeout(self, plugin):
        """PTR lookup timeout returns error gracefully."""
        with (
            patch("socket.gethostbyname", return_value="203.0.113.5"),
            patch("dns.reversename.from_address", return_value="5.113.0.203.in-addr.arpa"),
            patch("dns.resolver.resolve", side_effect=Exception("Timeout")),
        ):
            result = await plugin.run("203.0.113.5")

        assert result.status == "completed"
        assert result.gui_data["PTR Records"] == "Error / Not found"
        assert "Timeout" in result.terminal_data

    @pytest.mark.asyncio
    async def test_socket_error(self, plugin):
        """Socket error during gethostbyname is handled gracefully."""
        with patch("socket.gethostbyname", side_effect=OSError("Temporary failure in name resolution")):
            result = await plugin.run("bad.example.com")

        assert result.status == "completed"
        assert result.gui_data["Resolved IP"] == "N/A"
        assert result.gui_data["PTR Records"] == "Error / Not found"
        assert "Temporary failure in name resolution" in result.terminal_data

    @pytest.mark.asyncio
    async def test_empty_target(self, plugin):
        """Empty target raises an error (empty hostname) caught gracefully."""
        with patch("socket.gethostbyname", side_effect=OSError("No address associated with hostname")):
            result = await plugin.run("")

        assert result.status == "completed"
        assert result.gui_data["PTR Records"] == "Error / Not found"


# ======================== TEST: Plugin Metadata ========================


class TestPluginMetadata:
    """Tests for plugin identity and metadata."""

    def test_plugin_id_and_name(self, plugin):
        """Plugin metadata should be correct."""
        assert plugin.plugin_id == "reverse-dns"
        assert plugin.name == "Reverse DNS"
        assert plugin.category == "infrastructure"
        assert plugin.description == "Resolves target to IP and fetches PTR records"
        assert plugin.icon == "🔄"

    def test_input_types(self, plugin):
        """Should support both domain and IP inputs."""
        assert "domain" in plugin.input_types
        assert "ip" in plugin.input_types
        assert len(plugin.input_types) == 2

    @pytest.mark.asyncio
    async def test_run_safe_wrapper(self, plugin):
        """run_safe should catch exceptions and return a failed result."""
        with patch.object(plugin, "run", side_effect=Exception("Unexpected error")):
            result = await plugin.run_safe("example.com")
            assert result.status == "failed"
            assert "Unexpected error" in result.error


# ======================== TEST: Output Formatting ========================


class TestOutputFormatting:
    """Tests for GUI and terminal output formatting."""

    @pytest.mark.asyncio
    async def test_gui_data_structure(self, plugin):
        """GUI data should contain expected keys."""
        mock_ptr_answer = make_ptr_answers("host.example.com.")

        with (
            patch("socket.gethostbyname", return_value="1.2.3.4"),
            patch("dns.reversename.from_address", return_value="4.3.2.1.in-addr.arpa"),
            patch("dns.resolver.resolve", return_value=mock_ptr_answer),
        ):
            result = await plugin.run("example.com")

        gui = result.gui_data
        assert "Target" in gui
        assert "Resolved IP" in gui
        assert "PTR Records" in gui

    @pytest.mark.asyncio
    async def test_terminal_output_format(self, plugin):
        """Terminal output should contain target, IP, and PTR records."""
        mock_ptr_answer = make_ptr_answers("server.example.com.")

        with (
            patch("socket.gethostbyname", return_value="5.6.7.8"),
            patch("dns.reversename.from_address", return_value="8.7.6.5.in-addr.arpa"),
            patch("dns.resolver.resolve", return_value=mock_ptr_answer),
        ):
            result = await plugin.run("test.example.com")

        terminal = result.terminal_data
        assert "Target: test.example.com" in terminal
        assert "Resolved IP: 5.6.7.8" in terminal
        assert "PTR Records: server.example.com." in terminal

    @pytest.mark.asyncio
    async def test_terminal_output_on_error(self, plugin):
        """Terminal output should include error message on failure."""
        with patch("socket.gethostbyname", side_effect=OSError("DNS resolution failed")):
            result = await plugin.run("broken.test")

        terminal = result.terminal_data
        assert "Target: broken.test" in terminal
        assert "Error" in terminal
        assert "DNS resolution failed" in terminal
