"""Medical report endpoints (patients + clinical staff)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import client_ip
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.enums import Role
from app.models.report import MedicalReport
from app.models.user import User
from app.schemas.common import Page
from app.schemas.report import ReportFromDocumentIn, ReportIn, ReportOut
from app.services import document_service, report_service
from app.utils.pagination import pagination_params

router = APIRouter(prefix="/reports", tags=["reports"])

_HEALTH_STAFF = (Role.CLINICIAN, Role.HEALTH_ADMIN, Role.SUPER_ADMIN)


@router.post("", response_model=ReportOut, status_code=201)
def create_report(
    data: ReportIn,
    request: Request,
    user: User = Depends(require_roles(Role.PATIENT, Role.CLINICIAN, Role.SUPER_ADMIN,
                                       Role.HEALTH_ADMIN)),
    db: Session = Depends(get_db),
):
    report = report_service.create_report(db, user, data, ip=client_ip(request))
    out = ReportOut.model_validate(report)
    out.patient_alias = report_service.patient_alias(report)
    return out


@router.get("", response_model=Page[ReportOut])
def list_reports(
    urgency: str | None = Query(default=None),
    district: str | None = Query(default=None),
    symptom: str | None = Query(default=None, max_length=60),
    page_page: tuple[int, int] = Depends(pagination_params),
    user: User = Depends(require_roles(Role.PATIENT, Role.CLINICIAN, Role.HEALTH_ADMIN,
                                       Role.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    page, page_size = page_page
    query = db.query(MedicalReport)
    # privacy: patients see only their own reports
    if user.role == Role.PATIENT.value:
        query = query.filter(MedicalReport.patient_id == user.id)
    if urgency:
        query = query.filter(MedicalReport.urgency == urgency)
    if district:
        query = query.filter(MedicalReport.district == district)
    if symptom:
        # JSON list containment (SQLite + Postgres compatible via LIKE fallback)
        like = f'%"{symptom.lower()}"%'
        query = query.filter(MedicalReport.symptoms.cast("VARCHAR").ilike(like))
    total = query.count()
    rows = (query.order_by(MedicalReport.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    items = []
    for r in rows:
        item = ReportOut.model_validate(r)
        item.patient_alias = report_service.patient_alias(r)
        # privacy: identity is only visible to the owning patient
        if r.patient_id != user.id:
            item.patient_id = None
        items.append(item)
    return Page.build(items, total, page, page_size)


@router.get("/{report_id}", response_model=ReportOut)
def get_report(
    report_id: int,
    user: User = Depends(require_roles(Role.PATIENT, Role.CLINICIAN, Role.HEALTH_ADMIN,
                                       Role.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    report = report_service.get_report_or_404(db, report_id)
    if not report_service.can_view_report(user, report):
        raise HTTPException(status_code=403, detail="You do not have access to this report")
    out = ReportOut.model_validate(report)
    out.patient_alias = report_service.patient_alias(report)
    if report.patient_id != user.id:
        out.patient_id = None
    return out


@router.post("/{report_id}/summarize", response_model=ReportOut)
def summarize_report(
    report_id: int,
    request: Request,
    user: User = Depends(require_roles(*_HEALTH_STAFF, Role.PATIENT)),
    db: Session = Depends(get_db),
):
    report = report_service.get_report_or_404(db, report_id)
    if not report_service.can_view_report(user, report):
        raise HTTPException(status_code=403, detail="You do not have access to this report")
    report = report_service.summarize_report(db, user, report, ip=client_ip(request))
    out = ReportOut.model_validate(report)
    out.patient_alias = report_service.patient_alias(report)
    return out


@router.post("/from-document", response_model=ReportOut, status_code=201)
def create_from_document(
    data: ReportFromDocumentIn,
    request: Request,
    user: User = Depends(require_roles(Role.PATIENT, Role.CLINICIAN, Role.SUPER_ADMIN,
                                       Role.HEALTH_ADMIN)),
    db: Session = Depends(get_db),
):
    document = document_service.get_document_or_404(db, data.document_id)
    if not document_service.can_view_document(user, document):
        raise HTTPException(status_code=403, detail="You do not have access to this document")
    report = report_service.create_from_document(db, user, document, ip=client_ip(request))
    out = ReportOut.model_validate(report)
    out.patient_alias = report_service.patient_alias(report)
    return out
