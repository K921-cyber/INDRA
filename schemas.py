from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List, Any
from datetime import datetime


# ── AUTH ──────────────────────────────────────────────────────────────────

class UserCreate(BaseModel):
    username:  str
    email:     EmailStr
    password:  str
    full_name: Optional[str] = None

    @field_validator("username")
    @classmethod
    def username_alphanumeric(cls, v):
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError(
                "Username must be alphanumeric "
                "(underscores and hyphens allowed)"
            )
        if len(v) < 3 or len(v) > 50:
            raise ValueError("Username must be 3–50 characters")
        return v.lower()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserOut(BaseModel):
    id:         int
    username:   str
    email:      str
    full_name:  Optional[str]
    role:       str
    is_active:  bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type:   str
    user:         UserOut


class TokenData(BaseModel):
    username: Optional[str] = None


# ── CASES ─────────────────────────────────────────────────────────────────

class CaseCreate(BaseModel):
    title:       str
    description: Optional[str] = None
    target:      Optional[str] = None
    priority:    str            = "medium"
    tags:        Optional[str]  = None
    notes:       Optional[str]  = None

    @field_validator("priority")
    @classmethod
    def valid_priority(cls, v):
        if v not in ("low", "medium", "high"):
            raise ValueError("Priority must be low, medium, or high")
        return v


class CaseUpdate(BaseModel):
    title:       Optional[str] = None
    description: Optional[str] = None
    target:      Optional[str] = None
    status:      Optional[str] = None
    priority:    Optional[str] = None
    tags:        Optional[str] = None
    notes:       Optional[str] = None


class CaseOut(BaseModel):
    id:          int
    title:       str
    description: Optional[str]
    target:      Optional[str]
    status:      str
    priority:    str
    tags:        Optional[str]
    notes:       Optional[str]
    owner_id:    int
    created_at:  datetime
    updated_at:  Optional[datetime]
    query_count: Optional[int] = 0

    class Config:
        from_attributes = True


# ── QUERIES ───────────────────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query_type:  str
    query_input: str
    case_id:     Optional[int] = None

    @field_validator("query_type")
    @classmethod
    def valid_type(cls, v):
        allowed = {"ip", "whois", "company", "threat", "news", "geo"}
        if v not in allowed:
            raise ValueError(
                f"query_type must be one of: {', '.join(sorted(allowed))}"
            )
        return v

    @field_validator("query_input")
    @classmethod
    def input_not_empty(cls, v):
        if not v.strip():
            raise ValueError("query_input cannot be empty")
        if len(v) > 500:
            raise ValueError("query_input too long (max 500 characters)")
        return v.strip()


class QueryResult(BaseModel):
    query_type:  str
    query_input: str
    success:     bool
    source:      str
    is_fallback: bool
    data:        Any
    response_ms: int
    legal_note:  str
    error:       Optional[str] = None


class QueryLogOut(BaseModel):
    id:          int
    query_type:  str
    query_input: str
    source_used: Optional[str]
    is_fallback: bool
    response_ms: Optional[int]
    success:     bool
    queried_at:  datetime

    class Config:
        from_attributes = True


# ── FEEDS ─────────────────────────────────────────────────────────────────

class FeedItemOut(BaseModel):
    id:           int
    source:       str
    title:        str
    summary:      Optional[str]
    url:          Optional[str]
    severity:     str
    category:     Optional[str]
    published_at: Optional[datetime]
    fetched_at:   datetime
    is_read:      bool

    class Config:
        from_attributes = True


class ApiStatusOut(BaseModel):
    api_name:         str
    base_url:         Optional[str]
    is_healthy:       bool
    last_response_ms: Optional[int]
    last_checked:     Optional[datetime]
    requires_key:     bool
    key_configured:   bool
    license_type:     Optional[str]

    class Config:
        from_attributes = True