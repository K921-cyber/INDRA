"""
TRINETRA — Watch & Alert API Routes

CRUD endpoints for managing watched targets and viewing alerts.
"""

import json
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional

from app.core.detector import AutoDetect
from app.core.sanitizer import sanitize_target, InputValidationError
from app.core.api_key_auth import require_api_key
from app.services import watch_service

router = APIRouter(prefix="/api/watches", tags=["watches"])


# ── Request / Response Schemas ───────────────────────────────


class WatchCreateRequest(BaseModel):
    target: str
    target_type: Optional[str] = None  # auto-detect if omitted
    plugin_ids: Optional[list[str]] = None
    interval_seconds: int = 3600  # default: 1 hour
    webhook_url: Optional[str] = None
    email: Optional[str] = None


class AlertResponse(BaseModel):
    id: int
    watch_id: int
    target: str
    plugin_id: str
    old_data: dict
    new_data: dict
    summary: str
    created_at: str


class WatchResponse(BaseModel):
    id: int
    target: str
    target_type: str
    plugin_ids: list[str]
    interval_seconds: int
    webhook_url: Optional[str]
    email: Optional[str]
    is_active: bool
    last_checked_at: Optional[str]
    created_at: str


# ── Endpoints ────────────────────────────────────────────────


@router.post("", response_model=WatchResponse)
async def create_watch(req: WatchCreateRequest, _key: str = Depends(require_api_key)):
    """Create a new watch for a target.

    The target will be periodically re-scanned at the configured
    interval. Any differences from the previous scan will trigger
    an alert.
    """
    # Sanitize input
    try:
        target = sanitize_target(req.target)
    except InputValidationError as e:
        raise HTTPException(400, detail={"error": e.message, "detail": e.detail})

    target_type = req.target_type or AutoDetect.detect(target)
    if target_type == "unknown":
        raise HTTPException(400, "Could not auto-detect target type. Please specify it.")

    # Validate interval bounds
    if req.interval_seconds < 60:
        raise HTTPException(400, "Minimum watch interval is 60 seconds")
    if req.interval_seconds > 604800:  # 7 days
        raise HTTPException(400, "Maximum watch interval is 7 days")

    watch = await watch_service.create_watch(
        target=target,
        target_type=target_type,
        plugin_ids=req.plugin_ids,
        interval_seconds=req.interval_seconds,
        webhook_url=req.webhook_url,
        email=req.email,
    )
    return _format_watch(watch)


@router.get("", response_model=list[WatchResponse])
async def list_watches(_key: str = Depends(require_api_key)):
    """List all watches."""
    watches = await watch_service.list_watches()
    return [_format_watch(w) for w in watches]


# ── Alerts (defined BEFORE /{watch_id} to avoid route collision) ──


@router.get("/alerts", response_model=list[AlertResponse])
async def list_alerts(limit: int = 50, _key: str = Depends(require_api_key)):
    """List the most recent alerts across all watches."""
    alerts = await watch_service.list_alerts(limit)
    return [_format_alert(a) for a in alerts]


@router.get("/{watch_id}", response_model=WatchResponse)
async def get_watch(watch_id: int, _key: str = Depends(require_api_key)):
    """Get details for a specific watch."""
    watch = await watch_service.get_watch(watch_id)
    if not watch:
        raise HTTPException(404, "Watch not found")
    return _format_watch(watch)


@router.delete("/{watch_id}")
async def delete_watch(watch_id: int, _key: str = Depends(require_api_key)):
    """Delete a watch."""
    deleted = await watch_service.delete_watch(watch_id)
    if not deleted:
        raise HTTPException(404, "Watch not found")
    return {"status": "deleted", "watch_id": watch_id}


@router.post("/{watch_id}/toggle", response_model=dict)
async def toggle_watch(watch_id: int, _key: str = Depends(require_api_key)):
    """Toggle a watch on/off."""
    result = await watch_service.toggle_watch(watch_id)
    if not result:
        raise HTTPException(404, "Watch not found")
    return {"status": "toggled", "watch_id": watch_id, "is_active": result["is_active"]}


@router.get("/{watch_id}/alerts", response_model=list[AlertResponse])
async def list_alerts_for_watch(watch_id: int, _key: str = Depends(require_api_key)):
    """List alerts for a specific watch."""
    watch = await watch_service.get_watch(watch_id)
    if not watch:
        raise HTTPException(404, "Watch not found")
    alerts = await watch_service.list_alerts_for_watch(watch_id)
    return [_format_alert(a) for a in alerts]


# ── Helpers ──────────────────────────────────────────────────


def _format_watch(w: dict) -> dict:
    return {
        "id": w["id"],
        "target": w["target"],
        "target_type": w["target_type"],
        "plugin_ids": w.get("plugin_ids") or [],
        "interval_seconds": w["interval_seconds"],
        "webhook_url": w.get("webhook_url") or None,
        "email": w.get("email") or None,
        "is_active": bool(w.get("is_active", True)),
        "last_checked_at": _fmt_dt(w.get("last_checked_at")),
        "created_at": _fmt_dt(w["created_at"]),
    }


def _format_alert(a: dict) -> dict:
    # SQLite stores JSON as TEXT; PG stores as JSONB dict
    old_data = a.get("old_data")
    new_data = a.get("new_data")
    return {
        "id": a["id"],
        "watch_id": a["watch_id"],
        "target": a["target"],
        "plugin_id": a["plugin_id"],
        "old_data": _parse_json_field(old_data),
        "new_data": _parse_json_field(new_data),
        "summary": a["summary"],
        "created_at": _fmt_dt(a.get("created_at")),
    }


def _fmt_dt(val) -> str | None:
    """Convert a datetime (PG) or string (SQLite) to ISO string or None."""
    if val is None:
        return None
    if isinstance(val, str):
        return val
    # datetime object — convert to ISO string
    return val.isoformat()


def _parse_json_field(val) -> dict:
    """Parse a value that may be a dict (PG) or a JSON string (SQLite) into a dict."""
    if isinstance(val, dict):
        return val
    if isinstance(val, str):
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return {}
    return {}
