"""Complaint business logic: NLP analysis, duplicate detection, lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.models.complaint import Complaint
from app.models.enums import COMPLAINT_TRANSITIONS, ComplaintStatus, Role
from app.models.user import User
from app.schemas.complaint import ComplaintIn, ComplaintStatusIn
from app.services.nlp_service import complaint_corpus
from ml.inference.pipeline import get_pipeline


def create_complaint(db: Session, user: User, data: ComplaintIn,
                     ip: str | None = None) -> tuple[Complaint, dict, list[dict]]:
    """Analyze -> dedupe-check -> persist. Returns (complaint, analysis, duplicates)."""
    nlp = get_pipeline()
    analysis = nlp.analyze_complaint(data.text, lat=data.lat, lng=data.lng)

    corpus = complaint_corpus(db, days=30, district=analysis["location"]["district"])
    duplicates = nlp.find_duplicates(
        data.text, corpus,
        category=analysis["category"],
        lat=analysis["location"]["lat"] if analysis["location"]["lat"] is not None else data.lat,
        lng=analysis["location"]["lng"] if analysis["location"]["lng"] is not None else data.lng,
        created_at=datetime.now(timezone.utc),
    )
    top_dup = next((d for d in duplicates if d["is_duplicate"]), None)

    location = analysis["location"]
    complaint = Complaint(
        reporter_id=user.id,
        title=data.title,
        text=data.text,
        category=analysis["category"],
        category_confidence=analysis["category_confidence"],
        classifier_method=analysis["classifier_method"],
        urgency=analysis["urgency"]["label"],
        urgency_score=analysis["urgency"]["score"],
        urgency_reasons=analysis["urgency"]["reasons"],
        language=analysis["language"],
        district=location["district"],
        address=data.address,
        lat=location["lat"] if location["lat"] is not None else data.lat,
        lng=location["lng"] if location["lng"] is not None else data.lng,
        location_source=location["source"],
        embedding=analysis["embedding"],
        duplicate_of_id=top_dup["id"] if top_dup else None,
        duplicate_score=top_dup["score"] if top_dup else None,
    )
    db.add(complaint)
    db.flush()

    audit(db, actor=user, action="complaint.create", entity_type="complaint",
          entity_id=complaint.id,
          detail={"category": complaint.category, "urgency": complaint.urgency,
                  "district": complaint.district,
                  "duplicate_of": complaint.duplicate_of_id}, ip=ip)
    return complaint, analysis, duplicates


def get_complaint_or_404(db: Session, complaint_id: int) -> Complaint:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=404, detail="Complaint not found")
    return complaint


def can_view_complaint(user: User, complaint: Complaint) -> bool:
    if user.role in (Role.MUNICIPAL_ADMIN.value, Role.HEALTH_ADMIN.value,
                     Role.SUPER_ADMIN.value):
        return True
    return complaint.reporter_id == user.id


def transition_status(db: Session, user: User, complaint: Complaint,
                      data: ComplaintStatusIn, ip: str | None = None) -> Complaint:
    allowed = COMPLAINT_TRANSITIONS.get(complaint.status, set())
    if data.status not in allowed:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid transition {complaint.status} -> {data.status}. "
                   f"Allowed: {sorted(allowed) or 'none (terminal state)'}",
        )
    complaint.status = data.status
    if data.status == ComplaintStatus.RESOLVED.value:
        complaint.resolved_at = datetime.now(timezone.utc)
    if data.note is not None:
        complaint.resolution_note = data.note
    audit(db, actor=user, action="complaint.status", entity_type="complaint",
          entity_id=complaint.id,
          detail={"from": complaint.status, "to": data.status, "note": data.note}, ip=ip)
    return complaint


def mark_duplicate(db: Session, user: User, complaint: Complaint,
                   original_id: int, ip: str | None = None) -> Complaint:
    if original_id == complaint.id:
        raise HTTPException(status_code=422, detail="A complaint cannot duplicate itself")
    original = db.get(Complaint, original_id)
    if original is None:
        raise HTTPException(status_code=404, detail="Original complaint not found")
    complaint.duplicate_of_id = original_id
    audit(db, actor=user, action="complaint.mark_duplicate", entity_type="complaint",
          entity_id=complaint.id, detail={"original_id": original_id}, ip=ip)
    return complaint
