"""Alert + investigation endpoints (public health staff)."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from app.core.audit import audit, client_ip
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.alert import Alert
from app.models.enums import (AlertStatus, InvestigationStatus, Role)
from app.models.investigation import Investigation
from app.models.user import User
from app.schemas.alert import AlertOut, AlertStatusIn, InvestigationOut, InvestigationUpdateIn
from app.schemas.common import Page
from app.utils.pagination import pagination_params

router = APIRouter(tags=["alerts"])

_STAFF = (Role.HEALTH_ADMIN, Role.SUPER_ADMIN)
_OPS = (Role.MUNICIPAL_ADMIN, Role.HEALTH_ADMIN, Role.SUPER_ADMIN)


@router.get("/alerts", response_model=Page[AlertOut])
def list_alerts(
    type: str | None = Query(default=None),
    status: str | None = Query(default=None),
    district: str | None = Query(default=None),
    min_score: float | None = Query(default=None, ge=0, le=1),
    page_page: tuple[int, int] = Depends(pagination_params),
    user: User = Depends(require_roles(*_OPS)),
    db: Session = Depends(get_db),
):
    page, page_size = page_page
    query = db.query(Alert)
    if type:
        query = query.filter(Alert.type == type)
    if status:
        query = query.filter(Alert.status == status)
    if district:
        # JSON list containment via cast (works on SQLite and Postgres)
        like = f'%"{district}"%'
        query = query.filter(Alert.districts.cast("VARCHAR").ilike(like))
    if min_score is not None:
        query = query.filter(Alert.score >= min_score)
    total = query.count()
    rows = (query.order_by(Alert.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return Page.build([AlertOut.model_validate(a) for a in rows], total, page, page_size)


@router.get("/alerts/{alert_id}", response_model=AlertOut)
def get_alert(
    alert_id: int,
    user: User = Depends(require_roles(*_OPS)),
    db: Session = Depends(get_db),
):
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.model_validate(alert)


@router.patch("/alerts/{alert_id}/status", response_model=AlertOut)
def update_alert_status(
    alert_id: int,
    data: AlertStatusIn,
    request: Request,
    user: User = Depends(require_roles(*_STAFF)),
    db: Session = Depends(get_db),
):
    alert = db.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    valid = {s.value for s in AlertStatus}
    if data.status not in valid:
        raise HTTPException(status_code=422, detail=f"Invalid alert status '{data.status}'")

    alert.status = data.status
    alert.status_note = data.note
    alert.reviewed_by_id = user.id
    audit(db, actor=user, action="alert.status", entity_type="alert",
          entity_id=alert.id, detail={"to": data.status, "note": data.note},
          ip=client_ip(request))

    investigation = None
    # confirming an alert automatically opens an investigation
    if data.status == AlertStatus.CONFIRMED.value:
        existing = db.query(Investigation).filter(
            Investigation.alert_id == alert.id).first()
        if existing is None:
            investigation = Investigation(
                alert_id=alert.id,
                title=f"Investigation for: {alert.title[:160]}",
                assigned_to_id=user.id,
            )
            db.add(investigation)
            db.flush()
            audit(db, actor=user, action="investigation.create", entity_type="investigation",
                  entity_id=investigation.id,
                  detail={"alert_id": alert.id, "auto": True}, ip=client_ip(request))
    db.flush()
    out = AlertOut.model_validate(alert)
    if investigation is not None:
        out.status_note = (out.status_note or "") + f" [investigation #{investigation.id} opened]"
    return out


@router.get("/investigations", response_model=Page[InvestigationOut])
def list_investigations(
    status: str | None = Query(default=None),
    alert_id: int | None = Query(default=None),
    page_page: tuple[int, int] = Depends(pagination_params),
    user: User = Depends(require_roles(*_OPS)),
    db: Session = Depends(get_db),
):
    page, page_size = page_page
    query = db.query(Investigation)
    if status:
        query = query.filter(Investigation.status == status)
    if alert_id:
        query = query.filter(Investigation.alert_id == alert_id)
    total = query.count()
    rows = (query.order_by(Investigation.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return Page.build([InvestigationOut.model_validate(i) for i in rows],
                      total, page, page_size)


@router.patch("/investigations/{investigation_id}", response_model=InvestigationOut)
def update_investigation(
    investigation_id: int,
    data: InvestigationUpdateIn,
    request: Request,
    user: User = Depends(require_roles(*_OPS)),
    db: Session = Depends(get_db),
):
    investigation = db.get(Investigation, investigation_id)
    if investigation is None:
        raise HTTPException(status_code=404, detail="Investigation not found")
    changed = []
    if data.status:
        investigation.status = data.status
        changed.append(f"status={data.status}")
        if data.status in (InvestigationStatus.CLOSED_RESOLVED.value,
                           InvestigationStatus.CLOSED_NO_ACTION.value):
            investigation.closed_at = datetime.now(timezone.utc)
    if data.notes is not None:
        investigation.notes = data.notes
        changed.append("notes")
    if data.findings is not None:
        investigation.findings = data.findings
        changed.append("findings")
    if data.assigned_to_id is not None:
        investigation.assigned_to_id = data.assigned_to_id
        changed.append(f"assigned_to={data.assigned_to_id}")
    audit(db, actor=user, action="investigation.update", entity_type="investigation",
          entity_id=investigation.id, detail={"changes": changed}, ip=client_ip(request))
    return InvestigationOut.model_validate(investigation)
