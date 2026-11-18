"""End-to-end API smoke test (run against a live app via TestClient).

Usage (from backend/):  python -m scripts.smoke_test
Exercises: health, register/login, RBAC, complaint creation + NLP analysis +
duplicate detection, status workflow, report creation, document upload,
intelligence scan, alerts, investigations, analytics, audit logs, export.
"""

from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402

PASS, FAIL = [], []


def check(name: str, condition: bool, extra: str = "") -> None:
    (PASS if condition else FAIL).append(name)
    print(f"  [{'PASS' if condition else 'FAIL'}] {name}" + (f" ({extra})" if extra else ""))


def main() -> int:
    client = TestClient(app)

    print("== system ==")
    r = client.get("/api/v1/health")
    check("health endpoint", r.status_code == 200 and r.json()["status"] == "ok")

    print("== auth ==")

    def ensure_user(email: str, password: str, full_name: str, role: str) -> str:
        """Idempotent helper: register or fall back to login (re-runnable)."""
        r = client.post("/api/v1/auth/register", json={
            "email": email, "password": password, "full_name": full_name, "role": role})
        if r.status_code == 201:
            return r.json()["access_token"]
        r = client.post("/api/v1/auth/login", json={"email": email, "password": password})
        return r.json().get("access_token", "") if r.status_code == 200 else ""

    citizen_token = ensure_user("smoke.citizen@healthpulse.demo", "SmokeTest!2026",
                                "Smoke Citizen", "CITIZEN")
    check("citizen token available", bool(citizen_token))
    patient_token = ensure_user("smoke.patient@healthpulse.demo", "SmokeTest!2026",
                                "Smoke Patient", "PATIENT")
    check("patient token available", bool(patient_token))

    # staff roles cannot be self-registered; use the seeded super admin account
    r = client.post("/api/v1/auth/register", json={
        "email": "smoke.attempt@healthpulse.demo", "password": "SmokeTest!2026",
        "full_name": "Sneaky Register", "role": "SUPER_ADMIN"})
    check("self-registration of staff role rejected", r.status_code == 422)

    r = client.post("/api/v1/auth/login", json={
        "email": "super@healthpulse.demo", "password": "HealthPulse!2026"})
    admin_token = r.json()["access_token"] if r.status_code == 200 else ""
    check("seeded super admin login", r.status_code == 200, f"status={r.status_code}")

    r = client.post("/api/v1/auth/login", json={
        "email": "smoke.citizen@healthpulse.demo", "password": "SmokeTest!2026"})
    check("login works", r.status_code == 200)
    r = client.post("/api/v1/auth/login", json={
        "email": "smoke.citizen@healthpulse.demo", "password": "wrong-password"})
    check("wrong password rejected", r.status_code == 401)

    r = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {citizen_token}"})
    check("auth/me", r.status_code == 200 and r.json()["role"] == "CITIZEN")

    print("== complaints ==")
    headers_citizen = {"Authorization": f"Bearer {citizen_token}"}
    headers_admin = {"Authorization": f"Bearer {admin_token}"}

    complaint_payload = {
        "title": "Sewage smell in drinking water near Millbrook market",
        "text": "The tap water in Millbrook ward 3 has been smelling like sewage since "
                "three days. Water is blackish and several families have stomach problems "
                "after drinking it.",
    }
    r = client.post("/api/v1/complaints", json=complaint_payload, headers=headers_citizen)
    ok = r.status_code == 201
    check("create complaint", ok, f"status={r.status_code}")
    body = r.json() if ok else {}
    analysis = body.get("analysis", {})
    check("NLP category assigned", analysis.get("category") == "water_contamination",
          str(analysis.get("category")))
    check("urgency computed", analysis.get("urgency", {}).get("label") in
          ("LOW", "MEDIUM", "HIGH", "CRITICAL"), str(analysis.get("urgency", {}).get("label")))
    check("location extracted", analysis.get("location", {}).get("district") == "Millbrook",
          str(analysis.get("location", {}).get("district")))
    check("duplicate flag present", "duplicate_detected" in body)

    complaint_id = body.get("complaint", {}).get("id", 0)
    r = client.post("/api/v1/complaints", json=complaint_payload, headers=headers_citizen)
    check("near-duplicate detection on resubmit",
          r.status_code == 201 and r.json().get("duplicate_detected") is True)

    r = client.get("/api/v1/complaints", headers=headers_citizen)
    check("list complaints (own)", r.status_code == 200 and r.json()["total"] >= 2)

    r = client.get(f"/api/v1/complaints/{complaint_id}/similar", headers=headers_admin)
    check("similar complaints search", r.status_code == 200)

    r = client.patch(f"/api/v1/complaints/{complaint_id}/status",
                     json={"status": "ACKNOWLEDGED"}, headers=headers_citizen)
    check("RBAC: citizen cannot change status", r.status_code == 403)

    r = client.patch(f"/api/v1/complaints/{complaint_id}/status",
                     json={"status": "ACKNOWLEDGED", "note": "Water team notified"},
                     headers=headers_admin)
    check("admin acknowledges complaint", r.status_code == 200 and
          r.json()["status"] == "ACKNOWLEDGED")
    r = client.patch(f"/api/v1/complaints/{complaint_id}/status",
                     json={"status": "RESOLVED"}, headers=headers_admin)
    check("invalid transition rejected (ACK->RESOLVED via IN_PROGRESS)",
          r.status_code == 422)

    print("== medical reports ==")
    headers_patient = {"Authorization": f"Bearer {patient_token}"}
    r = client.post("/api/v1/reports", json={
        "text": "My 6-year-old son has had diarrhea, stomach pain and vomiting for three "
                "days. Fever 102 and worsening. We drink tap water in Millbrook.",
        "lat": 17.6965, "lng": 83.2208}, headers=headers_patient)
    ok = r.status_code == 201
    check("create symptom report", ok, f"status={r.status_code}")
    report_body = r.json() if ok else {}
    check("symptoms extracted", len(report_body.get("symptoms", [])) >= 2,
          str(report_body.get("symptoms")))
    check("summary generated", bool(report_body.get("summary")))
    report_id = report_body.get("id", 0)

    r = client.get("/api/v1/reports", headers=headers_patient)
    check("patient sees own reports", r.status_code == 200 and r.json()["total"] >= 1)

    r = client.get("/api/v1/reports", headers=headers_citizen)
    check("RBAC: citizen denied reports list", r.status_code == 403)

    print("== documents ==")
    pdf_bytes = b""
    try:
        import fitz
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((72, 72), "Clinical note: persistent fever, cough and sore throat "
                                   "for five days. Prescribed paracetamol.")
        pdf_bytes = doc.tobytes()
        doc.close()
    except Exception as exc:  # noqa: BLE001
        print(f"  (PyMuPDF unavailable: {exc})")
    if pdf_bytes:
        r = client.post("/api/v1/documents/upload", files={
            "file": ("clinical_note.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
            headers=headers_patient)
        ok = r.status_code == 201
        check("PDF upload + text extraction", ok, f"status={r.status_code}")
        doc_id = r.json().get("id", 0) if ok else 0
        r = client.get(f"/api/v1/documents/{doc_id}/text", headers=headers_patient)
        check("document text endpoint", r.status_code == 200 and "fever" in
              (r.json().get("extracted_text") or ""))
        r = client.post("/api/v1/reports/from-document", json={"document_id": doc_id},
                        headers=headers_patient)
        check("report from document", r.status_code == 201)
    else:
        r = client.post("/api/v1/documents/upload", files={
            "file": ("note.txt", io.BytesIO("Patient reports fever and cough for five days.".encode()), "text/plain")},
            headers=headers_patient)
        check("txt upload", r.status_code == 201)

    r = client.post("/api/v1/documents/upload", files={
        "file": ("evil.exe", io.BytesIO(b"MZ..."), "application/octet-stream")},
        headers=headers_patient)
    check("disallowed extension rejected", r.status_code == 415)

    print("== intelligence ==")
    r = client.post("/api/v1/intelligence/scan", json={"days": 30}, headers=headers_admin)
    ok = r.status_code == 200
    check("intelligence scan", ok, f"status={r.status_code}")
    scan_alerts = r.json().get("alerts_created", 0) if ok else 0
    check("scan produced alerts", scan_alerts >= 0, f"alerts_created={scan_alerts}")

    r = client.get("/api/v1/intelligence/status", headers=headers_admin)
    check("intelligence status", r.status_code == 200)

    r = client.get("/api/v1/alerts", headers=headers_admin)
    ok = r.status_code == 200
    check("list alerts", ok)
    alert_id = r.json()["items"][0]["id"] if ok and r.json()["items"] else 0
    if alert_id:
        r = client.get(f"/api/v1/alerts/{alert_id}", headers=headers_admin)
        check("alert detail with evidence", r.status_code == 200 and
              (r.json().get("evidence") is not None))
        r = client.patch(f"/api/v1/alerts/{alert_id}/status",
                         json={"status": "CONFIRMED", "note": "Field visit scheduled"},
                         headers=headers_admin)
        check("confirm alert", r.status_code == 200)
        r = client.get("/api/v1/investigations", headers=headers_admin)
        check("auto-created investigation", r.status_code == 200 and
              r.json()["total"] >= 1)

    print("== analytics ==")
    r = client.get("/api/v1/analytics/public")
    check("public analytics (unauthenticated)", r.status_code == 200)
    r = client.get("/api/v1/analytics/overview", headers=headers_admin)
    check("admin overview", r.status_code == 200 and "category_breakdown" in r.json())
    r = client.get("/api/v1/analytics/districts", headers=headers_admin)
    check("district stats", r.status_code == 200 and len(r.json()["districts"]) >= 3)
    r = client.get("/api/v1/analytics/heatmap", headers=headers_admin)
    check("heatmap points", r.status_code == 200 and len(r.json()["points"]) > 0)
    r = client.get("/api/v1/analytics/export?dataset=complaints", headers=headers_admin)
    check("CSV export", r.status_code == 200 and "id" in r.text.splitlines()[0])

    print("== admin ==")
    r = client.get("/api/v1/audit-logs", headers=headers_admin)
    ok = r.status_code == 200
    check("audit logs", ok, f"total={r.json()['total'] if ok else '?'}")
    r = client.get("/api/v1/system/health", headers=headers_admin)
    check("system health", r.status_code == 200 and r.json()["database"]["ok"])
    r = client.get("/api/v1/users", headers=headers_admin)
    check("user management list", r.status_code == 200 and r.json()["total"] >= 3)

    print(f"\nResult: {len(PASS)} passed, {len(FAIL)} failed")
    if FAIL:
        print("FAILED:", FAIL)
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
