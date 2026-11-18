"""Aggregations for dashboards. role-appropriate and cache-friendly."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.cache import cache_get_json, cache_set_json
from app.models.alert import Alert
from app.models.complaint import Complaint
from app.models.enums import Role
from app.models.investigation import Investigation
from app.models.report import MedicalReport
from app.models.user import User


def _day_key(dt: datetime) -> str:
    return dt.strftime("%Y-%m-%d")


def public_stats(db: Session) -> dict:
    cached = cache_get_json("analytics:public")
    if cached:
        return cached
    total = db.query(func.count(Complaint.id)).scalar() or 0
    resolved = db.query(func.count(Complaint.id)).filter(
        Complaint.status == "RESOLVED").scalar() or 0
    districts = db.query(func.count(func.distinct(Complaint.district))).scalar() or 0
    categories = dict(
        db.query(Complaint.category, func.count(Complaint.id))
        .group_by(Complaint.category).all()
    )
    result = {
        "total_complaints": total,
        "resolved_complaints": resolved,
        "resolution_rate": round(resolved / total, 3) if total else 0.0,
        "districts_covered": districts,
        "categories": {str(k): int(v) for k, v in categories.items()},
    }
    cache_set_json("analytics:public", result, ttl_seconds=30)
    return result


def daily_counts(db: Session, days: int = 14, district: str | None = None) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)

    cq = db.query(func.date(Complaint.created_at), func.count(Complaint.id))
    if district:
        cq = cq.filter(Complaint.district == district)
    complaints = {str(d): int(n) for d, n in cq.filter(
        Complaint.created_at >= since).group_by(func.date(Complaint.created_at)).all()}

    rq = db.query(func.date(MedicalReport.created_at), func.count(MedicalReport.id))
    if district:
        rq = rq.filter(MedicalReport.district == district)
    reports = {str(d): int(n) for d, n in rq.filter(
        MedicalReport.created_at >= since).group_by(func.date(MedicalReport.created_at)).all()}

    points = []
    for i in range(days):
        day = (datetime.now(timezone.utc) - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        points.append({"date": day,
                       "complaints": complaints.get(day, 0),
                       "reports": reports.get(day, 0)})
    return {"days": days, "district": district, "points": points}


def district_stats(db: Session) -> list[dict]:
    complaints = dict(
        db.query(Complaint.district, func.count(Complaint.id))
        .group_by(Complaint.district).all())
    open_c = dict(
        db.query(Complaint.district, func.count(Complaint.id))
        .filter(Complaint.status.in_(["SUBMITTED", "ACKNOWLEDGED", "IN_PROGRESS"]))
        .group_by(Complaint.district).all())
    reports = dict(
        db.query(MedicalReport.district, func.count(MedicalReport.id))
        .group_by(MedicalReport.district).all())
    high_urgency = dict(
        db.query(Complaint.district, func.count(Complaint.id))
        .filter(Complaint.urgency.in_(["HIGH", "CRITICAL"]))
        .group_by(Complaint.district).all())

    districts = sorted(set(complaints) | set(reports), key=lambda d: (d is None, d))
    out = []
    for d in districts:
        if d is None:
            continue
        out.append({
            "district": d,
            "complaints": int(complaints.get(d, 0)),
            "open_complaints": int(open_c.get(d, 0)),
            "reports": int(reports.get(d, 0)),
            "high_urgency": int(high_urgency.get(d, 0)),
        })
    return out


def heatmap_points(db: Session, days: int = 60) -> dict:
    since = datetime.now(timezone.utc) - timedelta(days=days)
    points: list[dict] = []

    for c in db.query(Complaint).filter(
            Complaint.created_at >= since, Complaint.lat.isnot(None)).limit(800):
        weight = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(c.urgency, 1)
        points.append({"lat": c.lat, "lng": c.lng, "weight": weight,
                       "kind": "complaint", "category": c.category,
                       "district": c.district, "id": c.id})
    for r in db.query(MedicalReport).filter(
            MedicalReport.created_at >= since, MedicalReport.lat.isnot(None)).limit(800):
        weight = {"LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(r.urgency, 1)
        points.append({"lat": r.lat, "lng": r.lng, "weight": weight,
                       "kind": "report", "district": r.district, "id": r.id})
    return {"points": points, "days": days}


def overview(db: Session, user: User) -> dict:
    """Role-appropriate KPI bundle."""
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=14)

    data: dict = {"role": user.role}

    if user.role in (Role.CITIZEN.value, Role.PATIENT.value):
        data["my_complaints"] = db.query(func.count(Complaint.id)).filter(
            Complaint.reporter_id == user.id).scalar() or 0
        data["my_open_complaints"] = db.query(func.count(Complaint.id)).filter(
            Complaint.reporter_id == user.id,
            Complaint.status.in_(["SUBMITTED", "ACKNOWLEDGED", "IN_PROGRESS"])).scalar() or 0
        data["my_reports"] = db.query(func.count(MedicalReport.id)).filter(
            MedicalReport.patient_id == user.id).scalar() or 0
        recent = db.query(Complaint).filter(
            Complaint.reporter_id == user.id).order_by(
            Complaint.created_at.desc()).limit(5).all()
        data["recent_complaints"] = [
            {"id": c.id, "title": c.title, "status": c.status,
             "category": c.category, "created_at": c.created_at}
            for c in recent
        ]
        return data

    if user.role == Role.CLINICIAN.value:
        data["total_reports"] = db.query(func.count(MedicalReport.id)).scalar() or 0
        data["high_urgency_reports"] = db.query(func.count(MedicalReport.id)).filter(
            MedicalReport.urgency.in_(["HIGH", "CRITICAL"])).scalar() or 0
        data["reports_last_7d"] = db.query(func.count(MedicalReport.id)).filter(
            MedicalReport.created_at >= now - timedelta(days=7)).scalar() or 0
        return data

    # civic / health / super admins
    data["total_complaints"] = db.query(func.count(Complaint.id)).scalar() or 0
    data["open_complaints"] = db.query(func.count(Complaint.id)).filter(
        Complaint.status.in_(["SUBMITTED", "ACKNOWLEDGED", "IN_PROGRESS"])).scalar() or 0
    data["resolved_complaints"] = db.query(func.count(Complaint.id)).filter(
        Complaint.status == "RESOLVED").scalar() or 0
    data["complaints_last_14d"] = db.query(func.count(Complaint.id)).filter(
        Complaint.created_at >= since).scalar() or 0
    data["status_breakdown"] = {
        str(k): int(v) for k, v in db.query(Complaint.status, func.count(Complaint.id))
        .group_by(Complaint.status).all()}
    data["category_breakdown"] = {
        str(k): int(v) for k, v in db.query(Complaint.category, func.count(Complaint.id))
        .group_by(Complaint.category).all()}
    data["urgency_breakdown"] = {
        str(k): int(v) for k, v in db.query(Complaint.urgency, func.count(Complaint.id))
        .group_by(Complaint.urgency).all()}
    data["trend"] = daily_counts(db, days=14)

    if user.role in (Role.HEALTH_ADMIN.value, Role.SUPER_ADMIN.value):
        data["total_reports"] = db.query(func.count(MedicalReport.id)).scalar() or 0
        data["reports_last_14d"] = db.query(func.count(MedicalReport.id)).filter(
            MedicalReport.created_at >= since).scalar() or 0
        data["urgency_reports"] = {
            str(k): int(v) for k, v in
            db.query(MedicalReport.urgency, func.count(MedicalReport.id))
            .group_by(MedicalReport.urgency).all()}
        data["open_alerts"] = db.query(func.count(Alert.id)).filter(
            Alert.status.in_(["NEW", "REVIEWING"])).scalar() or 0
        data["open_investigations"] = db.query(func.count(Investigation.id)).filter(
            Investigation.status.notin_(["CLOSED_RESOLVED", "CLOSED_NO_ACTION"])).scalar() or 0
        data["top_symptoms"] = _top_symptoms(db, limit=8)

    if user.role == Role.SUPER_ADMIN.value:
        data["total_users"] = db.query(func.count(User.id)).scalar() or 0
        data["active_users"] = db.query(func.count(User.id)).filter(
            User.is_active.is_(True)).scalar() or 0
        data["users_by_role"] = {
            str(k): int(v) for k, v in db.query(User.role, func.count(User.id))
            .group_by(User.role).all()}

    return data


def _top_symptoms(db: Session, limit: int = 8) -> list[dict]:
    """Aggregate canonical symptom frequency across reports (last 30 days)."""
    since = datetime.now(timezone.utc) - timedelta(days=30)
    counter: dict[str, int] = {}
    for (symptoms,) in db.query(MedicalReport.symptoms).filter(
            MedicalReport.created_at >= since):
        for s in symptoms or []:
            counter[s] = counter.get(s, 0) + 1
    ranked = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    return [{"symptom": k, "count": v} for k, v in ranked]
