"""
TRINETRA — API Key Authentication Tests (Updated for bcrypt + DB sessions)

Tests for ``app.core.api_key_auth`` covering:
* Password hashing with bcrypt
* Database-backed session storage
* Account lockout after failed attempts
* Generic error messages (no username enumeration)
* Token validation (database-backed)
* require_api_key — FastAPI HTTP dependency
"""

import pytest
import tempfile
import os
from unittest.mock import MagicMock, patch
from fastapi import HTTPException, Request

from app.core import api_key_auth
from app.core.config import settings


# ── Fixtures ──────────────────────────────────────────────


@pytest.fixture(autouse=True)
def _reset_auth_db():
    """Create a fresh auth database for each test."""
    # Use a temporary file for each test
    fd, db_path = tempfile.mkstemp(suffix=".db", prefix="trinetra_auth_test_")
    os.close(fd)
    
    # Set the auth DB path
    original_path = api_key_auth._AUTH_DB_PATH
    api_key_auth._AUTH_DB_PATH = db_path
    
    # Initialize the tables
    api_key_auth.init_users_table()
    
    yield
    
    # Cleanup
    api_key_auth._AUTH_DB_PATH = original_path
    try:
        os.unlink(db_path)
    except OSError:
        pass


def _make_request(
    headers: dict | None = None,
    query_params: dict | None = None,
    client_host: str = "127.0.0.1",
) -> Request:
    """Build a minimal FastAPI Request for testing."""
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


# ======================== Password Hashing Tests ========================


class TestPasswordHashing:
    def test_hash_password_returns_bcrypt_hash(self):
        """Password hash should start with $2 (bcrypt format)."""
        password = "my_secure_password_123"
        hashed = api_key_auth._hash_password(password)
        assert hashed.startswith("$2"), f"Expected bcrypt hash, got: {hashed[:10]}..."

    def test_hash_password_is_different_each_time(self):
        """Each hash should be unique due to random salt."""
        password = "same_password"
        hash1 = api_key_auth._hash_password(password)
        hash2 = api_key_auth._hash_password(password)
        assert hash1 != hash2, "Bcrypt hashes should be unique due to random salt"

    def test_verify_password_correct(self):
        """Correct password should verify successfully."""
        password = "test_password_123"
        hashed = api_key_auth._hash_password(password)
        assert api_key_auth._verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Wrong password should fail verification."""
        password = "correct_password"
        wrong_password = "wrong_password"
        hashed = api_key_auth._hash_password(password)
        assert api_key_auth._verify_password(wrong_password, hashed) is False

    def test_verify_password_empty_string(self):
        """Empty password should not match."""
        password = "some_password"
        hashed = api_key_auth._hash_password(password)
        assert api_key_auth._verify_password("", hashed) is False

    def test_verify_password_invalid_hash(self):
        """Invalid hash format should return False."""
        assert api_key_auth._verify_password("password", "not_a_valid_hash") is False


# ======================== User Registration Tests ========================


class TestUserRegistration:
    def test_create_first_user_becomes_admin(self):
        """First registered user should become admin."""
        success, result = api_key_auth.create_user("admin", "admin@test.com", "Admin@Pass1")
        assert success is True
        assert result == "admin"

    def test_create_second_user_is_regular(self):
        """Subsequent users should be regular users."""
        api_key_auth.create_user("admin", "admin@test.com", "Admin@Pass1")
        success, result = api_key_auth.create_user("user1", "user1@test.com", "User1@Pass1")
        assert success is True
        assert result == "user"

    def test_create_user_duplicate_username(self):
        """Duplicate username should fail with generic error."""
        api_key_auth.create_user("admin", "admin@test.com", "Admin@Pass1")
        success, result = api_key_auth.create_user("admin", "other@test.com", "Other@Pass1")
        assert success is False
        # Generic message to prevent enumeration
        assert "Username or email already exists" in result or "Registration failed" in result

    def test_create_user_duplicate_email(self):
        """Duplicate email should fail with generic error."""
        api_key_auth.create_user("admin", "admin@test.com", "Admin@Pass1")
        success, result = api_key_auth.create_user("other", "admin@test.com", "Other@Pass1")
        assert success is False
        assert "Username or email already exists" in result or "Registration failed" in result

    def test_create_user_password_reuse_rejected(self):
        """Registration with recently used password should be rejected."""
        api_key_auth.create_user("admin", "admin@test.com", "Admin@Pass1")
        success, result = api_key_auth.create_user("user1", "user1@test.com", "Admin@Pass1")
        assert success is False
        assert "recently used" in result.lower()

    def test_get_user_returns_user_data(self):
        """get_user should return user data."""
        api_key_auth.create_user("testuser", "test@test.com", "password123")
        user = api_key_auth.get_user("testuser")
        assert user is not None
        assert user["username"] == "testuser"
        assert user["email"] == "test@test.com"
        assert "password_hash" in user

    def test_get_user_nonexistent_returns_none(self):
        """get_user should return None for non-existent users."""
        user = api_key_auth.get_user("nonexistent")
        assert user is None


# ======================== Login Tests ========================


class TestLogin:
    def test_login_success(self):
        """Successful login should return a token."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        token = api_key_auth.login("testuser", "Test@Pass1")
        assert token is not None
        assert len(token) == 64  # 32 bytes hex = 64 chars

    def test_login_wrong_password(self):
        """Wrong password should return None."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        token = api_key_auth.login("testuser", "wrong_password")
        assert token is None

    def test_login_nonexistent_user(self):
        """Non-existent user should return None."""
        token = api_key_auth.login("nonexistent", "Test@Pass1")
        assert token is None

    def test_login_empty_credentials(self):
        """Empty credentials should return None."""
        assert api_key_auth.login("", "Test@Pass1") is None
        assert api_key_auth.login("user", "") is None

    def test_login_creates_session_in_database(self):
        """Login should create a session in the database."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        token = api_key_auth.login("testuser", "Test@Pass1")
        assert token is not None
        # Verify session exists in database
        assert api_key_auth.validate_token(token) is True


