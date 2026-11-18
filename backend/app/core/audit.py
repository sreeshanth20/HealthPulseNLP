"""Audit logging helper — records every privileged mutation."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User

_MAX_DETAIL_JSON = 4000


def audit(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: str | int | None = None,
    detail: dict[str, Any] | None = None,
    ip: str | None = None,
) -> None:
    """Persist an audit row. Best-effort: never breaks the caller's request."""
    try:
        serialized = None
        if detail:
            serialized = json.dumps(detail, default=str)[:_MAX_DETAIL_JSON]
        db.add(AuditLog(
            actor_id=actor.id if actor else None,
            actor_role=actor.role if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id) if entity_id is not None else None,
            detail_json=serialized,
            ip=ip,
        ))
    except Exception:  # noqa: BLE001 - audit must not break business flow
        pass


def client_ip(request) -> str | None:
    """Extract client IP from request (proxy-aware, best effort)."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
