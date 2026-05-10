import json
import time

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import QueryLog, User
from schemas import QueryRequest, QueryResult
from auth import get_current_active_user

from services.ip_service      import lookup_ip
from services.whois_service   import lookup_whois
from services.geo_service     import lookup_geo
from services.threat_service  import lookup_threat
from services.company_service import lookup_company
from services.news_service    import lookup_news


router = APIRouter()

SERVICE_MAP = {
    "ip":      lookup_ip,
    "whois":   lookup_whois,
    "geo":     lookup_geo,
    "threat":  lookup_threat,
    "company": lookup_company,
    "news":    lookup_news,
}


@router.post("", response_model=QueryResult)
async def run_query(
    req:          QueryRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_active_user),
):
    service_fn = SERVICE_MAP.get(req.query_type)
    if not service_fn:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown query type: {req.query_type}"
        )

    # ── Call the service ──────────────────────────────────────────
    start = time.monotonic()
    try:
        result_data = await service_fn(req.query_input)
        success     = "error" not in result_data
    except Exception as e:
        result_data = {"error": str(e)}
        success     = False
    total_ms = int((time.monotonic() - start) * 1000)

    # ── Strip internal metadata ───────────────────────────────────
    source      = result_data.pop("_source",   "unknown")
    is_fallback = result_data.pop("_fallback", False)
    legal_note  = result_data.pop("_legal",    "See API Registry.")
    result_data.pop("_ms", None)

    # ── Log to database ───────────────────────────────────────────
    log = QueryLog(
        query_type  = req.query_type,
        query_input = req.query_input,
        result_json = json.dumps(result_data)[:4000],
        source_used = source,
        is_fallback = is_fallback,
        response_ms = total_ms,
        success     = success,
        error_msg   = (result_data.get("error") if not success else None),
        user_id     = current_user.id,
        case_id     = req.case_id,
    )
    db.add(log)
    db.commit()

    # ── Return structured response ────────────────────────────────
    return QueryResult(
        query_type  = req.query_type,
        query_input = req.query_input,
        success     = success,
        source      = source,
        is_fallback = is_fallback, 
        data        = result_data,
        response_ms = total_ms,
        legal_note  = legal_note,
        error       = (result_data.get("error") if not success else None),
    )


@router.get("/history")
def get_history(
    limit: int     = 50,
    db:    Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    limit = min(limit, 200)

    logs = (
        db.query(QueryLog)
        .filter(QueryLog.user_id == current_user.id)
        .order_by(QueryLog.queried_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id":         log.id,
            "type":       log.query_type,
            "input":      log.query_input,
            "source":     log.source_used,
            "fallback":   log.is_fallback,
            "ms":         log.response_ms,
            "success":    log.success,
            "case_id":    log.case_id,
            "queried_at": log.queried_at,
        }
        for log in logs
    ]