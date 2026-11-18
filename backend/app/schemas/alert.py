"""Alert & investigation schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: str
    title: str
    interpretation: str | None = None
    disclaimer: str | None = None
    score: float
    districts: list | None = None
    complaint_categories: list | None = None
    n_complaints: int
    n_reports: int
    n_supporting_pairs: int
    evidence: list | None = None
    status: str
    status_note: str | None = None
    created_at: datetime


class AlertStatusIn(BaseModel):
    status: str = Field(pattern="^(NEW|REVIEWING|CONFIRMED|DISMISSED)$")
    note: str | None = Field(default=None, max_length=2000)


class InvestigationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    alert_id: int
    title: str | None = None
    status: str
    notes: str | None = None
    findings: str | None = None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
    assigned_to_id: int | None = None


class InvestigationUpdateIn(BaseModel):
    status: str | None = Field(
        default=None,
        pattern="^(OPEN|FIELD_VISIT_SCHEDULED|SAMPLING|CLOSED_RESOLVED|CLOSED_NO_ACTION)$",
    )
    notes: str | None = None
    findings: str | None = None
    assigned_to_id: int | None = None


class ScanIn(BaseModel):
    days: int = Field(default=30, ge=1, le=180)
