"""User administration (SUPER_ADMIN)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.audit import audit, client_ip
from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.auth import UserOut, UserUpdateIn
from app.schemas.common import Page
from app.utils.pagination import pagination_params

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=Page[UserOut])
def list_users(
    q: str | None = Query(default=None, max_length=100),
    role: str | None = Query(default=None),
    active: bool | None = Query(default=None),
    page_page: tuple[int, int] = Depends(pagination_params),
    user: User = Depends(require_roles(Role.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    page, page_size = page_page
    query = db.query(User)
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(or_(User.email.like(like), User.full_name.ilike(like)))
    if role:
        query = query.filter(User.role == role)
    if active is not None:
        query = query.filter(User.is_active == active)
    total = query.count()
    rows = (query.order_by(User.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return Page.build([UserOut.model_validate(u) for u in rows], total, page, page_size)


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    data: UserUpdateIn,
    request: Request,
    admin: User = Depends(require_roles(Role.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")

    if data.role and data.role != target.role:
        # guard: never leave the system without an active super admin
        if target.role == Role.SUPER_ADMIN.value and target.is_active:
            other_super = db.query(User).filter(
                User.role == Role.SUPER_ADMIN.value,
                User.is_active.is_(True), User.id != target.id).count()
            if other_super == 0:
                raise HTTPException(status_code=422,
                                    detail="Cannot demote the last active super administrator")
        old_role = target.role
        target.role = data.role
        audit(db, actor=admin, action="user.role_change", entity_type="user",
              entity_id=target.id,
              detail={"from": old_role, "to": data.role}, ip=client_ip(request))
    if data.is_active is not None and data.is_active != target.is_active:
        if (not data.is_active and target.role == Role.SUPER_ADMIN.value):
            other_super = db.query(User).filter(
                User.role == Role.SUPER_ADMIN.value,
                User.is_active.is_(True), User.id != target.id).count()
            if other_super == 0:
                raise HTTPException(status_code=422,
                                    detail="Cannot disable the last active super administrator")
        target.is_active = data.is_active
        audit(db, actor=admin, action="user.activation", entity_type="user",
              entity_id=target.id, detail={"is_active": data.is_active},
              ip=client_ip(request))
    return UserOut.model_validate(target)


@router.get("/{user_id}", response_model=UserOut)
def get_user(
    user_id: int,
    admin: User = Depends(require_roles(Role.SUPER_ADMIN)),
    db: Session = Depends(get_db),
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(target)
