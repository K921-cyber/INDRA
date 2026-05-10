from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import FeedItem, ApiStatus, User
from schemas import FeedItemOut, ApiStatusOut
from auth import get_current_active_user


router = APIRouter()


@router.get("/items", response_model=List[FeedItemOut])
def get_feed_items(
    source:   Optional[str] = None,
    severity: Optional[str] = None,
    limit:    int           = 50,
    db:       Session       = Depends(get_db),
    _:        User          = Depends(get_current_active_user),
):
    q = db.query(FeedItem)

    if source:
        q = q.filter(FeedItem.source == source)

    if severity:
        q = q.filter(FeedItem.severity == severity)

    return (
        q.order_by(FeedItem.fetched_at.desc())
        .limit(min(limit, 200))
        .all()
    )


@router.post("/items/{item_id}/read", status_code=204)
def mark_read(
    item_id: int,
    db:      Session = Depends(get_db),
    _:       User    = Depends(get_current_active_user),
):
    item = db.query(FeedItem).filter(FeedItem.id == item_id).first()
    if item:
        item.is_read = True  # type: ignore[assignment]
        db.commit()


@router.post("/refresh")
async def trigger_refresh(
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_active_user),
):
    try:
        from scheduler import fetch_certin_feed, fetch_boomlive_feed
        background_tasks.add_task(fetch_certin_feed)
        background_tasks.add_task(fetch_boomlive_feed)
        return {"message": "Feed refresh triggered — check back in 30 seconds"}
    except ImportError:
        return {"message": "Scheduler not available yet"}


@router.get("/api-status", response_model=List[ApiStatusOut])
def get_api_status(
    db: Session = Depends(get_db),
    _:  User    = Depends(get_current_active_user),
):
    return (
        db.query(ApiStatus)
        .order_by(ApiStatus.api_name)
        .all()
    )


@router.post("/api-status/ping")
async def trigger_health_ping(
    background_tasks: BackgroundTasks,
    _: User = Depends(get_current_active_user),
):
    try:
        from scheduler import ping_apis
        background_tasks.add_task(ping_apis)
        return {"message": "Health ping triggered — check api-status in 15 seconds"}
    except ImportError:
        return {"message": "Scheduler not available yet"}