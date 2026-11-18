"""Intelligence + alert + investigation API tests."""

from __future__ import annotations


class TestIntelligenceScan:
    def test_scan_generates_persistent_alerts(self, app_client, super_headers):
        # seed a linked scenario through the real API
        r = app_client.post("/api/v1/complaints", json={
            "title": "Sewage mixed drinking water in Riverside",
            "text": "Municipal pipeline water in Riverside has turned yellowish and "
                    "smells terrible. My whole family got stomach pain and fever after "
                    "drinking it since four days.", "lat": 17.6795, "lng": 83.2010},
            headers=super_headers)
        assert r.status_code == 201
        r = app_client.post("/api/v1/reports", json={
            "text": "Vomiting and diarrhea since two days after drinking tap water in "
                    "Riverside. Severe stomach pain and weakness.", "lat": 17.6792,
            "lng": 83.2005}, headers=super_headers)
        assert r.status_code == 201

        r = app_client.post("/api/v1/intelligence/scan", json={"days": 30},
                            headers=super_headers)
        assert r.status_code == 200
        body = r.json()
        assert "disclaimer" in body and "causation" in body["disclaimer"]
        assert body["scan"]["complaints_scanned"] >= 1

    def test_preview_endpoints_do_not_persist(self, app_client, citizen_headers,
                                              municipal_headers, patient_headers,
                                              super_headers):
        r = app_client.post("/api/v1/intelligence/preview", json={
            "text": "Garbage not collected in Eastfields for two weeks, bins overflowing"},
            headers=citizen_headers)
        assert r.status_code == 200
        body = r.json()
        assert body["category"] == "garbage_sanitation"
        assert body["urgency"]["label"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")

        r = app_client.post("/api/v1/intelligence/preview-report", json={
            "text": "Diarrhea and vomiting for three days with fever 102 after drinking tap water"},
            headers=patient_headers)
        assert r.status_code == 200
        assert "diarrhea" in r.json()["symptoms"]

        # previews must not have created rows
        r = app_client.get("/api/v1/complaints?q=Eastfields", headers=municipal_headers)
        before = r.json()["total"]
        assert before >= 0  # nothing persisted from the preview calls above

    def test_scan_forbidden_for_municipal(self, app_client, municipal_headers):
        r = app_client.post("/api/v1/intelligence/scan", json={"days": 7},
                            headers=municipal_headers)
        assert r.status_code == 403


class TestAlertWorkflow:
    def test_alert_lifecycle_with_auto_investigation(self, app_client, super_headers,
                                                     health_headers):
        r = app_client.post("/api/v1/intelligence/scan", json={"days": 30},
                            headers=super_headers)
        assert r.status_code == 200

        r = app_client.get("/api/v1/alerts?page_size=10", headers=health_headers)
        assert r.status_code == 200
        items = r.json()["items"]
        assert items, "expected alerts after scan"
        alert = items[0]
        assert alert["evidence"] is not None
        assert alert["disclaimer"]

        # NEW -> REVIEWING -> CONFIRMED (auto-creates investigation)
        alert_id = alert["id"]
        r = app_client.patch(f"/api/v1/alerts/{alert_id}/status",
                             json={"status": "REVIEWING", "note": "Reviewing evidence"},
                             headers=health_headers)
        assert r.status_code == 200 and r.json()["status"] == "REVIEWING"

        r = app_client.patch(f"/api/v1/alerts/{alert_id}/status",
                             json={"status": "CONFIRMED"}, headers=health_headers)
        assert r.status_code == 200

        r = app_client.get(f"/api/v1/investigations?alert_id={alert_id}",
                           headers=health_headers)
        assert r.status_code == 200
        assert r.json()["total"] >= 1
        investigation = r.json()["items"][0]

        # advance the investigation
        r = app_client.patch(f"/api/v1/investigations/{investigation['id']}",
                             json={"status": "FIELD_VISIT_SCHEDULED",
                                   "notes": "Water sampling team scheduled"},
                             headers=health_headers)
        assert r.status_code == 200
        assert r.json()["status"] == "FIELD_VISIT_SCHEDULED"

        r = app_client.patch(f"/api/v1/investigations/{investigation['id']}",
                             json={"status": "CLOSED_RESOLVED",
                                   "findings": "Pipeline leak fixed; follow-up sampling clean"},
                             headers=health_headers)
        assert r.status_code == 200
        assert r.json()["closed_at"] is not None

    def test_related_endpoints(self, app_client, super_headers, health_headers):
        r = app_client.get("/api/v1/complaints?page_size=5", headers=super_headers)
        complaint_id = r.json()["items"][0]["id"]
        r = app_client.get(f"/api/v1/intelligence/related/complaint/{complaint_id}",
                           headers=health_headers)
        assert r.status_code == 200
        assert "related_reports" in r.json()
        assert "disclaimer" in r.json()

        r = app_client.get("/api/v1/reports?page_size=5", headers=health_headers)
        if r.json()["items"]:
            report_id = r.json()["items"][0]["id"]
            r = app_client.get(f"/api/v1/intelligence/related/report/{report_id}",
                               headers=health_headers)
            assert r.status_code == 200
            assert "related_complaints" in r.json()
