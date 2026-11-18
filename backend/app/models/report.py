from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ReportStatus, UrgencyLevel
from app.models.user import utcnow


class MedicalReport(Base):
    """Voluntary symptom report. Patient identity is stored but NEVER exposed
    to civic administrators; clinicians see content with an alias only."""

    __tablename__ = "medical_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    patient_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True,
                                                   nullable=True)
    created_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    document_id: Mapped[int | None] = mapped_column(ForeignKey("documents.id"), nullable=True)

    text: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    entities: Mapped[list | None] = mapped_column(JSON, nullable=True)
    symptoms: Mapped[list | None] = mapped_column(JSON, nullable=True)
    symptom_categories: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ner_backend: Mapped[str | None] = mapped_column(String(40), nullable=True)
    entity_count: Mapped[int] = mapped_column(default=0, nullable=False)

    urgency: Mapped[str] = mapped_column(String(12), default=UrgencyLevel.LOW.value,
                                         index=True, nullable=False)
    urgency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    urgency_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)

    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    digest: Mapped[str | None] = mapped_column(Text, nullable=True)

    district: Mapped[str | None] = mapped_column(String(60), index=True, nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)

    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default=ReportStatus.SUBMITTED.value,
                                        index=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow,
                                                 index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow,
                                                 onupdate=utcnow, nullable=False)

    patient = relationship("User", foreign_keys=[patient_id])
    document = relationship("Document", foreign_keys=[document_id])
