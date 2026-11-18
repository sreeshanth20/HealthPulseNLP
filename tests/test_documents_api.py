"""Document upload / extraction / security tests."""

from __future__ import annotations

import io


def _make_pdf(text: str) -> bytes:
    import fitz

    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    data = doc.tobytes()
    doc.close()
    return data


class TestUploadAndExtraction:
    def test_pdf_upload_and_text_extraction(self, app_client, patient_headers):
        pdf = _make_pdf("Clinical note: persistent fever, cough and sore throat for "
                        "five days. Prescribed paracetamol and rest.")
        r = app_client.post("/api/v1/documents/upload", files={
            "file": ("note.pdf", io.BytesIO(pdf), "application/pdf")},
            headers=patient_headers)
        assert r.status_code == 201
        body = r.json()
        assert body["extraction_status"] == "EXTRACTED"
        assert body["pages"] == 1
        assert body["size_bytes"] > 0

        r = app_client.get(f"/api/v1/documents/{body['id']}/text", headers=patient_headers)
        assert r.status_code == 200
        assert "fever" in r.json()["extracted_text"]

    def test_txt_upload(self, app_client, patient_headers):
        r = app_client.post("/api/v1/documents/upload", files={
            "file": ("summary.txt", io.BytesIO("Patient has fever and cough for four days.".encode()),
                     "text/plain")}, headers=patient_headers)
        assert r.status_code == 201
        assert r.json()["extraction_status"] == "EXTRACTED"

    def test_report_from_document(self, app_client, patient_headers):
        pdf = _make_pdf("Follow-up: patient recovering from typhoid symptoms, fever "
                        "resolved, stomach pain mild. Continue ORS and rest.")
        r = app_client.post("/api/v1/documents/upload", files={
            "file": ("followup.pdf", io.BytesIO(pdf), "application/pdf")},
            headers=patient_headers)
        doc_id = r.json()["id"]
        r = app_client.post("/api/v1/reports/from-document", json={"document_id": doc_id},
                            headers=patient_headers)
        assert r.status_code == 201
        assert r.json()["document_id"] == doc_id
        assert r.json()["symptoms"]


class TestUploadSecurity:
    def test_disallowed_extension_rejected(self, app_client, patient_headers):
        r = app_client.post("/api/v1/documents/upload", files={
            "file": ("payload.exe", io.BytesIO(b"MZfake"), "application/octet-stream")},
            headers=patient_headers)
        assert r.status_code == 415

    def test_empty_file_rejected(self, app_client, patient_headers):
        r = app_client.post("/api/v1/documents/upload", files={
            "file": ("empty.txt", io.BytesIO(b""), "text/plain")},
            headers=patient_headers)
        assert r.status_code == 422

    def test_path_traversal_in_filename_neutralized(self, app_client, patient_headers):
        r = app_client.post("/api/v1/documents/upload", files={
            "file": ("../../etc/passwd.txt", io.BytesIO(b"safe content here"),
                     "text/plain")}, headers=patient_headers)
        assert r.status_code == 201
        assert ".." not in r.json()["filename"]
        assert "/" not in r.json()["filename"]

    def test_citizen_cannot_upload(self, app_client, citizen_headers):
        r = app_client.post("/api/v1/documents/upload", files={
            "file": ("x.txt", io.BytesIO(b"data"), "text/plain")},
            headers=citizen_headers)
        assert r.status_code == 403

    def test_owner_only_deletion(self, app_client, patient_headers, super_headers,
                                 clinician_headers):
        r = app_client.post("/api/v1/documents/upload", files={
            "file": ("delete_me.txt", io.BytesIO(b"temporary document"),
                     "text/plain")}, headers=patient_headers)
        doc_id = r.json()["id"]
        # clinician can read but not delete
        assert app_client.get(f"/api/v1/documents/{doc_id}",
                              headers=clinician_headers).status_code == 200
        assert app_client.delete(f"/api/v1/documents/{doc_id}",
                                 headers=clinician_headers).status_code == 403
        # super admin can delete
        assert app_client.delete(f"/api/v1/documents/{doc_id}",
                                 headers=super_headers).status_code == 204
