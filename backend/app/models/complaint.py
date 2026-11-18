from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import ComplaintStatus, UrgencyLevel
from app.models.user import utcnow


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(primary_key=True)
    reporter_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), index=True,
                                                    nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    category_confidence: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    classifier_method: Mapped[str | None] = mapped_column(String(40), nullable=True)

    urgency: Mapped[str] = mapped_column(String(12), default=UrgencyLevel.LOW.value,
                                         index=True, nullable=False)
    urgency_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    urgency_reasons: Mapped[list | None] = mapped_column(JSON, nullable=True)

    language: Mapped[str | None] = mapped_column(String(8), nullable=True)
    district: Mapped[str | None] = mapped_column(String(60), index=True, nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_source: Mapped[str | None] = mapped_column(String(30), nullable=True)

    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default=ComplaintStatus.SUBMITTED.value,
                                        index=True, nullable=False)
    duplicate_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("complaints.id"), nullable=True)
    duplicate_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    resolution_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow,
                                                 index=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow,
                                                 onupdate=utcnow, nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    reporter = relationship("User", foreign_keys=[reporter_id])
    duplicate_of = relationship("Complaint", remote_side=[id], foreign_keys=[duplicate_of_id])
