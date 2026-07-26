"""
TRINETRA — User Authentication with Registration

Users register with username + email + password (stored in SQLite with
hashed passwords). Login generates session tokens stored in memory.

Usage:
    POST /api/auth/register  { "username": "...", "email": "...", "password": "..." }
    → { "success": true, "token": "...", "username": "..." }

    POST /api/auth/login  { "username": "...", "password": "..." }
    → { "success": true, "token": "...", "username": "..." }
"""

import secrets
import hashlib
import logging
import os
from fastapi import Request, HTTPException

logger = logging.getLogger("trinetra.auth")

# In-memory store of valid session tokens: { token: username }
_active_tokens: dict[str, str] = {}

# Dedicated SQLite database for auth (works regardless of main DATABASE_URL)
# File is created in the app working directory (current dir or /app in Docker)
_AUTH_DB_PATH = os.environ.get("AUTH_DB_PATH", "trinetra_auth.db")

# ── Password hashing ──────────────────────────────────────


def _hash_password(password: str) -> str:
    """Hash a password with a random salt using SHA-256.
    Returns format: "salt:hash"
    """
    salt = secrets.token_hex(16)
    h = hashlib.sha256(f"{salt}:{password}".encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored hash."""
    try:
        salt, h = stored.split(":", 1)
        return hashlib.sha256(f"{salt}:{password}".encode()).hexdigest() == h
    except (ValueError, AttributeError):
        return False


# ── Database helpers — direct SQLite access ───────────────


def _get_db():
    """Get a synchronous SQLite connection for auth operations.
    Uses a dedicated auth database file independent of the main DATABASE_URL.
    """
    import sqlite3

    conn = sqlite3.connect(_AUTH_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=10000")
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_users_table():
    """Create the users table if it doesn't exist."""
    conn = _get_db()
    if not conn:
        return False
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                is_admin INTEGER DEFAULT 0,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
        return True
    except Exception as e:
        logger.error("Failed to init users table: %s", e)
        return False
    finally:
        conn.close()


def create_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """Create a new user. Returns (success, message)."""
    conn = _get_db()
    if not conn:
        return False, "Database not available"

    try:
        # Check if this is the first user (becomes admin)
        cursor = conn.execute("SELECT COUNT(*) as count FROM users")
        count = cursor.fetchone()["count"]
        is_admin = 1 if count == 0 else 0

        password_hash = _hash_password(password)
        conn.execute(
            "INSERT INTO users (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)",
            (username, email, password_hash, is_admin),
        )
        conn.commit()
        role = "admin" if is_admin else "user"
        return True, role
    except Exception as e:
        err = str(e)
        if "UNIQUE" in err:
            if "username" in err.lower():
                return False, "Username already taken"
            if "email" in err.lower():
                return False, "Email already registered"
        return False, f"Registration failed: {err}"
    finally:
        conn.close()


def get_user(username: str) -> dict | None:
    """Get a user by username. Returns None if not found."""
    conn = _get_db()
    if not conn:
        return None
    try:
        cursor = conn.execute(
            "SELECT id, username, email, password_hash, is_admin, created_at FROM users WHERE username = ?",
            (username,),
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    except Exception:
        return None
    finally:
        conn.close()


# ── Auth functions ────────────────────────────────────────


def is_auth_enabled() -> bool:
    """Auth is always enabled."""
    return True


def login(username: str, password: str) -> str | None:
    """Validate credentials and generate a session token.

    Returns the token string on success, or None on failure.
    """
    if not username or not password:
        return None

    user = get_user(username)
    if not user:
        return None

    if not _verify_password(password, user["password_hash"]):
        return None

    # Generate a cryptographically random token
    token = secrets.token_hex(32)
    _active_tokens[token] = username
    return token


def logout_token(token: str) -> bool:
    """Invalidate a session token. Returns True if it existed."""
    if token in _active_tokens:
        del _active_tokens[token]
        return True
    return False


def validate_token(token: str | None) -> bool:
    """Check if a session token is valid.

    Returns True if the token is in the active tokens store.
    """
    if not token:
        return False

    return token in _active_tokens


def get_username_for_token(token: str) -> str | None:
    """Get the username associated with a token, or None."""
    return _active_tokens.get(token)


def clear_all_tokens():
    """Clear all session tokens (used on server restart)."""
    _active_tokens.clear()


# ── Header extraction (kept from previous API key system) ─


def _extract_key_from_headers(request: Request) -> str | None:
    """Extract token from request headers.

    Supports:
        - Authorization: Bearer <token>
        - X-API-Key: <token>  (legacy name)
    """
    token = request.headers.get("x-api-key")
    if token:
        return token

    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    return None


def _extract_key_from_query(request: Request) -> str | None:
    """Extract token from query string (for WebSocket upgrade requests)."""
    return request.query_params.get("api_key")


# ── FastAPI dependency ────────────────────────────────────


async def require_api_key(request: Request) -> str | None:
    """FastAPI dependency for HTTP endpoints.

    Checks for a valid session token in headers.
    Raises 401 if no valid token is provided.
    """
    token = _extract_key_from_headers(request)
    if token is None:
        token = _extract_key_from_query(request)

    if not validate_token(token):
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Unauthorized",
                "detail": "Valid session token required. "
                "Register via POST /api/auth/register then "
                "log in via POST /api/auth/login.",
            },
        )

    return token


def validate_ws_message_key(data: dict) -> bool:
    """Validate session token from the first WebSocket JSON message."""
    return validate_token(data.get("api_key"))
