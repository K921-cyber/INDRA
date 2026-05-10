from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from models import Case, QueryLog, User
from schemas import CaseCreate, CaseUpdate, CaseOut
from auth import get_current_active_user


router = APIRouter()


@router.post("", response_model=CaseOut, status_code=status.HTTP_201_CREATED)
def create_case(
    case_in:      CaseCreate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_active_user),
):
    case = Case(
        title       = case_in.title,
        description = case_in.description,
        target      = case_in.target,
        priority    = case_in.priority,
        tags        = case_in.tags,
        notes       = case_in.notes,
        owner_id    = current_user.id,
        status      = "open",
    )
    db.add(case)
    db.commit()
    db.refresh(case)

    out             = CaseOut.model_validate(case)
    out.query_count = 0
    return out


@router.get("", response_model=List[CaseOut])
def list_cases(
    status_filter: Optional[str] = None,
    db:            Session        = Depends(get_db),
    current_user:  User           = Depends(get_current_active_user),
):
    q = db.query(Case).filter(Case.owner_id == current_user.id)

    if status_filter:
        q = q.filter(Case.status == status_filter)

    cases = q.order_by(Case.created_at.desc()).all()

    results = []
    for c in cases:
        count = (
            db.query(QueryLog)
            .filter(QueryLog.case_id == c.id)
            .count()
        )
        out             = CaseOut.model_validate(c)
        out.query_count = count
        results.append(out)

    return results


@router.get("/{case_id}", response_model=CaseOut)
def get_case(
    case_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_active_user),
):
    case = (
        db.query(Case)
        .filter(
            Case.id       == case_id,
            Case.owner_id == current_user.id,
        )
        .first()
    )
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    count           = db.query(QueryLog).filter(QueryLog.case_id == case_id).count()
    out             = CaseOut.model_validate(case)
    out.query_count = count
    return out


@router.patch("/{case_id}", response_model=CaseOut)
def update_case(
    case_id:      int,
    updates:      CaseUpdate,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_active_user),
):
    case = (
        db.query(Case)
        .filter(
            Case.id       == case_id,
            Case.owner_id == current_user.id,
        )
        .first()
    )
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    update_data = updates.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(case, field, value)

    db.commit()
    db.refresh(case)

    count           = db.query(QueryLog).filter(QueryLog.case_id == case_id).count()
    out             = CaseOut.model_validate(case)
    out.query_count = count
    return out


@router.delete("/{case_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_case(
    case_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_active_user),
):
    case = (
        db.query(Case)
        .filter(
            Case.id       == case_id,
            Case.owner_id == current_user.id,
        )
        .first()
    )
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    db.delete(case)
    db.commit()


@router.get("/{case_id}/queries")
def get_case_queries(
    case_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_active_user),
):
    case = (
        db.query(Case)
        .filter(
            Case.id       == case_id,
            Case.owner_id == current_user.id,
        )
        .first()
    )
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Case not found",
        )

    logs = (
        db.query(QueryLog)
        .filter(QueryLog.case_id == case_id)
        .order_by(QueryLog.queried_at.desc())
        .all()
    )

    return [
        {
            "id":         log.id,
            "type":       log.query_type,
            "input":      log.query_input,
            "source":     log.source_used,
            "success":    log.success,
            "ms":         log.response_ms,
            "queried_at": log.queried_at,
        }
        for log in logs
    ]