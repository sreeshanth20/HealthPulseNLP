"""Canonical string enums shared by models, schemas and services."""

from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.value


class Role(StrEnum):
    CITIZEN = "CITIZEN"
    PATIENT = "PATIENT"
    CLINICIAN = "CLINICIAN"
    MUNICIPAL_ADMIN = "MUNICIPAL_ADMIN"
    HEALTH_ADMIN = "HEALTH_ADMIN"
    SUPER_ADMIN = "SUPER_ADMIN"

    @property
    def is_civic_staff(self) -> bool:
        return self in (Role.MUNICIPAL_ADMIN, Role.HEALTH_ADMIN, Role.SUPER_ADMIN)

    @property
    def is_health_staff(self) -> bool:
        return self in (Role.CLINICIAN, Role.HEALTH_ADMIN, Role.SUPER_ADMIN)


class ComplaintCategory(StrEnum):
    WATER_CONTAMINATION = "water_contamination"
    GARBAGE_SANITATION = "garbage_sanitation"
    DRAINAGE_SEWAGE = "drainage_sewage"
    MOSQUITO_MENACE = "mosquito menace"
    ROAD_INFRASTRUCTURE = "road_infrastructure"
    STREET_LIGHTING = "street_lighting"
    PUBLIC_SANITATION = "public_sanitation"
    NOISE_POLLUTION = "noise_pollution"
    ANIMAL_NUISANCE = "animal_nuisance"
    OTHER = "other"


class ComplaintStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    REJECTED = "REJECTED"


class UrgencyLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ReportStatus(StrEnum):
    SUBMITTED = "SUBMITTED"
    REVIEWED = "REVIEWED"
    FLAGGED = "FLAGGED"


class AlertType(StrEnum):
    CROSS_DOMAIN_CLUSTER = "CROSS_DOMAIN_CLUSTER"
    TEMPORAL_ANOMALY = "TEMPORAL_ANOMALY"
    SPATIAL_CLUSTER = "SPATIAL_CLUSTER"


class AlertStatus(StrEnum):
    NEW = "NEW"
    REVIEWING = "REVIEWING"
    CONFIRMED = "CONFIRMED"
    DISMISSED = "DISMISSED"


class InvestigationStatus(StrEnum):
    OPEN = "OPEN"
    FIELD_VISIT_SCHEDULED = "FIELD_VISIT_SCHEDULED"
    SAMPLING = "SAMPLING"
    CLOSED_RESOLVED = "CLOSED_RESOLVED"
    CLOSED_NO_ACTION = "CLOSED_NO_ACTION"


class DocumentStatus(StrEnum):
    UPLOADED = "UPLOADED"
    EXTRACTED = "EXTRACTED"
    FAILED = "FAILED"


# Status transition graph for complaints (validated in the service layer).
COMPLAINT_TRANSITIONS: dict[str, set[str]] = {
    ComplaintStatus.SUBMITTED.value: {ComplaintStatus.ACKNOWLEDGED.value,
                                      ComplaintStatus.REJECTED.value,
                                      ComplaintStatus.IN_PROGRESS.value},
    ComplaintStatus.ACKNOWLEDGED.value: {ComplaintStatus.IN_PROGRESS.value,
                                         ComplaintStatus.REJECTED.value},
    ComplaintStatus.IN_PROGRESS.value: {ComplaintStatus.RESOLVED.value,
                                        ComplaintStatus.REJECTED.value},
    ComplaintStatus.RESOLVED.value: set(),
    ComplaintStatus.REJECTED.value: set(),
}
