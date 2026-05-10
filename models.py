from sqlalchemy import (
    Column, Integer, String, Text,
    Boolean, DateTime, ForeignKey, Float
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class User(Base):
    __tablename__ = "users"

    id               = Column(Integer, primary_key=True, index=True)
    username         = Column(String(50), unique=True, index=True, nullable=False)
    email            = Column(String(120), unique=True, index=True, nullable=False)
    hashed_password  = Column(String(256), nullable=False)
    full_name        = Column(String(100), nullable=True)
    role             = Column(String(20), default="student")
    is_active        = Column(Boolean, default=True)
    created_at       = Column(DateTime(timezone=True), server_default=func.now())
    last_login       = Column(DateTime(timezone=True), nullable=True)

    cases       = relationship("Case", back_populates="owner")
    query_logs  = relationship("QueryLog", back_populates="user")


class Case(Base):
    __tablename__ = "cases"

    id          = Column(Integer, primary_key=True, index=True)
    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    target      = Column(String(200), nullable=True)
    status      = Column(String(20), default="open")
    priority    = Column(String(10), default="medium")
    tags        = Column(String(500), nullable=True)
    notes       = Column(Text, nullable=True)
    owner_id    = Column(Integer, ForeignKey("users.id"))
    created_at  = Column(DateTime(timezone=True), server_default=func.now())
    updated_at  = Column(DateTime(timezone=True), onupdate=func.now())

    owner      = relationship("User", back_populates="cases")
    query_logs = relationship("QueryLog", back_populates="case")


class QueryLog(Base):
    __tablename__ = "query_logs"

    id          = Column(Integer, primary_key=True, index=True)
    query_type  = Column(String(30), nullable=False)
    query_input = Column(String(500), nullable=False)
    result_json = Column(Text, nullable=True)
    source_used = Column(String(100), nullable=True)
    is_fallback = Column(Boolean, default=False)
    response_ms = Column(Integer, nullable=True)
    success     = Column(Boolean, default=True)
    error_msg   = Column(String(500), nullable=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=True)
    case_id     = Column(Integer, ForeignKey("cases.id"), nullable=True)
    queried_at  = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="query_logs")
    case = relationship("Case", back_populates="query_logs")


class FeedItem(Base):
    __tablename__ = "feed_items"

    id           = Column(Integer, primary_key=True, index=True)
    source       = Column(String(50), nullable=False)
    title        = Column(String(500), nullable=False)
    summary      = Column(Text, nullable=True)
    url          = Column(String(1000), nullable=True)
    severity     = Column(String(10), default="medium")
    category     = Column(String(50), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at   = Column(DateTime(timezone=True), server_default=func.now())
    is_read      = Column(Boolean, default=False)


class ApiStatus(Base):
    __tablename__ = "api_status"

    id               = Column(Integer, primary_key=True, index=True)
    api_name         = Column(String(100), unique=True, nullable=False)
    base_url         = Column(String(500), nullable=True)
    is_healthy       = Column(Boolean, default=True)
    last_response_ms = Column(Integer, nullable=True)
    last_checked     = Column(DateTime(timezone=True), nullable=True)
    requires_key     = Column(Boolean, default=False)
    key_configured   = Column(Boolean, default=False)
    license_type     = Column(String(100), nullable=True)
    notes            = Column(Text, nullable=True)