"""
TRINETRA — Pydantic Schemas

Request and response models used across the REST API
and WebSocket endpoints.
"""

from typing import Optional
from pydantic import BaseModel
from datetime import datetime


# ==================== Search Types ====================


class SearchRequest(BaseModel):
    target: str
    type: Optional[str] = None  # auto-detect if not provided


# ==================== Plugin Results ====================


class PluginResultData(BaseModel):
    plugin_id: str
    plugin_name: str
    category: str
    target: str
    status: str  # running, completed, failed
    freshness: str  # moments, minutes, hours, days, weeks
    timestamp: datetime
    gui_data: dict
    terminal_data: str
    error: Optional[str] = None
    credit_cost: int = 1


class SearchResponse(BaseModel):
    target: str
    type: str
    timestamp: datetime
    total_plugins: int
    completed_plugins: int
    results: list[PluginResultData]
    credits_used: Optional[int] = None
    credits_refunded: Optional[int] = None
    credits_remaining: Optional[int] = None
