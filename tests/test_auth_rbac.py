"""Auth + RBAC tests."""

from __future__ import annotations

TEST_PASSWORD = "TestPass!2026"


class TestRegistrationAndLogin:
    def test_register_and_login_roundtrip(self, app_client):
        r = app_client.post("/api/v1/auth/register", json={
            "email": "roundtrip@test.demo", "password": "RoundTrip!1",
            "full_name": "Round Trip", "role": "CITIZEN"})
        assert r.status_code == 201
        token = r.json()["access_token"]
        assert r.json()["user"]["role"] == "CITIZEN"

        r = app_client.post("/api/v1/auth/login", json={
            "email": "roundtrip@test.demo", "password": "RoundTrip!1"})
        assert r.status_code == 200
        assert r.json()["access_token"]

        r = app_client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert r.json()["email"] == "roundtrip@test.demo"

    def test_duplicate_email_rejected(self, app_client):
        payload = {"email": "dupe@test.demo", "password": "DupeTest!1",
                   "full_name": "Dupe", "role": "CITIZEN"}
        assert app_client.post("/api/v1/auth/register", json=payload).status_code == 201
        assert app_client.post("/api/v1/auth/register", json=payload).status_code == 409

    def test_wrong_password_rejected(self, app_client):
        r = app_client.post("/api/v1/auth/login", json={
            "email": "citizen@test.demo", "password": "nope-nope"})
        assert r.status_code == 401

    def test_short_password_rejected(self, app_client):
        r = app_client.post("/api/v1/auth/register", json={
            "email": "shortpw@test.demo", "password": "short",
            "full_name": "Short PW", "role": "CITIZEN"})
        assert r.status_code == 422

    def test_invalid_role_rejected_at_registration(self, app_client):
        r = app_client.post("/api/v1/auth/register", json={
            "email": "sneaky@test.demo", "password": "SneakyTest!1",
            "full_name": "Sneaky", "role": "SUPER_ADMIN"})
        assert r.status_code == 422

    def test_unauthenticated_access_blocked(self, app_client):
        assert app_client.get("/api/v1/auth/me").status_code == 401
        assert app_client.get("/api/v1/complaints").status_code == 401

    def test_garbage_token_blocked(self, app_client):
        r = app_client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
        assert r.status_code == 401


class TestRBAC:
    def test_citizen_cannot_update_complaint_status(self, app_client, citizen_headers,
                                                    municipal_headers):
        r = app_client.post("/api/v1/complaints", json={
            "title": "RBAC test streetlight broken",
            "text": "Street lights are not working near Northgate for two weeks. "
                    "The stretch is dark at night and unsafe."},
            headers=citizen_headers)
        assert r.status_code == 201
        complaint_id = r.json()["complaint"]["id"]

        r = app_client.patch(f"/api/v1/complaints/{complaint_id}/status",
                             json={"status": "ACKNOWLEDGED"}, headers=citizen_headers)
        assert r.status_code == 403

        r = app_client.patch(f"/api/v1/complaints/{complaint_id}/status",
                             json={"status": "ACKNOWLEDGED"}, headers=municipal_headers)
        assert r.status_code == 200

    def test_citizen_cannot_run_intelligence_scan(self, app_client, citizen_headers):
        r = app_client.post("/api/v1/intelligence/scan", json={"days": 30},
                            headers=citizen_headers)
        assert r.status_code == 403

    def test_citizen_cannot_view_alerts(self, app_client, citizen_headers):
        r = app_client.get("/api/v1/alerts", headers=citizen_headers)
        assert r.status_code == 403

    def test_citizen_cannot_list_audit_logs(self, app_client, citizen_headers):
        r = app_client.get("/api/v1/audit-logs", headers=citizen_headers)
        assert r.status_code == 403

    def test_municipal_cannot_list_audit_logs(self, app_client, municipal_headers):
        r = app_client.get("/api/v1/audit-logs", headers=municipal_headers)
        assert r.status_code == 403

    def test_clinician_can_view_reports(self, app_client, clinician_headers,
                                        patient_headers):
        r = app_client.post("/api/v1/reports", json={
            "text": "Patient reports mild fever and cough for two days, resting at home."},
            headers=patient_headers)
        assert r.status_code == 201
        r = app_client.get("/api/v1/reports", headers=clinician_headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1

    def test_patient_cannot_access_user_management(self, app_client, patient_headers):
        r = app_client.get("/api/v1/users", headers=patient_headers)
        assert r.status_code == 403
