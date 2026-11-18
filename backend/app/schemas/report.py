"""Medical report & document schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ReportIn(BaseModel):
    text: str = Field(min_length=15, max_length=8000)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    district: str | None = Field(default=None, max_length=60)


class EntityOut(BaseModel):
    text: str
    canonical: str
    type: str
    start: int
    end: int
    confidence: float


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    text: str
    language: str | None = None
    entities: list | None = None
    symptoms: list | None = None
    symptom_categories: list | None = None
    ner_backend: str | None = None
    entity_count: int = 0
    urgency: str
    urgency_score: float
    urgency_reasons: list | None = None
    summary: str | None = None
    digest: str | None = None
    district: str | None = None
    lat: float | None = None
    lng: float | None = None
    status: str
    created_at: datetime
    patient_id: int | None = None
    patient_alias: str | None = None  # computed in service, not stored
    document_id: int | None = None


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    mime: str | None = None
    size_bytes: int
    sha256: str
    pages: int | None = None
    extraction_status: str
    report_id: int | None = None
    created_at: datetime
    uploader_id: int | None = None


class DocumentTextOut(BaseModel):
    id: int
    filename: str
    extracted_text: str | None
    extraction_status: str


class ReportFromDocumentIn(BaseModel):
    document_id: int
