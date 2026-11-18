"""Cross-domain intelligence endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field


class PreviewIn(BaseModel):
    text: str = Field(min_length=10, max_length=6000)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)

from app.core.audit import client_ip
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.complaint import Complaint
from app.models.enums import Role
from app.models.report import MedicalReport
from app.models.user import User
from app.schemas.alert import ScanIn
from app.services import complaint_service, intelligence_service, nlp_service, report_service

router = APIRouter(prefix="/intelligence", tags=["intelligence"])

_STAFF = (Role.HEALTH_ADMIN, Role.SUPER_ADMIN)
_OPS = (Role.MUNICIPAL_ADMIN, Role.HEALTH_ADMIN, Role.SUPER_ADMIN)


@router.post("/preview")
def analysis_preview(
    data: PreviewIn,
    user: User = Depends(require_roles(Role.CITIZEN, Role.PATIENT, Role.CLINICIAN,
                                       Role.MUNICIPAL_ADMIN, Role.HEALTH_ADMIN,
                                       Role.SUPER_ADMIN)),
):
    """Live NLP analysis preview without persisting anything (used by the
    complaint form's 'as you type' panel)."""
    from ml.inference.pipeline import get_pipeline

    return get_pipeline().analyze_complaint(data.text, lat=data.lat, lng=data.lng)


@router.post("/preview-report")
def report_preview(
    data: PreviewIn,
    user: User = Depends(require_roles(Role.PATIENT, Role.CLINICIAN,
                                       Role.HEALTH_ADMIN, Role.SUPER_ADMIN)),
):
    """Live symptom-extraction preview for the report form (not persisted)."""
    from ml.inference.pipeline import get_pipeline

    return get_pipeline().analyze_symptom_report(data.text, lat=data.lat, lng=data.lng)


@router.post("/scan")
def run_scan(
    data: ScanIn,
    request: Request,
    user: User = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
):
    return intelligence_service.run_scan(db, user, days=data.days, ip=client_ip(request))


@router.get("/status")
def intelligence_status(
    user: User = Depends(require_roles(*_OPS)),
    db: Session = Depends(get_db),
):
    from app.models.alert import Alert
    from app.models.enums import AlertStatus

    open_alerts = db.query(Alert).filter(
        Alert.status.in_([AlertStatus.NEW.value, AlertStatus.REVIEWING.value])).count()
    total_alerts = db.query(Alert).count()
    latest = (db.query(Alert).order_by(Alert.created_at.desc()).first())
    return {
        "engine": nlp_service.pipeline_health(),
        "open_alerts": open_alerts,
        "total_alerts": total_alerts,
        "latest_alert": {
            "id": latest.id, "type": latest.type, "title": latest.title,
            "score": latest.score, "created_at": latest.created_at,
        } if latest else None,
        "disclaimer": nlp_service.DISCLAIMER,
    }


@router.get("/related/complaint/{complaint_id}")
def related_for_complaint(
    complaint_id: int,
    user: User = Depends(require_roles(*_OPS)),
    db: Session = Depends(get_db),
):
    complaint = complaint_service.get_complaint_or_404(db, complaint_id)
    return intelligence_service.related_for_complaint(db, complaint)


@router.get("/related/report/{report_id}")
def related_for_report(
    report_id: int,
    user: User = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
):
    report = report_service.get_report_or_404(db, report_id)
    return intelligence_service.related_for_report(db, report)
