"""Medical report API + privacy tests."""

from __future__ import annotations

GI_TEXT = ("My 6-year-old son has had diarrhea, stomach pain and vomiting for three "
           "days. Fever is 102 and worsening. He is very weak. We drink the tap water "
           "in Millbrook.")


class TestReportCreation:
    def test_create_with_extraction_and_summary(self, app_client, patient_headers):
        r = app_client.post("/api/v1/reports", json={
            "text": GI_TEXT, "lat": 17.6965, "lng": 83.2208}, headers=patient_headers)
        assert r.status_code == 201
        body = r.json()
        assert len(body["symptoms"]) >= 3
        assert "diarrhea" in body["symptoms"]
        assert "gastrointestinal" in body["symptom_categories"]
        assert body["urgency"] in ("MEDIUM", "HIGH", "CRITICAL")
        assert body["summary"]
        assert body["digest"] and "not a diagnosis" in body["digest"]
        assert body["entity_count"] >= 3
        assert body["patient_alias"]

    def test_patient_sees_only_own_reports(self, app_client, patient_headers,
                                           super_headers):
        r = app_client.post("/api/v1/reports", json={
            "text": "Itching and red rash on arms since three days after swimming in "
                    "the stagnant water near our lane in Riverside."},
            headers=patient_headers)
        assert r.status_code == 201
        my_id = r.json()["id"]

        r = app_client.get("/api/v1/reports?page_size=100", headers=patient_headers)
        assert r.status_code == 200
        ids = {item["id"] for item in r.json()["items"]}
        assert my_id in ids
        # all visible reports belong to this patient (no cross-patient leakage)
        patient_alias_ids = {item["patient_id"] for item in r.json()["items"]}
        assert len(patient_alias_ids) == 1

    def test_civic_admin_has_no_access_to_reports(self, app_client, municipal_headers):
        r = app_client.get("/api/v1/reports", headers=municipal_headers)
        assert r.status_code == 403

    def test_clinician_reads_but_patient_privacy_kept(self, app_client,
                                                      clinician_headers):
        r = app_client.get("/api/v1/reports?page_size=10", headers=clinician_headers)
        assert r.status_code == 200
        for item in r.json()["items"]:
            assert item["patient_id"] is None  # identity stripped for clinicians
            assert item["patient_alias"]

    def test_summarize_endpoint(self, app_client, patient_headers):
        r = app_client.post("/api/v1/reports", json={
            "text": "Persistent fever with headache and body ache for five days, "
                    "chills at night, doctor suspects dengue because of mosquitoes."},
            headers=patient_headers)
        report_id = r.json()["id"]
        r = app_client.post(f"/api/v1/reports/{report_id}/summarize", headers=patient_headers)
        assert r.status_code == 200
        assert r.json()["summary"]
