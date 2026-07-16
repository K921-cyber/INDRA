"""
TRINETRA — API Key Authentication Tests

Tests for ``app.core.api_key_auth`` covering:
* validate_api_key — constant-time comparison, auth disabled/enabled, edge cases
* require_api_key — FastAPI HTTP dependency with mocked Request
* _extract_key_from_headers — Bearer token, X-API-Key header, missing
* _extract_key_from_query — query param extraction
* validate_ws_message_key — WebSocket first-message auth
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request

from app.core import api_key_auth
from app.core.config import settings


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_api_key():
    """Ensure api_key is empty (auth disabled) before each test."""
    original = settings.api_key
    settings.api_key = ""
    yield
    settings.api_key = original


@pytest.fixture
def auth_enabled():
    """Temporarily enable API key auth with a known key."""
    settings.api_key = "test-secret-key-12345"
    yield
    settings.api_key = ""


def _make_request(
    headers: dict | None = None,
    query_params: dict | None = None,
    client_host: str = "127.0.0.1",
) -> Request:
    """Build a minimal FastAPI Request for testing."""
    from starlette.testclient import TestClient
    from starlette.applications import Starlette
    from starlette.routing import Route
    from starlette.requests import Request as StarletteRequest

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/test",
        "query_string": b"",
        "headers": [],
        "client": (client_host, 12345),
    }

    # Build raw headers as list of (lowercase_name, value) tuples
    raw_headers = []
    for k, v in (headers or {}).items():
        raw_headers.append((k.lower().encode(), v.encode()))
    scope["headers"] = raw_headers

    # Build query string
    if query_params:
        qs = "&".join(f"{k}={v}" for k, v in query_params.items())
        scope["query_string"] = qs.encode()

    return StarletteRequest(scope)


# ======================== validate_api_key ========================


class TestValidateApiKey:
    def test_auth_disabled_any_key_passes(self):
        """When API_KEY is empty, any provided key should pass."""
        assert api_key_auth.validate_api_key(None) is True
        assert api_key_auth.validate_api_key("") is True
        assert api_key_auth.validate_api_key("anything") is True
        assert api_key_auth.validate_api_key(123) is True

    @pytest.mark.usefixtures("auth_enabled")
    def test_correct_key_passes(self):
        """A correct key should be accepted."""
        assert api_key_auth.validate_api_key("test-secret-key-12345") is True

    @pytest.mark.usefixtures("auth_enabled")
    def test_wrong_key_rejected(self):
        """An incorrect key should be rejected."""
        assert api_key_auth.validate_api_key("wrong-key") is False
        assert api_key_auth.validate_api_key("test-secret-key-1234") is False  # off by one
        assert api_key_auth.validate_api_key("test-secret-key-123456") is False  # extra char

    @pytest.mark.usefixtures("auth_enabled")
    def test_none_rejected(self):
        """None should be rejected when auth is enabled."""
        assert api_key_auth.validate_api_key(None) is False

    @pytest.mark.usefixtures("auth_enabled")
    def test_empty_string_rejected(self):
        """Empty string should be rejected when auth is enabled."""
        assert api_key_auth.validate_api_key("") is False

    @pytest.mark.usefixtures("auth_enabled")
    def test_non_string_rejected(self):
        """Non-string types should be rejected when auth is enabled."""
        assert api_key_auth.validate_api_key(123) is False
        assert api_key_auth.validate_api_key(True) is False
        assert api_key_auth.validate_api_key([]) is False

    @pytest.mark.usefixtures("auth_enabled")
    def test_timing_safe_comparison(self):
        """Correct key should use hmac.compare_digest (no timing side-channel).

        We verify by checking that both the correct key and a similar-length
        wrong key are handled by the same code path. The actual timing safety
        is guaranteed by hmac.compare_digest itself.
        """
        import hmac as hmac_mod

        # Verify the function returns the same result as hmac.compare_digest
        correct = "test-secret-key-12345"
        wrong = "test-secret-key-AAAAA"
        expected_correct = hmac_mod.compare_digest(correct, settings.api_key)
        expected_wrong = hmac_mod.compare_digest(wrong, settings.api_key)

        assert api_key_auth.validate_api_key(correct) == expected_correct
        assert api_key_auth.validate_api_key(wrong) == expected_wrong

    @pytest.mark.usefixtures("auth_enabled")
    def test_whitespace_in_key_rejected(self):
        """Leading/trailing whitespace should cause rejection."""
        assert api_key_auth.validate_api_key("  test-secret-key-12345  ") is False
        assert api_key_auth.validate_api_key("test-secret-key-12345\n") is False


# ======================== _extract_key_from_headers ========================


class TestExtractKeyFromHeaders:
    def test_x_api_key_header(self):
        """X-API-Key header is extracted correctly."""
        request = _make_request(headers={"X-API-Key": "my-key-123"})
        assert api_key_auth._extract_key_from_headers(request) == "my-key-123"

    def test_authorization_bearer(self):
        """Authorization: Bearer <key> is extracted correctly."""
        request = _make_request(headers={"Authorization": "Bearer my-token-abc"})
        assert api_key_auth._extract_key_from_headers(request) == "my-token-abc"

    def test_authorization_bearer_case_insensitive(self):
        """Bearer prefix is case-insensitive."""
        request = _make_request(headers={"Authorization": "bearer my-token"})
        assert api_key_auth._extract_key_from_headers(request) == "my-token"

        request = _make_request(headers={"Authorization": "BEARER my-token"})
        assert api_key_auth._extract_key_from_headers(request) == "my-token"

    def test_bearer_with_extra_spaces(self):
        """Bearer token extraction handles whitespace."""
        request = _make_request(headers={"Authorization": "Bearer   my-token  "})
        assert api_key_auth._extract_key_from_headers(request) == "my-token"

    def test_no_auth_headers_returns_none(self):
        """No auth headers should return None."""
        request = _make_request(headers={})
        assert api_key_auth._extract_key_from_headers(request) is None

    def test_x_api_key_takes_priority(self):
        """X-API-Key should be checked before Authorization."""
        request = _make_request(headers={
            "X-API-Key": "from-x-api",
            "Authorization": "Bearer from-bearer",
        })
        # X-API-Key is checked first
        assert api_key_auth._extract_key_from_headers(request) == "from-x-api"

    def test_non_bearer_authorization_ignored(self):
        """Authorization header without Bearer prefix should return None."""
        request = _make_request(headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert api_key_auth._extract_key_from_headers(request) is None


# ======================== _extract_key_from_query ========================


class TestExtractKeyFromQuery:
    def test_query_param_present(self):
        """API key from query params is extracted."""
        request = _make_request(query_params={"api_key": "query-key-123"})
        assert api_key_auth._extract_key_from_query(request) == "query-key-123"

    def test_query_param_missing(self):
        """Missing query param returns None."""
        request = _make_request(query_params={})
        assert api_key_auth._extract_key_from_query(request) is None

    def test_other_query_params_ignored(self):
        """Other query params don't interfere."""
        request = _make_request(query_params={"target": "example.com", "format": "json"})
        assert api_key_auth._extract_key_from_query(request) is None


