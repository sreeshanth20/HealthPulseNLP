"""Seed the demo dataset.

Creates demo accounts (all roles), synthetic complaints/reports, alerts from a
live intelligence scan, and demonstrates duplicate detection.

ALL DATA IS SYNTHETIC DEMONSTRATION DATA - see docs/DEMO_DATA.md.

Usage (from backend/):
    python -m scripts.seed_demo            # SQLite dev DB / DATABASE_URL target
    python -m scripts.seed_demo --reset    # wipe demo data first
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from app.core.database import Base, SessionLocal, engine  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.models.alert import Alert  # noqa: E402
from app.models.complaint import Complaint  # noqa: E402
from app.models.enums import AlertStatus, ComplaintStatus  # noqa: E402
from app.models.investigation import Investigation  # noqa: E402
from app.models.report import MedicalReport  # noqa: E402
from app.models.user import User  # noqa: E402
from ml.datasets.demo_corpus import COMPLAINTS, MEDICAL_REPORTS  # noqa: E402
from ml.inference.pipeline import get_pipeline  # noqa: E402

DEMO_PASSWORD = "HealthPulse!2026"

ACCOUNTS = [
    ("citizen@healthpulse.demo", "Meera Citizen", "CITIZEN"),
    ("patient@healthpulse.demo", "Arjun Patient", "PATIENT"),
    ("clinician@healthpulse.demo", "Dr. Dev Clinician", "CLINICIAN"),
    ("municipal@healthpulse.demo", "Ravi Municipal", "MUNICIPAL_ADMIN"),
    ("health@healthpulse.demo", "Dr. Sana Health", "HEALTH_ADMIN"),
    ("super@healthpulse.demo", "Ada Super", "SUPER_ADMIN"),
]


def reset(db) -> None:
    db.query(Investigation).delete()
    db.query(Alert).delete()
    db.query(MedicalReport).delete()
    db.query(Complaint).delete()
    db.query(User).filter(User.email.like("%@healthpulse.demo")).delete(
        synchronize_session=False)
    db.commit()


def seed() -> dict:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = {}
        for email, name, role in ACCOUNTS:
            user = db.query(User).filter(User.email == email).first()
            if user is None:
                user = User(email=email, full_name=name, role=role,
                            password_hash=hash_password(DEMO_PASSWORD))
                db.add(user)
                db.flush()
            else:
                # Demo credentials are part of the supported local workflow.
                # Re-seeding repairs stale demo records created by an older build
                # without touching non-demo accounts or application data.
                user.full_name = name
                user.role = role
                user.is_active = True
                user.password_hash = hash_password(DEMO_PASSWORD)
            users[role] = user

        patients = [users["PATIENT"], users["CITIZEN"]]
        complaint_ids: list[int] = []
        for row in COMPLAINTS:
            complaint = db.get(Complaint, row["id"])
            if complaint is None:
                nlp = get_pipeline()
                analysis = nlp.analyze_complaint(row["text"], lat=row["lat"], lng=row["lng"])
                reporter = patients[row["id"] % len(patients)]
                complaint = Complaint(
                    id=row["id"],
                    reporter_id=reporter.id,
                    title=row["title"],
                    text=row["text"],
                    category=row["category"],
                    category_confidence=analysis["category_confidence"],
                    classifier_method=analysis["classifier_method"],
                    urgency=analysis["urgency"]["label"],
                    urgency_score=analysis["urgency"]["score"],
                    urgency_reasons=analysis["urgency"]["reasons"],
                    language=analysis["language"],
                    district=row["district"],
                    lat=row["lat"],
                    lng=row["lng"],
                    location_source=analysis["location"]["source"],
                    embedding=analysis["embedding"],
                    created_at=row["created_at"],
                    status=ComplaintStatus.RESOLVED.value if row["id"] == 111
                    else ComplaintStatus.SUBMITTED.value,
                    resolved_at=row["created_at"] if row["id"] == 111 else None,
                )
                db.add(complaint)
                db.flush()
            complaint_ids.append(complaint.id)

        for row in MEDICAL_REPORTS:
            report = db.get(MedicalReport, row["id"])
            if report is None:
                nlp = get_pipeline()
                analysis = nlp.analyze_symptom_report(row["text"], lat=row["lat"], lng=row["lng"])
                owner = users["PATIENT"] if row["id"] % 2 == 0 else users["CITIZEN"]
                report = MedicalReport(
                    id=row["id"],
                    patient_id=owner.id,
                    created_by_id=owner.id,
                    text=row["text"],
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
                    district=row["district"],
                    lat=row["lat"],
                    lng=row["lng"],
                    embedding=analysis["embedding"],
                    created_at=row["created_at"],
                )
                db.add(report)
                db.flush()

        # link explicit duplicate groups (ground truth for the demo UI)
        from ml.datasets.demo_corpus import DUPLICATE_GROUPS

        for group in DUPLICATE_GROUPS:
            original = db.get(Complaint, group["original"])
            if original is None:
                continue
            nlp = get_pipeline()
            for dup_id in group["duplicates"]:
                dup = db.get(Complaint, dup_id)
                if dup is None or dup.duplicate_of_id is not None:
                    continue
                scored = nlp.find_duplicates(
                    dup.text, [{"id": original.id, "text": original.text,
                                "category": original.category, "district": original.district,
                                "lat": original.lat, "lng": original.lng,
                                "created_at": original.created_at, "embedding": original.embedding}],
                    category=dup.category, lat=dup.lat, lng=dup.lng,
                    created_at=dup.created_at)
                dup.duplicate_of_id = original.id
                dup.duplicate_score = scored[0]["score"] if scored else None

        db.commit()

        # run a real intelligence scan and persist its alerts
        from app.services.intelligence_service import run_scan
        scan_result = run_scan(db, users["SUPER_ADMIN"], days=30)

        # demo workflow: first alert under review with an investigation
        first_alert = db.query(Alert).order_by(Alert.id).first()
        investigation_id = None
        if first_alert is not None:
            first_alert.status = AlertStatus.REVIEWING.value
            inv = Investigation(alert_id=first_alert.id,
                                title=f"Investigation for: {first_alert.title[:160]}",
                                assigned_to_id=users["HEALTH_ADMIN"].id,
                                notes="Demo workflow: field team scheduled for water sampling.")
            db.add(inv)
            db.flush()
            investigation_id = inv.id

        # acknowledge one complaint to show the lifecycle
        first_open = db.query(Complaint).filter(
            Complaint.status == ComplaintStatus.SUBMITTED.value).first()
        if first_open:
            first_open.status = ComplaintStatus.ACKNOWLEDGED.value

        db.commit()

        counts = {
            "users": len(ACCOUNTS),
            "complaints": db.query(Complaint).count(),
            "medical_reports": db.query(MedicalReport).count(),
            "alerts": db.query(Alert).count(),
            "investigations": db.query(Investigation).count(),
            "scan_pairs": scan_result["scan"]["candidate_pairs"],
        }
        print("Demo data seeded:")
        for key, value in counts.items():
            print(f"  {key}: {value}")
        print(f"Demo accounts (password: {DEMO_PASSWORD}):")
        for email, _, role in ACCOUNTS:
            print(f"  {role:<16} {email}")
        return counts
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--reset", action="store_true",
                        help="delete existing demo data before seeding")
    args = parser.parse_args()
    if args.reset:
        db = SessionLocal()
        reset(db)
        db.close()
        print("Existing demo data removed.")
    seed()
