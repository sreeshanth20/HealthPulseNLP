"""Complaint API tests: NLP analysis, duplicates, lifecycle, scoping, pagination."""

from __future__ import annotations

WATER_TEXT = ("The tap water in Millbrook ward 3 has been smelling like sewage since "
              "three days. Water is blackish and dirty. Several families have stomach "
              "problems after drinking it. Please test the pipeline near Millbrook market.")


class TestComplaintCreation:
    def test_create_with_full_analysis(self, app_client, citizen_headers):
        r = app_client.post("/api/v1/complaints", json={
            "title": "Sewage smell in Millbrook drinking water",
            "text": WATER_TEXT}, headers=citizen_headers)
        assert r.status_code == 201
        body = r.json()
        analysis = body["analysis"]
        assert analysis["category"] == "water_contamination"
        assert analysis["category_confidence"] > 0.5
        assert analysis["urgency"]["label"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")
        assert analysis["urgency"]["reasons"]
        assert analysis["location"]["district"] == "Millbrook"
        assert analysis["language"] == "en"
        complaint = body["complaint"]
        assert complaint["category"] == "water_contamination"
        assert complaint["status"] == "SUBMITTED"
        assert analysis["embedding"]  # embedding stored for similarity
        assert complaint["lat"] is not None  # geocoded from text

    def test_duplicate_detection_on_resubmit(self, app_client, citizen_headers):
        payload = {"title": "Sewage smell in Millbrook drinking water",
                   "text": WATER_TEXT}
        first = app_client.post("/api/v1/complaints", json=payload, headers=citizen_headers)
        assert first.status_code == 201
        second = app_client.post("/api/v1/complaints", json=payload, headers=citizen_headers)
        assert second.status_code == 201
        body = second.json()
        assert body["duplicate_detected"] is True
        candidates = body["duplicate_candidates"]
        assert candidates and candidates[0]["score"] > 0.7

    def test_validation_rejects_short_text(self, app_client, citizen_headers):
        r = app_client.post("/api/v1/complaints", json={
            "title": "Too short", "text": "water bad"}, headers=citizen_headers)
        assert r.status_code == 422


class TestComplaintWorkflow:
    def _create(self, app_client, headers):
        r = app_client.post("/api/v1/complaints", json={
            "title": "Pothole workflow test near Old Town school",
            "text": "Deep pothole in front of Old Town school gate. Dangerous for "
                    "children, several two-wheeler accidents reported this week."},
            headers=headers)
        return r.json()["complaint"]["id"]

    def test_status_transitions_enforced(self, app_client, citizen_headers,
                                         municipal_headers):
        complaint_id = self._create(app_client, citizen_headers)
        # SUBMITTED -> RESOLVED is invalid (must pass through the graph)
        r = app_client.patch(f"/api/v1/complaints/{complaint_id}/status",
                             json={"status": "RESOLVED"}, headers=municipal_headers)
        assert r.status_code == 422
        # valid path
        for status in ("ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED"):
            r = app_client.patch(f"/api/v1/complaints/{complaint_id}/status",
                                 json={"status": status}, headers=municipal_headers)
            assert r.status_code == 200
            assert r.json()["status"] == status
        # resolved_at stamped
        assert r.json()["resolved_at"] is not None
        # terminal state rejects further transitions
        r = app_client.patch(f"/api/v1/complaints/{complaint_id}/status",
                             json={"status": "IN_PROGRESS"}, headers=municipal_headers)
        assert r.status_code == 422

    def test_mark_duplicate(self, app_client, citizen_headers, municipal_headers):
        payload = {"title": "Repeated garbage complaint",
                   "text": "Garbage has not been collected in Eastfields for two weeks. "
                           "Bins are overflowing and the stench is unbearable."}
        first = app_client.post("/api/v1/complaints", json=payload, headers=citizen_headers)
        second = app_client.post("/api/v1/complaints", json=payload, headers=citizen_headers)
        dup_id = second.json()["complaint"]["id"]
        original_id = first.json()["complaint"]["id"]
        r = app_client.post(f"/api/v1/complaints/{dup_id}/mark-duplicate",
                            json={"original_id": original_id}, headers=municipal_headers)
        assert r.status_code == 200
        assert r.json()["duplicate_of_id"] == original_id

    def test_similar_complaints_endpoint(self, app_client, citizen_headers,
                                         municipal_headers):
        complaint_id = self._create(app_client, citizen_headers)
        r = app_client.get(f"/api/v1/complaints/{complaint_id}/similar",
                           headers=municipal_headers)
        assert r.status_code == 200
        assert "similar" in r.json()


class TestScopingAndPagination:
    def test_citizen_sees_only_own_complaints(self, app_client, citizen_headers,
                                              municipal_headers):
        # citizen creates one
        r = app_client.post("/api/v1/complaints", json={
            "title": "Ownership scoping check near Southbay",
            "text": "Drain is choked in Southbay lane 2 with stagnant water for a week, "
                    "terrible smell all day."}, headers=citizen_headers)
        assert r.status_code == 201
        # municipal admin creates one under its own account
        r = app_client.post("/api/v1/complaints", json={
            "title": "Admin-created complaint near Southbay",
            "text": "Stray dogs near Southbay beach road have become aggressive, two "
                    "children were chased yesterday evening."}, headers=municipal_headers)
        assert r.status_code == 201

        r = app_client.get("/api/v1/complaints?page_size=100", headers=citizen_headers)
        assert r.status_code == 200
        assert all(item["reporter_id"] is not None for item in r.json()["items"])
        # citizen's own rows only: reporter ids must be consistent
        reporter_ids = {item["reporter_id"] for item in r.json()["items"]}
        assert len(reporter_ids) == 1

        r = app_client.get("/api/v1/complaints?page_size=100", headers=municipal_headers)
        assert r.status_code == 200
        assert len({item["reporter_id"] for item in r.json()["items"]}) >= 2

    def test_filters_and_pagination_shape(self, app_client, municipal_headers):
        r = app_client.get("/api/v1/complaints?category=water_contamination&page=1&page_size=5",
                           headers=municipal_headers)
        assert r.status_code == 200
        body = r.json()
        assert {"items", "total", "page", "page_size", "pages"} <= set(body)
        assert len(body["items"]) <= 5
        assert all(i["category"] == "water_contamination" for i in body["items"])

    def test_geo_endpoint_requires_staff(self, app_client, citizen_headers,
                                         municipal_headers):
        assert app_client.get("/api/v1/complaints/geo", headers=citizen_headers).status_code == 403
        r = app_client.get("/api/v1/complaints/geo", headers=municipal_headers)
        assert r.status_code == 200
        assert "points" in r.json()
