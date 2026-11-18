"""Admin endpoints: audit logs + system health (SUPER_ADMIN)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import cast, String as _SAString
from sqlalchemy.orm import Session

from app.core.cache import cache_status
from app.core.config import settings
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.complaint import Complaint
from app.models.document import Document
from app.models.enums import Role
from app.models.report import MedicalReport
from app.models.user import User
from app.schemas.common import Page
from app.services import nlp_service
from app.services.document_service import storage_root
from app.utils.pagination import pagination_params

router = APIRouter(tags=["admin"])


@router.get("/audit-logs")
def list_audit_logs(
    actor_id: int | None = Query(default=None),
    action: str | None = Query(default=None, max_length=60),
    entity_type: str | None = Query(default=None, max_length=40),
    q: str | None = Query(default=None, max_length=100),
    page_page: tuple[int, int] = Depends(pagination_params),
    user: User = Depends(require_roles(Role.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    page, page_size = page_page
    query = db.query(AuditLog)
    if actor_id:
        query = query.filter(AuditLog.actor_id == actor_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)
    if q:
        query = query.filter(cast(AuditLog.detail_json, _SAString).ilike(f"%{q}%"))
    total = query.count()
    rows = (query.order_by(AuditLog.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    items = [
        {
            "id": log.id,
            "actor_id": log.actor_id,
            "actor_role": log.actor_role,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "detail": log.detail_json,
            "ip": log.ip,
            "created_at": log.created_at.isoformat(),
        }
        for log in rows
    ]
    return Page.build(items, total, page, page_size)


@router.get("/system/health")
def system_health(
    user: User = Depends(require_roles(Role.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    db_ok = True
    counts: dict = {}
    try:
        counts = {
            "users": db.query(User).count(),
            "complaints": db.query(Complaint).count(),
            "medical_reports": db.query(MedicalReport).count(),
            "documents": db.query(Document).count(),
            "alerts": db.query(Alert).count(),
        }
    except Exception:  # noqa: BLE001
        db_ok = False

    root = storage_root()
    storage_mb = 0.0
    try:
        storage_mb = sum(f.stat().st_size for f in root.rglob("*") if f.is_file()) / 1e6
    except Exception:  # noqa: BLE001
        pass

    return {
        "database": {"ok": db_ok, "counts": counts},
        "cache": cache_status(),
        "nlp_pipeline": nlp_service.pipeline_health(),
        "document_storage": {"root": str(root), "used_mb": round(storage_mb, 2)},
        "environment": settings.environment,
    }
