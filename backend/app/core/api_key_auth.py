"""
TRINETRA — API Key Authentication

FastAPI dependency that validates API keys on protected endpoints.

Behavior:
    - If API_KEY env var is empty/unset: auth is DISABLED (dev mode, open access)
    - If API_KEY env var is set: all protected endpoints require a valid key

Accepted header formats:
    Authorization: Bearer <api_key>
    X-API-Key: <api_key>

Uses constant-time comparison (hmac.compare_digest) to prevent timing attacks.
"""

import hmac
import logging
from fastapi import Request, HTTPException, WebSocket
from app.core.config import settings

logger = logging.getLogger("trinetra.auth")


def _extract_key_from_headers(request: Request) -> str | None:
    """Extract API key from request headers.

    Supports:
        - Authorization: Bearer <key>
        - X-API-Key: <key>
    """
    # Check X-API-Key first (simpler for non-browser clients)
    api_key = request.headers.get("x-api-key")
    if api_key:
        return api_key

    # Check Authorization: Bearer <key>
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        return auth_header[7:].strip()

    return None


def _extract_key_from_query(request: Request) -> str | None:
    """Extract API key from query string (for WebSocket upgrade requests).

    Supports: ?api_key=<key>
    """
    return request.query_params.get("api_key")


def validate_api_key(provided: str | None) -> bool:
    """Validate the provided API key against the configured key.

    Returns True if auth is disabled (no key configured) or key matches.
    Uses constant-time comparison to prevent timing attacks.
    """
    configured = settings.api_key

    # Auth disabled — no key configured
    if not configured:
        return True

    # No key provided
    if not provided:
        return False

    if not isinstance(provided, str):
        return False

    # Constant-time comparison
    return hmac.compare_digest(provided, configured)


async def require_api_key(request: Request) -> str | None:
    """FastAPI dependency for HTTP endpoints.

    Raises 401 if API_KEY is configured and the request doesn't include a valid key.
    Returns the key if valid, or None if auth is disabled.
    """
    if not settings.api_key:
        # Auth disabled — open access
        return None

    key = _extract_key_from_headers(request)
    if key is None:
        key = _extract_key_from_query(request)

    if not validate_api_key(key):
        logger.warning(
            "API key rejected from %s",
            request.client.host if request.client else "unknown",
        )
        raise HTTPException(
            status_code=401,
            detail={
                "error": "Unauthorized",
                "detail": "Valid API key required. "
                "Provide via 'Authorization: Bearer <key>' header "
                "or 'X-API-Key: <key>' header.",
            },
        )

    return key


def validate_ws_message_key(data: dict) -> bool:
    """Validate API key from the first WebSocket JSON message.

    The client can send: {"api_key": "<key>", "target": "..."}
    Returns True if valid or auth is disabled.
    """
    return validate_api_key(data.get("api_key"))
