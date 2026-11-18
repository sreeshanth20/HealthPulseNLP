"""Document upload/management endpoints (secure storage)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import client_ip
from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.enums import Role
from app.models.user import User
from app.schemas.common import Page
from app.schemas.report import DocumentOut, DocumentTextOut
from app.services import document_service
from app.utils.pagination import pagination_params

router = APIRouter(prefix="/documents", tags=["documents"])

_ALLOWED_ROLES = (Role.PATIENT, Role.CLINICIAN, Role.HEALTH_ADMIN, Role.SUPER_ADMIN)


@router.post("/upload", response_model=DocumentOut, status_code=201)
async def upload_document(
    request: Request,
    file: UploadFile = File(...),
    user: User = Depends(require_roles(*_ALLOWED_ROLES)),
    db: Session = Depends(get_db),
):
    document = await document_service.save_upload(db, user, file, ip=client_ip(request))
    return DocumentOut.model_validate(document)


@router.get("", response_model=Page[DocumentOut])
def list_documents(
    page_page: tuple[int, int] = Depends(pagination_params),
    user: User = Depends(require_roles(*_ALLOWED_ROLES)),
    db: Session = Depends(get_db),
):
    from app.models.document import Document

    page, page_size = page_page
    query = db.query(Document)
    if user.role != Role.SUPER_ADMIN.value and user.role != Role.CLINICIAN.value \
            and user.role != Role.HEALTH_ADMIN.value:
        query = query.filter(Document.uploader_id == user.id)
    total = query.count()
    rows = (query.order_by(Document.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size).all())
    return Page.build([DocumentOut.model_validate(d) for d in rows], total, page, page_size)


@router.get("/{document_id}", response_model=DocumentOut)
def get_document(
    document_id: int,
    user: User = Depends(require_roles(*_ALLOWED_ROLES)),
    db: Session = Depends(get_db),
):
    document = document_service.get_document_or_404(db, document_id)
    if not document_service.can_view_document(user, document):
        raise HTTPException(status_code=403, detail="You do not have access to this document")
    return DocumentOut.model_validate(document)


@router.get("/{document_id}/text", response_model=DocumentTextOut)
def get_document_text(
    document_id: int,
    user: User = Depends(require_roles(*_ALLOWED_ROLES)),
    db: Session = Depends(get_db),
):
    document = document_service.get_document_or_404(db, document_id)
    if not document_service.can_view_document(user, document):
        raise HTTPException(status_code=403, detail="You do not have access to this document")
    return DocumentTextOut(
        id=document.id, filename=document.filename,
        extracted_text=document.extracted_text,
        extraction_status=document.extraction_status,
    )


@router.delete("/{document_id}", status_code=204)
def delete_document(
    document_id: int,
    request: Request,
    user: User = Depends(require_roles(*_ALLOWED_ROLES)),
    db: Session = Depends(get_db),
):
    document = document_service.get_document_or_404(db, document_id)
    if document.uploader_id != user.id and user.role != Role.SUPER_ADMIN.value:
        raise HTTPException(status_code=403,
                            detail="Only the uploader or a super admin can delete a document")
    document_service.delete_document(db, user, document, ip=client_ip(request))
    return None
