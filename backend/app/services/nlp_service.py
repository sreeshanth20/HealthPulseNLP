"""NLP service: thin wrapper over ml.inference.pipeline for DB-integrated ops."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from ml.inference.pipeline import get_pipeline
from ml.config import DISCLAIMER

from app.models.complaint import Complaint
from app.models.report import MedicalReport


def pipeline_health() -> dict:
    return get_pipeline().health()


def complaint_corpus(db: Session, days: int = 30, limit: int = 400,
                     exclude_id: int | None = None,
                     district: str | None = None) -> list[dict]:
    """Recent complaints as duplicate/search corpus rows."""
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = db.query(Complaint).filter(Complaint.created_at >= since)
    if district:
        q = q.filter(Complaint.district == district)
    if exclude_id is not None:
        q = q.filter(Complaint.id != exclude_id)
    rows = q.order_by(Complaint.created_at.desc()).limit(limit).all()
    return [
        {
            "id": c.id, "title": c.title, "text": c.text, "category": c.category,
            "district": c.district, "lat": c.lat, "lng": c.lng,
            "created_at": c.created_at, "embedding": c.embedding,
            "status": c.status,
        }
        for c in rows
    ]


def report_corpus(db: Session, days: int = 60, limit: int = 400,
                  exclude_id: int | None = None) -> list[dict]:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    q = db.query(MedicalReport).filter(MedicalReport.created_at >= since)
    if exclude_id is not None:
        q = q.filter(MedicalReport.id != exclude_id)
    rows = q.order_by(MedicalReport.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "text": r.text, "symptoms": r.symptoms or [],
            "symptom_categories": r.symptom_categories or [],
            "urgency": r.urgency, "district": r.district,
            "lat": r.lat, "lng": r.lng, "created_at": r.created_at,
            "embedding": r.embedding,
        }
        for r in rows
    ]


def engine_complaint_rows(db: Session, since: datetime) -> list[dict]:
    rows = db.query(Complaint).filter(Complaint.created_at >= since).all()
    return [
        {
            "id": c.id, "text": c.text, "category": c.category, "district": c.district,
            "lat": c.lat, "lng": c.lng, "created_at": c.created_at,
            "embedding": c.embedding, "urgency": c.urgency,
        }
        for c in rows
    ]


def engine_report_rows(db: Session, since: datetime) -> list[dict]:
    rows = db.query(MedicalReport).filter(MedicalReport.created_at >= since).all()
    return [
        {
            "id": r.id, "text": r.text, "symptoms": r.symptoms or [],
            "symptom_categories": r.symptom_categories or [],
            "district": r.district, "lat": r.lat, "lng": r.lng,
            "created_at": r.created_at, "embedding": r.embedding,
            "urgency": r.urgency,
        }
        for r in rows
    ]


def daily_series(db: Session, since: datetime) -> list[dict]:
    """Daily complaint counts grouped by district (for anomaly detection)."""
    rows = (
        db.query(
            Complaint.district,
            func.date(Complaint.created_at).label("day"),
            func.count(Complaint.id).label("n"),
        )
        .filter(Complaint.created_at >= since)
        .group_by(Complaint.district, "day")
        .all()
    )
    series: dict[str, list[tuple[str, int]]] = {}
    for district, day, count in rows:
        key = district or "Unknown"
        series.setdefault(key, []).append((str(day), int(count)))
    return [{"key": k, "points": points} for k, points in series.items()]


def scan_window(days: int) -> datetime:
    return datetime.now(timezone.utc) - timedelta(days=days)


__all__ = ["DISCLAIMER", "complaint_corpus", "daily_series", "engine_complaint_rows",
           "engine_report_rows", "pipeline_health", "report_corpus", "scan_window"]
