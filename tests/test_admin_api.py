"""Audit logging + user management + system health tests."""

from __future__ import annotations


class TestAuditLog:
    def test_mutations_are_audited(self, app_client, citizen_headers, super_headers):
        r = app_client.post("/api/v1/complaints", json={
            "title": "Audit trail test near Greenhills",
            "text": "Footpath tiles near Greenhills park are broken and the road is "
                    "damaged after the cable laying work."},
            headers=citizen_headers)
        complaint_id = r.json()["complaint"]["id"]

        app_client.patch(f"/api/v1/complaints/{complaint_id}/status",
                         json={"status": "ACKNOWLEDGED"}, headers=super_headers)

        r = app_client.get("/api/v1/audit-logs?action=complaint.create",
                           headers=super_headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        r = app_client.get("/api/v1/audit-logs?action=complaint.status",
                           headers=super_headers)
        assert r.json()["total"] >= 1
        entry = r.json()["items"][0]
        assert entry["entity_type"] == "complaint"
        assert entry["actor_role"] in ("SUPER_ADMIN", "MUNICIPAL_ADMIN", "HEALTH_ADMIN")

    def test_audit_filters(self, app_client, super_headers):
        r = app_client.get("/api/v1/audit-logs?entity_type=complaint&page_size=5",
                           headers=super_headers)
        assert r.status_code == 200
        assert all(item["entity_type"] == "complaint" for item in r.json()["items"])


class TestUserManagement:
    def test_role_change_and_activation(self, app_client, super_headers):
        r = app_client.post("/api/v1/auth/register", json={
            "email": "promote@test.demo", "password": "PromoteTest!1",
            "full_name": "Promoted User", "role": "CITIZEN"})
        assert r.status_code == 201
        user_id = r.json()["user"]["id"]

        r = app_client.patch(f"/api/v1/users/{user_id}", json={"role": "CLINICIAN"},
                             headers=super_headers)
        assert r.status_code == 200
        assert r.json()["role"] == "CLINICIAN"

        r = app_client.patch(f"/api/v1/users/{user_id}", json={"is_active": False},
                             headers=super_headers)
        assert r.status_code == 200
        assert r.json()["is_active"] is False

        # deactivated user cannot authenticate
        r = app_client.post("/api/v1/auth/login", json={
            "email": "promote@test.demo", "password": "PromoteTest!1"})
        assert r.status_code == 403

    def test_cannot_demote_last_super_admin(self, app_client, super_headers):
        r = app_client.get("/api/v1/auth/me", headers=super_headers)
        me = r.json()
        r = app_client.patch(f"/api/v1/users/{me['id']}", json={"role": "CITIZEN"},
                             headers=super_headers)
        assert r.status_code == 422


class TestSystemHealth:
    def test_system_health(self, app_client, super_headers):
        r = app_client.get("/api/v1/system/health", headers=super_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["database"]["ok"] is True
        assert "nlp_pipeline" in body
        assert body["nlp_pipeline"]["classifier"] in ("tfidf-logreg", "hf-transformer")
        assert "document_storage" in body

    def test_health_endpoint_open(self, app_client):
        r = app_client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"

    def test_disclaimer_endpoint_open(self, app_client):
        r = app_client.get("/api/v1/disclaimer")
        assert r.status_code == 200
        assert "causation" in r.json()["disclaimer"]
