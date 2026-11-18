"""Analytics endpoints for dashboards (role-appropriate)."""

from __future__ import annotations

import csv
import io

from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.orm import Session

from app.core.audit import audit, client_ip
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.complaint import Complaint
from app.models.enums import Role
from app.models.report import MedicalReport
from app.models.user import User
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])

_STAFF = (Role.MUNICIPAL_ADMIN, Role.HEALTH_ADMIN, Role.SUPER_ADMIN)


@router.get("/public")
def public_stats(db: Session = Depends(get_db)):
    return analytics_service.public_stats(db)


@router.get("/overview")
def overview(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return analytics_service.overview(db, user)


@router.get("/trends")
def trends(
    days: int = Query(default=14, ge=1, le=180),
    district: str | None = Query(default=None, max_length=60),
    user: User = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
):
    return analytics_service.daily_counts(db, days=days, district=district)


@router.get("/districts")
def districts(
    user: User = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
):
    return {"districts": analytics_service.district_stats(db)}


@router.get("/heatmap")
def heatmap(
    days: int = Query(default=60, ge=1, le=365),
    user: User = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
):
    return analytics_service.heatmap_points(db, days=days)


@router.get("/export")
def export_csv(
    request: Request,
    dataset: str = Query(default="complaints", pattern="^(complaints|reports)$"),
    user: User = Depends(require_roles(Role.HEALTH_ADMIN, Role.SUPER_ADMIN,
                                       Role.MUNICIPAL_ADMIN)),
    db: Session = Depends(get_db),
):
    buffer = io.StringIO()
    writer = csv.writer(buffer)

    if dataset == "complaints":
        writer.writerow(["id", "created_at", "category", "urgency", "status",
                         "district", "lat", "lng", "title", "duplicate_of_id"])
        for c in db.query(Complaint).order_by(Complaint.created_at.desc()).limit(5000):
            writer.writerow([c.id, c.created_at.isoformat(), c.category, c.urgency,
                             c.status, c.district, c.lat, c.lng, c.title,
                             c.duplicate_of_id or ""])
        filename = "healthpulse_complaints.csv"
    else:
        # reports export is de-identified: no patient ids, no raw text
        writer.writerow(["id", "created_at", "district", "urgency", "symptom_categories",
                         "symptom_count"])
        for r in db.query(MedicalReport).order_by(MedicalReport.created_at.desc()).limit(5000):
            writer.writerow([r.id, r.created_at.isoformat(), r.district, r.urgency,
                             "|".join(r.symptom_categories or []),
                             len(r.symptoms or [])])
        filename = "healthpulse_reports_deidentified.csv"

    audit(db, actor=user, action="analytics.export", entity_type="analytics",
          entity_id=dataset, ip=client_ip(request))
    content = buffer.getvalue()
    return Response(
        content=content,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
