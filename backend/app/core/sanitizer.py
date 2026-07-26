"""
TRINETRA — Input Sanitization

Validates and sanitizes search targets before they reach plugins.
Prevents injection attacks, command injection, and abuse of external
APIs through crafted inputs.

Rules:
    - Max 253 characters (DNS hostname limit)
    - No control characters, null bytes, or shell metacharacters
    - Domain/IP/email/phone validated against strict patterns
    - Names allow only letters, spaces, hyphens, dots, and @
"""

import re

# ── Max target length (DNS hostname max is 253 chars) ───────
MAX_TARGET_LENGTH = 253

# ── Characters that should never appear in OSINT targets ────
# Shell metacharacters, control chars, null bytes
FORBIDDEN_CHARS = re.compile(r"[\x00-\x1f\x7f`$;|&{}()!#<>\"'\\]")

# ── Strict per-type patterns ────────────────────────────────
STRICT_IP = re.compile(
    r"^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$"
)
STRICT_EMAIL = re.compile(
    r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
)
STRICT_DOMAIN = re.compile(
    r"^[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?(\.[a-zA-Z0-9]([a-zA-Z0-9\-]*[a-zA-Z0-9])?)*\.[a-zA-Z]{2,}$"
)
STRICT_PHONE = re.compile(
    r"^\+?[\d\s\-().]{7,20}$"
)
# Names: letters, spaces, dots, hyphens, apostrophes, @ for email-like names
STRICT_NAME = re.compile(
    r"^[a-zA-Z0-9.\s\-_'@]+$"
)


class InputValidationError(Exception):
    """Raised when a search target fails validation."""

    def __init__(self, message: str, detail: str = ""):
        self.message = message
        self.detail = detail
        super().__init__(message)


def sanitize_target(raw: str) -> str:
    """Strip and validate a raw search target string.

    Returns the cleaned target string, or raises InputValidationError.
    """
    if not raw or not raw.strip():
        raise InputValidationError("Target cannot be empty")

    target = raw.strip()

    # Length check
    if len(target) > MAX_TARGET_LENGTH:
        raise InputValidationError(
            f"Target exceeds maximum length of {MAX_TARGET_LENGTH} characters",
            f"Received {len(target)} characters",
        )

    # Null byte / control character check
    if FORBIDDEN_CHARS.search(target):
        raise InputValidationError(
            "Target contains forbidden characters",
            "Control characters, shell metacharacters, and null bytes are not allowed",
        )

    return target


def validate_target(target: str) -> tuple[bool, str, str]:
    """Validate a sanitized target and return (is_valid, target_type, error_msg).

    This is stricter than AutoDetect.detect() — it rejects inputs that
    don't match any known pattern cleanly.
    """
    target = target.strip()

    if not target:
        return False, "unknown", "Target cannot be empty"

    # IP validation
    m = STRICT_IP.match(target)
    if m:
        # Validate each octet is 0-255
        octets = [int(m.group(i)) for i in range(1, 5)]
        if all(0 <= o <= 255 for o in octets):
            return True, "ip", ""
        return False, "ip", f"Invalid IP address: octets must be 0-255"

    # Email validation
    if "@" in target:
        if STRICT_EMAIL.match(target):
            return True, "email", ""
        return False, "email", "Invalid email format"

    # Phone validation: must be mostly digits, allowing common formatting chars
    stripped = target.replace("+", "").replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
    if stripped.isdigit() and 7 <= len(stripped) <= 15:
        return True, "phone", ""

    # Domain validation
    if "." in target and not target.startswith("."):
        if STRICT_DOMAIN.match(target):
            return True, "domain", ""
        return False, "domain", "Invalid domain format"

    # Name validation (fallback)
    if STRICT_NAME.match(target):
        return True, "name", ""

    return False, "unknown", (
        "Target does not match any known format "
        "(domain, IP, email, phone, or name)"
    )


def get_max_length() -> int:
    """Return the maximum allowed target length."""
    return MAX_TARGET_LENGTH
