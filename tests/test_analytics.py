"""Analytics endpoint tests (role-appropriate aggregates)."""

from __future__ import annotations


class TestAnalytics:
    def test_public_stats_no_auth(self, app_client):
        r = app_client.get("/api/v1/analytics/public")
        assert r.status_code == 200
        body = r.json()
        assert "total_complaints" in body
        assert "categories" in body

    def test_overview_role_shapes(self, app_client, citizen_headers, municipal_headers,
                                  health_headers, super_headers):
        r = app_client.get("/api/v1/analytics/overview", headers=citizen_headers)
        assert r.status_code == 200
        assert "my_complaints" in r.json()

        r = app_client.get("/api/v1/analytics/overview", headers=municipal_headers)
        assert r.status_code == 200
        body = r.json()
        assert "status_breakdown" in body and "category_breakdown" in body
        assert "trend" in body

        r = app_client.get("/api/v1/analytics/overview", headers=health_headers)
        body = r.json()
        assert "total_reports" in body and "open_alerts" in body

        r = app_client.get("/api/v1/analytics/overview", headers=super_headers)
        body = r.json()
        assert "total_users" in body and "users_by_role" in body

    def test_trends_and_districts_staff_only(self, app_client, citizen_headers,
                                             municipal_headers):
        assert app_client.get("/api/v1/analytics/trends",
                              headers=citizen_headers).status_code == 403
        r = app_client.get("/api/v1/analytics/trends?days=14", headers=municipal_headers)
        assert r.status_code == 200
        assert len(r.json()["points"]) == 14

        r = app_client.get("/api/v1/analytics/districts", headers=municipal_headers)
        assert r.status_code == 200
        districts = r.json()["districts"]
        assert districts
        assert all({"district", "complaints", "reports"} <= set(d) for d in districts)

    def test_heatmap_staff_only(self, app_client, municipal_headers):
        r = app_client.get("/api/v1/analytics/heatmap", headers=municipal_headers)
        assert r.status_code == 200
        points = r.json()["points"]
        assert points
        assert all({"lat", "lng", "weight", "kind"} <= set(p) for p in points)

    def test_export_csv_deidentified_reports(self, app_client, health_headers):
        r = app_client.get("/api/v1/analytics/export?dataset=reports",
                           headers=health_headers)
        assert r.status_code == 200
        header_row = r.text.splitlines()[0]
        assert "patient" not in header_row.lower().replace("deidentified", "")
        assert "text" not in header_row.lower()

    def test_export_forbidden_for_citizen(self, app_client, citizen_headers):
        r = app_client.get("/api/v1/analytics/export?dataset=complaints",
                           headers=citizen_headers)
        assert r.status_code == 403
