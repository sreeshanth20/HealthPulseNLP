from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import DocumentStatus
from app.models.user import utcnow


class Document(Base):
    """Metadata for uploaded medical documents. Bytes live outside the DB in a
    content-addressed store; access is only via authorized endpoints."""

    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    uploader_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True,
                                                    nullable=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    mime: Mapped[str | None] = mapped_column(String(100), nullable=True)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    pages: Mapped[int | None] = mapped_column(Integer, nullable=True)
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extraction_status: Mapped[str] = mapped_column(String(20),
                                                   default=DocumentStatus.UPLOADED.value,
                                                   nullable=False)

    report_id: Mapped[int | None] = mapped_column(Integer, nullable=True,
                                                  index=True)  # denormalized link (reports.document_id is authoritative)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow,
                                                 nullable=False)