# ======================== require_api_key ========================


class TestRequireApiKey:
    @pytest.mark.asyncio
    async def test_auth_disabled_returns_none(self):
        """When auth is disabled, require_api_key returns None."""
        request = _make_request()
        result = await api_key_auth.require_api_key(request)
        assert result is None

    @pytest.mark.usefixtures("auth_enabled")
    @pytest.mark.asyncio
    async def test_valid_bearer_token_accepted(self):
        """Valid Bearer token is accepted."""
        request = _make_request(headers={"Authorization": "Bearer test-secret-key-12345"})
        result = await api_key_auth.require_api_key(request)
        assert result == "test-secret-key-12345"

    @pytest.mark.usefixtures("auth_enabled")
    @pytest.mark.asyncio
    async def test_valid_x_api_key_accepted(self):
        """Valid X-API-Key header is accepted."""
        request = _make_request(headers={"X-API-Key": "test-secret-key-12345"})
        result = await api_key_auth.require_api_key(request)
        assert result == "test-secret-key-12345"

    @pytest.mark.usefixtures("auth_enabled")
    @pytest.mark.asyncio
    async def test_valid_query_param_accepted(self):
        """Valid api_key query param is accepted."""
        request = _make_request(query_params={"api_key": "test-secret-key-12345"})
        result = await api_key_auth.require_api_key(request)
        assert result == "test-secret-key-12345"

    @pytest.mark.usefixtures("auth_enabled")
    @pytest.mark.asyncio
    async def test_no_key_raises_401(self):
        """Missing key raises HTTP 401."""
        request = _make_request()
        with pytest.raises(HTTPException) as exc_info:
            await api_key_auth.require_api_key(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.usefixtures("auth_enabled")
    @pytest.mark.asyncio
    async def test_wrong_key_raises_401(self):
        """Wrong key raises HTTP 401."""
        request = _make_request(headers={"X-API-Key": "wrong-key"})
        with pytest.raises(HTTPException) as exc_info:
            await api_key_auth.require_api_key(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.usefixtures("auth_enabled")
    @pytest.mark.asyncio
    async def test_x_api_key_takes_priority_over_bearer(self):
        """When both X-API-Key and Bearer are present, X-API-Key wins."""
        request = _make_request(headers={
            "X-API-Key": "test-secret-key-12345",
            "Authorization": "Bearer wrong-key",
        })
        result = await api_key_auth.require_api_key(request)
        assert result == "test-secret-key-12345"

    @pytest.mark.usefixtures("auth_enabled")
    @pytest.mark.asyncio
    async def test_401_detail_includes_helpful_message(self):
        """401 error detail should include usage instructions."""
        request = _make_request()
        with pytest.raises(HTTPException) as exc_info:
            await api_key_auth.require_api_key(request)
        detail = exc_info.value.detail
        assert "Unauthorized" in detail["error"]
        assert "Authorization" in detail["detail"] or "X-API-Key" in detail["detail"]


# ======================== validate_ws_message_key ========================


class TestValidateWsMessageKey:
    def test_auth_disabled_any_message_passes(self):
        """When auth is disabled, any message dict passes."""
        assert api_key_auth.validate_ws_message_key({}) is True
        assert api_key_auth.validate_ws_message_key({"api_key": "anything"}) is True

    @pytest.mark.usefixtures("auth_enabled")
    def test_correct_key_in_message(self):
        """Correct api_key in message passes."""
        assert api_key_auth.validate_ws_message_key(
            {"api_key": "test-secret-key-12345", "target": "example.com"}
        ) is True

    @pytest.mark.usefixtures("auth_enabled")
    def test_wrong_key_in_message(self):
        """Wrong api_key in message is rejected."""
        assert api_key_auth.validate_ws_message_key(
            {"api_key": "wrong-key", "target": "example.com"}
        ) is False

    @pytest.mark.usefixtures("auth_enabled")
    def test_missing_key_in_message(self):
        """Missing api_key field in message is rejected."""
        assert api_key_auth.validate_ws_message_key(
            {"target": "example.com"}
        ) is False

    @pytest.mark.usefixtures("auth_enabled")
    def test_none_key_in_message(self):
        """api_key: None in message is rejected."""
        assert api_key_auth.validate_ws_message_key(
            {"api_key": None, "target": "example.com"}
        ) is False

    @pytest.mark.usefixtures("auth_enabled")
    def test_empty_message_dict(self):
        """Empty message dict is rejected when auth is enabled."""
        assert api_key_auth.validate_ws_message_key({}) is False
