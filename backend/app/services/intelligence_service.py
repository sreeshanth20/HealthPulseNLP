"""Cross-domain intelligence: scan orchestration + per-record related items."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.audit import audit
from app.models.alert import Alert
from app.models.complaint import Complaint
from app.models.enums import AlertStatus
from app.models.report import MedicalReport
from app.models.user import User
from app.services import nlp_service
from ml.config import DISCLAIMER
from ml.inference.pipeline import get_pipeline


def run_scan(db: Session, user: User, days: int, ip: str | None = None) -> dict:
    """Run the cross-domain engine over the scan window and persist new alerts.

    De-duplication: an alert with the same (type, title) that is not DISMISSED
    and was created within the last 7 days suppresses a new row.
    """
    nlp = get_pipeline()
    since = nlp_service.scan_window(days)

    complaint_rows = nlp_service.engine_complaint_rows(db, since)
    report_rows = nlp_service.engine_report_rows(db, since)
    daily = nlp_service.daily_series(db, since)

    result = nlp.scan_cross_domain(complaint_rows, report_rows, daily_series=daily)

    created: list[Alert] = []
    suppress_since = datetime.now(timezone.utc) - timedelta(days=7)
    for alert_data in result["alerts"]:
        existing = (
            db.query(Alert)
            .filter(
                and_(
                    Alert.type == alert_data["type"],
                    Alert.title == alert_data["title"],
                    Alert.status != AlertStatus.DISMISSED.value,
                    Alert.created_at >= suppress_since,
                )
            )
            .first()
        )
        if existing:
            continue
        alert = Alert(
            type=alert_data["type"],
            title=alert_data["title"][:300],
            interpretation=alert_data.get("interpretation"),
            disclaimer=DISCLAIMER,
            score=alert_data["score"],
            districts=alert_data.get("districts"),
            complaint_categories=alert_data.get("complaint_categories"),
            n_complaints=alert_data.get("n_complaints", 0),
            n_reports=alert_data.get("n_reports", 0),
            n_supporting_pairs=alert_data.get("n_supporting_pairs", 0),
            evidence=alert_data.get("evidence"),
        )
        db.add(alert)
        db.flush()
        created.append(alert)

    audit(db, actor=user, action="intelligence.scan", entity_type="system",
          entity_id=None,
          detail={"days": days, "complaints": result["stats"]["complaints_scanned"],
                  "reports": result["stats"]["reports_scanned"],
                  "pairs": result["stats"]["candidate_pairs"],
                  "new_alerts": len(created)}, ip=ip)

    return {
        "scan": result["stats"],
        "alerts_created": len(created),
        "alerts": [
            {
                "id": a.id, "type": a.type, "title": a.title, "score": a.score,
                "districts": a.districts, "status": a.status,
            }
            for a in created
        ],
        "disclaimer": DISCLAIMER,
    }


def related_for_complaint(db: Session, complaint: Complaint, limit: int = 5) -> dict:
    """Cross-domain matches for one complaint: symptom reports in space/time."""
    nlp = get_pipeline()
    corpus = nlp_service.report_corpus(db, days=60, exclude_id=None)
    matches = nlp.search.top_k(complaint.text, corpus, k=limit, min_score=0.15)

    enriched: list[dict] = []
    for match in matches:
        report = db.get(MedicalReport, match["id"])
        if report is None:
            continue
        distance_km = None
        if complaint.lat is not None and report.lat is not None:
            from ml.preprocessing.gazetteer import haversine_km

            distance_km = haversine_km(complaint.lat, complaint.lng or 0.0,
                                       report.lat, report.lng or 0.0)
            if distance_km > 10.0:
                continue
        gap_days = None
        if complaint.created_at and report.created_at:
            gap_days = abs((complaint.created_at - report.created_at).total_seconds()) / 86400.0
        enriched.append({
            "report_id": report.id,
            "symptoms": report.symptoms or [],
            "symptom_categories": report.symptom_categories or [],
            "urgency": report.urgency,
            "district": report.district,
            "semantic_score": match["score"],
            "distance_km": round(distance_km, 3) if distance_km is not None else None,
            "gap_days": round(gap_days, 1) if gap_days is not None else None,
            "excerpt": report.text[:200],
        })
    return {"complaint_id": complaint.id, "related_reports": enriched,
            "disclaimer": DISCLAIMER}


def related_for_report(db: Session, report: MedicalReport, limit: int = 5) -> dict:
    """Civic complaints near one symptom report (investigation lead, admin view)."""
    nlp = get_pipeline()
    corpus = nlp_service.complaint_corpus(db, days=60)
    matches = nlp.search.top_k(report.text, corpus, k=limit, min_score=0.15)

    enriched: list[dict] = []
    for match in matches:
        complaint = db.get(Complaint, match["id"])
        if complaint is None:
            continue
        distance_km = None
        if report.lat is not None and complaint.lat is not None:
            from ml.preprocessing.gazetteer import haversine_km

            distance_km = haversine_km(report.lat, report.lng or 0.0,
                                       complaint.lat, complaint.lng or 0.0)
            if distance_km > 10.0:
                continue
        enriched.append({
            "complaint_id": complaint.id,
            "title": complaint.title,
            "category": complaint.category,
            "status": complaint.status,
            "district": complaint.district,
            "semantic_score": match["score"],
            "distance_km": round(distance_km, 3) if distance_km is not None else None,
            "excerpt": complaint.text[:200],
        })
    return {"report_id": report.id, "related_complaints": enriched,
            "disclaimer": DISCLAIMER}
