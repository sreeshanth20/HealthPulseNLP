"""Complaint endpoints (citizens + civic staff)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import client_ip
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.complaint import Complaint
from app.models.enums import Role
from app.models.user import User
from app.schemas.complaint import (ComplaintIn, ComplaintOut, ComplaintStatusIn,
                                   MarkDuplicateIn)
from app.schemas.common import Page
from app.services import complaint_service, nlp_service
from app.utils.pagination import pagination_params
from ml.inference.pipeline import get_pipeline

router = APIRouter(prefix="/complaints", tags=["complaints"])

_STAFF_ROLES = (Role.MUNICIPAL_ADMIN, Role.HEALTH_ADMIN, Role.SUPER_ADMIN)


@router.post("", response_model=dict, status_code=201)
def create_complaint(
    data: ComplaintIn,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaint, analysis, duplicates = complaint_service.create_complaint(
        db, user, data, ip=client_ip(request))
    return {
        "complaint": ComplaintOut.model_validate(complaint),
        "analysis": analysis,
        "duplicate_candidates": duplicates[:5],
        "duplicate_detected": any(d["is_duplicate"] for d in duplicates),
    }


@router.get("", response_model=Page[ComplaintOut])
def list_complaints(
    status: str | None = Query(default=None),
    category: str | None = Query(default=None),
    district: str | None = Query(default=None),
    urgency: str | None = Query(default=None),
    q: str | None = Query(default=None, max_length=100),
    page_page: tuple[int, int] = Depends(pagination_params),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    page, page_size = page_page
    query = db.query(Complaint)
    # role scoping: citizens/patients see only their own complaints
    if user.role not in tuple(r.value for r in _STAFF_ROLES):
        query = query.filter(Complaint.reporter_id == user.id)
    if status:
        query = query.filter(Complaint.status == status)
    if category:
        query = query.filter(Complaint.category == category)
    if district:
        query = query.filter(Complaint.district == district)
    if urgency:
        query = query.filter(Complaint.urgency == urgency)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(or_(Complaint.title.ilike(like), Complaint.text.ilike(like)))
    total = query.count()
    rows = (query.order_by(Complaint.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return Page.build([ComplaintOut.model_validate(c) for c in rows], total, page, page_size)


@router.get("/geo")
def complaint_geo(
    days: int = Query(default=60, ge=1, le=365),
    user: User = Depends(require_roles(*_STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(days=days)
    rows = db.query(Complaint).filter(
        Complaint.created_at >= since, Complaint.lat.isnot(None)).limit(600).all()
    return {
        "points": [
            {"id": c.id, "lat": c.lat, "lng": c.lng, "category": c.category,
             "urgency": c.urgency, "status": c.status, "district": c.district}
            for c in rows
        ]
    }


@router.get("/{complaint_id}", response_model=ComplaintOut)
def get_complaint(
    complaint_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    if not complaint_service.can_view_complaint(user, complaint):
        raise HTTPException(status_code=403, detail="You do not have access to this complaint")
    return ComplaintOut.model_validate(complaint)


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
def update_status(
    complaint_id: int,
    data: ComplaintStatusIn,
    request: Request,
    user: User = Depends(require_roles(*_STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    complaint = complaint_service.transition_status(db, user, complaint, data,
                                                    ip=client_ip(request))
    return ComplaintOut.model_validate(complaint)


@router.post("/{complaint_id}/mark-duplicate", response_model=ComplaintOut)
def mark_duplicate(
    complaint_id: int,
    data: MarkDuplicateIn,
    request: Request,
    user: User = Depends(require_roles(*_STAFF_ROLES)),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    complaint = complaint_service.mark_duplicate(db, user, complaint, data.original_id,
                                                 ip=client_ip(request))
    return ComplaintOut.model_validate(complaint)


@router.get("/{complaint_id}/similar")
def similar_complaints(
    complaint_id: int,
    limit: int = Query(default=5, ge=1, le=20),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    if not complaint_service.can_view_complaint(user, complaint):
        raise HTTPException(status_code=403, detail="You do not have access to this complaint")
    corpus = nlp_service.complaint_corpus(db, days=90, exclude_id=complaint.id)
    matches = get_pipeline().related_items(complaint.text, corpus, k=limit)
    return {"complaint_id": complaint.id, "similar": matches}
