"""Secure document storage: content-addressed local store + text extraction.

- Files are stored under DOCUMENT_STORAGE_DIR/<sha256>/<sanitized name>.
- The client never receives filesystem paths, only metadata + endpoints.
- Extraction: PyMuPDF for PDFs; UTF-8 (with latin-1 fallback) for text.
- OCR fallback: if a PDF has no text layer, we flag extraction_status=NO_TEXT
  and surface guidance (OCR requires the optional tesseract extra).
"""

from __future__ import annotations

import hashlib
import re
import secrets
from pathlib import Path

from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.core.config import settings
from app.models.document import Document
from app.models.enums import DocumentStatus
from app.models.user import User

ALLOWED_MIME = {
    "application/pdf": ".pdf",
    "text/plain": ".txt",
    "text/markdown": ".md",
    "application/msword": ".doc",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md", ".doc", ".docx"}
_UNSAFE = re.compile(r"[^A-Za-z0-9._-]+")


def storage_root() -> Path:
    root = Path(settings.document_storage_dir)
    root.mkdir(parents=True, exist_ok=True)
    return root


def _sanitize_filename(name: str) -> str:
    cleaned = _UNSAFE.sub("_", Path(name).name).strip("._")
    return (cleaned or "upload")[:120]


def _extract_pdf(path: Path) -> tuple[str | None, int | None]:
    try:
        import fitz  # PyMuPDF

        doc = fitz.open(path)
        pages = doc.page_count
        text = "\n".join(page.get_text() for page in doc)
        doc.close()
        return (text if text.strip() else None), pages
    except ImportError:
        raise HTTPException(
            status_code=503,
            detail="PyMuPDF is not installed on this server; PDF extraction unavailable",
        )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=422, detail=f"Could not read PDF: {exc}") from exc


def _extract_plain(path: Path) -> str | None:
    raw = path.read_bytes()
    for encoding in ("utf-8", "latin-1"):
        try:
            text = raw.decode(encoding)
            return text if text.strip() else None
        except UnicodeDecodeError:
            continue
    return None


async def save_upload(db: Session, user: User, upload: UploadFile,
                      ip: str | None = None) -> Document:
    ext = Path(upload.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415,
                            detail=f"Unsupported file type '{ext}'. Allowed: {sorted(ALLOWED_EXTENSIONS)}")

    max_bytes = settings.max_upload_mb * 1024 * 1024
    content = await upload.read()
    if len(content) == 0:
        raise HTTPException(status_code=422, detail="Empty file")
    if len(content) > max_bytes:
        raise HTTPException(status_code=413,
                            detail=f"File exceeds {settings.max_upload_mb} MB limit")

    sha256 = hashlib.sha256(content).hexdigest()
    safe_name = _sanitize_filename(upload.filename or "upload")
    file_dir = storage_root() / sha256
    file_dir.mkdir(parents=True, exist_ok=True)
    final_path = file_dir / f"{secrets.token_hex(6)}_{safe_name}"
    final_path.write_bytes(content)
    try:
        final_path.chmod(0o640)
    except OSError:  # pragma: no cover - platform dependent
        pass

    pages: int | None = None
    extracted: str | None = None
    status = DocumentStatus.UPLOADED.value
    if ext == ".pdf":
        try:
            extracted, pages = _extract_pdf(final_path)
            status = DocumentStatus.EXTRACTED.value if extracted else "NO_TEXT"
        except HTTPException:
            status = DocumentStatus.FAILED.value
            raise
    elif ext in (".txt", ".md"):
        extracted = _extract_plain(final_path)
        status = DocumentStatus.EXTRACTED.value if extracted else "NO_TEXT"
    else:  # .doc/.docx: no extractor bundled; document limitation
        status = "UNSUPPORTED_FORMAT"

    document = Document(
        uploader_id=user.id,
        filename=safe_name,
        mime=upload.content_type,
        size_bytes=len(content),
        sha256=sha256,
        storage_path=str(final_path.relative_to(storage_root())),
        pages=pages,
        extracted_text=extracted[:100_000] if extracted else None,
        extraction_status=status,
    )
    db.add(document)
    db.flush()
    audit(db, actor=user, action="document.upload", entity_type="document",
          entity_id=document.id,
          detail={"filename": safe_name, "size": len(content), "status": status}, ip=ip)
    return document


def get_document_or_404(db: Session, document_id: int) -> Document:
    document = db.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


def can_view_document(user: User, document: Document) -> bool:
    if user.role in ("CLINICIAN", "HEALTH_ADMIN", "SUPER_ADMIN"):
        return True
    return document.uploader_id == user.id


def delete_document(db: Session, user: User, document: Document,
                    ip: str | None = None) -> None:
    target = storage_root() / document.storage_path
    try:
        if target.exists():
            target.unlink()
    except OSError:  # noqa: BLE001
        pass
    audit(db, actor=user, action="document.delete", entity_type="document",
          entity_id=document.id, detail={"filename": document.filename}, ip=ip)
    db.delete(document)
