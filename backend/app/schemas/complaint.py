"""Complaint schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ComplaintIn(BaseModel):
    title: str = Field(min_length=5, max_length=200)
    text: str = Field(min_length=15, max_length=6000)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    address: str | None = Field(default=None, max_length=255)


class UrgencyOut(BaseModel):
    label: str
    score: float
    reasons: list[str]


class LocationOut(BaseModel):
    raw_text: str | None = None
    district: str | None = None
    lat: float | None = None
    lng: float | None = None
    pincode: str | None = None
    confidence: float = 0.0
    source: str | None = None


class ComplaintAnalysisOut(BaseModel):
    category: str
    category_confidence: float
    category_scores: dict[str, float] = {}
    classifier_method: str
    matched_terms: list[str] = []
    urgency: UrgencyOut
    location: LocationOut
    language: str | None = None


class DuplicateCandidateOut(BaseModel):
    id: int
    title: str | None = None
    text: str
    category: str | None = None
    district: str | None = None
    score: float
    is_duplicate: bool
    signals: dict = {}


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    text: str
    category: str
    category_confidence: float
    urgency: str
    urgency_score: float
    urgency_reasons: list | None = None
    language: str | None = None
    district: str | None = None
    address: str | None = None
    lat: float | None = None
    lng: float | None = None
    status: str
    duplicate_of_id: int | None = None
    duplicate_score: float | None = None
    resolution_note: str | None = None
    created_at: datetime
    resolved_at: datetime | None = None
    reporter_id: int | None = None


class ComplaintStatusIn(BaseModel):
    status: str = Field(pattern="^(SUBMITTED|ACKNOWLEDGED|IN_PROGRESS|RESOLVED|REJECTED)$")
    note: str | None = Field(default=None, max_length=2000)


class MarkDuplicateIn(BaseModel):
    original_id: int
