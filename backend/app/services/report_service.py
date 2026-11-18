"""Medical report business logic."""

from __future__ import annotations

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.models.document import Document
from app.models.enums import Role
from app.models.report import MedicalReport
from app.models.user import User
from app.schemas.report import ReportIn
from ml.inference.pipeline import get_pipeline


def create_report(db: Session, user: User, data: ReportIn,
                  document_id: int | None = None,
                  ip: str | None = None) -> MedicalReport:
    nlp = get_pipeline()
    analysis = nlp.analyze_symptom_report(data.text, lat=data.lat, lng=data.lng)

    district = data.district or analysis["location"]["district"]
    report = MedicalReport(
        patient_id=user.id,
        created_by_id=user.id,
        document_id=document_id,
        text=data.text,
        language=analysis["language"],
        entities=analysis["entities"],
        symptoms=analysis["symptoms"],
        symptom_categories=analysis["symptom_categories"],
        ner_backend=analysis["ner_backend"],
        entity_count=analysis["entity_count"],
        urgency=analysis["urgency"]["label"],
        urgency_score=analysis["urgency"]["score"],
        urgency_reasons=analysis["urgency"]["reasons"],
        summary=analysis["summary"],
        digest=analysis["digest"],
        district=district,
        lat=data.lat if data.lat is not None else analysis["location"]["lat"],
        lng=data.lng if data.lng is not None else analysis["location"]["lng"],
        embedding=analysis["embedding"],
    )
    db.add(report)
    db.flush()

    audit(db, actor=user, action="report.create", entity_type="medical_report",
          entity_id=report.id,
          detail={"urgency": report.urgency, "symptoms": report.symptoms,
                  "district": report.district}, ip=ip)
    return report


def get_report_or_404(db: Session, report_id: int) -> MedicalReport:
    report = db.get(MedicalReport, report_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


def can_view_report(user: User, report: MedicalReport) -> bool:
    """Privacy rule: patients see only their own; clinical/health staff see
    content with an alias; civic (municipal) staff have no access."""
    if user.role in (Role.CLINICIAN.value, Role.HEALTH_ADMIN.value,
                     Role.SUPER_ADMIN.value):
        return True
    return report.patient_id == user.id


def patient_alias(report: MedicalReport) -> str:
    """Stable, non-identifying display alias."""
    if report.patient_id is None:
        return "Anonymous"
    return f"Patient #{report.patient_id:05d}"


def summarize_report(db: Session, user: User, report: MedicalReport,
                     ip: str | None = None) -> MedicalReport:
    nlp = get_pipeline()
    summary = nlp.analyze_symptom_report(report.text)
    report.summary = summary["summary"]
    report.digest = summary["digest"]
    report.symptoms = summary["symptoms"]
    report.entities = summary["entities"]
    report.symptom_categories = summary["symptom_categories"]
    report.entity_count = summary["entity_count"]
    audit(db, actor=user, action="report.summarize", entity_type="medical_report",
          entity_id=report.id, ip=ip)
    return report


def create_from_document(db: Session, user: User, document: Document,
                         ip: str | None = None) -> MedicalReport:
    if not document.extracted_text or len(document.extracted_text.strip()) < 15:
        raise HTTPException(status_code=422,
                            detail="Document has no extractable text to convert into a report")
    data = ReportIn(text=document.extracted_text[:8000],
                    lat=None, lng=None, district=None)
    report = create_report(db, user, data, document_id=document.id, ip=ip)
    return report