# ======================== Account Lockout Tests ========================


class TestAccountLockout:
    def test_lockout_after_max_attempts(self):
        """Account should be locked after MAX_LOGIN_ATTEMPTS failed attempts."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        
        # Make MAX_LOGIN_ATTEMPTS failed attempts
        for _ in range(api_key_auth.MAX_LOGIN_ATTEMPTS):
            api_key_auth.login("testuser", "wrong_password")
        
        # Account should now be locked
        assert api_key_auth._is_account_locked("testuser") is True
        
        # Even correct password should fail
        token = api_key_auth.login("testuser", "Test@Pass1")
        assert token is None

    def test_successful_login_clears_attempts(self):
        """Successful login should clear failed attempts."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        
        # Make some failed attempts
        for _ in range(3):
            api_key_auth.login("testuser", "wrong_password")
        
        # Successful login should clear attempts
        token = api_key_auth.login("testuser", "Test@Pass1")
        assert token is not None
        
        # Account should not be locked
        assert api_key_auth._is_account_locked("testuser") is False


# ======================== Token Validation Tests ========================


class TestTokenValidation:
    def test_validate_valid_token(self):
        """Valid token should pass validation."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        token = api_key_auth.login("testuser", "Test@Pass1")
        assert api_key_auth.validate_token(token) is True

    def test_validate_invalid_token(self):
        """Invalid token should fail validation."""
        assert api_key_auth.validate_token("invalid_token_12345") is False

    def test_validate_none_token(self):
        """None token should fail validation."""
        assert api_key_auth.validate_token(None) is False

    def test_validate_empty_token(self):
        """Empty token should fail validation."""
        assert api_key_auth.validate_token("") is False

    def test_logout_invalidates_token(self):
        """Logout should invalidate the token."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        token = api_key_auth.login("testuser", "Test@Pass1")
        assert token is not None
        
        # Logout
        result = api_key_auth.logout_token(token)
        assert result is True
        
        # Token should now be invalid
        assert api_key_auth.validate_token(token) is False

    def test_get_username_for_token(self):
        """get_username_for_token should return the username."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        token = api_key_auth.login("testuser", "Test@Pass1")
        username = api_key_auth.get_username_for_token(token)
        assert username == "testuser"

    def test_get_username_for_invalid_token(self):
        """get_username_for_token should return None for invalid token."""
        assert api_key_auth.get_username_for_token("invalid_token") is None


# ======================== require_api_key Tests ========================


class TestRequireApiKey:
    @pytest.mark.asyncio
    async def test_valid_token_accepted(self):
        """Valid token in header should be accepted."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass1")
        token = api_key_auth.login("testuser", "Test@Pass1")
        
        request = _make_request(headers={"X-API-Key": token})
        result = await api_key_auth.require_api_key(request)
        assert result == token

    @pytest.mark.asyncio
    async def test_valid_bearer_token_accepted(self):
        """Valid Bearer token should be accepted."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass2")
        token = api_key_auth.login("testuser", "Test@Pass2")
        
        request = _make_request(headers={"Authorization": f"Bearer {token}"})
        result = await api_key_auth.require_api_key(request)
        assert result == token

    @pytest.mark.asyncio
    async def test_invalid_token_raises_401(self):
        """Invalid token should raise HTTP 401."""
        request = _make_request(headers={"X-API-Key": "invalid_token"})
        with pytest.raises(HTTPException) as exc_info:
            await api_key_auth.require_api_key(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_no_token_raises_401(self):
        """Missing token should raise HTTP 401."""
        request = _make_request()
        with pytest.raises(HTTPException) as exc_info:
            await api_key_auth.require_api_key(request)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_query_param_token_accepted(self):
        """Token in query params should be accepted."""
        api_key_auth.create_user("testuser", "test@test.com", "Test@Pass3")
        token = api_key_auth.login("testuser", "Test@Pass3")
        
        request = _make_request(query_params={"api_key": token})
        result = await api_key_auth.require_api_key(request)
        assert result == token


# ======================== WebSocket Validation Tests ========================


class TestValidateWsMessage:
    def test_valid_token_in_message(self):
        """Valid token in message should pass."""
        api_key_auth.create_user("testuser", "test@test.com", "Ws@Pass1")
        token = api_key_auth.login("testuser", "Ws@Pass1")
        
        assert api_key_auth.validate_ws_message_key({"api_key": token}) is True

    def test_invalid_token_in_message(self):
        """Invalid token in message should fail."""
        assert api_key_auth.validate_ws_message_key({"api_key": "invalid"}) is False

    def test_missing_token_in_message(self):
        """Missing token in message should fail."""
        assert api_key_auth.validate_ws_message_key({"target": "example.com"}) is False

    def test_empty_message(self):
        """Empty message should fail."""
        assert api_key_auth.validate_ws_message_key({}) is False
