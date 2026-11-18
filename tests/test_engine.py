"""Cross-domain intelligence engine tests (synthetic fixtures only)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ml.config import DISCLAIMER
from ml.inference.pipeline import get_pipeline

NOW = datetime(2026, 11, 10, 12, 0, 0, tzinfo=timezone.utc)
MILLBROOK = (17.6968, 83.2204)


def _complaint(i: int, text: str, category: str, days_ago: int = 8) -> dict:
    return {"id": 100 + i, "text": text, "category": category,
            "district": "Millbrook", "lat": MILLBROOK[0], "lng": MILLBROOK[1],
            "created_at": NOW - timedelta(days=days_ago)}


def _report(i: int, text: str, symptoms: list[str], categories: list[str],
            days_ago: int = 7) -> dict:
    return {"id": 200 + i, "text": text, "symptoms": symptoms,
            "symptom_categories": categories, "district": "Millbrook",
            "lat": MILLBROOK[0] + 0.001, "lng": MILLBROOK[1] + 0.001,
            "created_at": NOW - timedelta(days=days_ago)}


class TestCrossDomainScan:
    def test_water_complaints_plus_gi_reports_generate_alert(self):
        pipeline = get_pipeline()
        complaints = [
            _complaint(1, "Tap water smells like sewage in Millbrook, blackish water, "
                          "families have stomach problems", "water_contamination"),
            _complaint(2, "Borewell water muddy and worm-infested near Millbrook market",
                       "water_contamination"),
        ]
        reports = [
            _report(1, "Son has diarrhea, stomach pain and vomiting for three days "
                       "after drinking tap water", ["diarrhea", "stomach_pain", "vomiting"],
                    ["gastrointestinal"]),
            _report(2, "Family suffering loose motions and stomach cramps, admitted "
                       "with dehydration", ["diarrhea", "dehydration"],
                    ["gastrointestinal"]),
        ]
        result = pipeline.scan_cross_domain(complaints, reports)
        assert result["stats"]["complaints_scanned"] == 2
        assert result["stats"]["reports_scanned"] == 2
        assert result["alerts"], "expected at least one cross-domain alert"
        alert = result["alerts"][0]
        assert alert["type"] == "CROSS_DOMAIN_CLUSTER"
        assert alert["districts"] == ["Millbrook"]
        assert alert["n_supporting_pairs"] >= 1
        assert alert["score"] > 0.5
        # evidence is explainable: every pair carries its contribution breakdown
        evidence = alert["evidence"][0]
        for key in ("association_score", "semantic_similarity", "spatial_proximity",
                    "temporal_proximity", "theme_match", "weights"):
            assert key in evidence
        # disclaimer present in result
        assert "causation" in result["disclaimer"].lower()
        assert "diagnos" in result["disclaimer"].lower()

    def test_unrelated_records_do_not_alert(self):
        pipeline = get_pipeline()
        complaints = [
            _complaint(1, "Loudspeakers till midnight near Northgate community hall",
                       "noise_pollution", days_ago=1),
        ]
        reports = [
            _report(1, "Mild cold and sneezing for two days", ["cold"],
                    ["respiratory"], days_ago=1),
        ]
        # different district, unrelated theme
        complaints[0]["district"] = "Northgate"
        complaints[0]["lat"], complaints[0]["lng"] = 17.7120, 83.2188
        result = pipeline.scan_cross_domain(complaints, reports)
        clusters = [a for a in result["alerts"] if a["type"] == "CROSS_DOMAIN_CLUSTER"]
        assert clusters == []

    def test_temporal_window_enforced(self):
        pipeline = get_pipeline()
        complaints = [_complaint(1, "Sewage overflow near Millbrook park",
                                 "drainage_sewage", days_ago=40)]
        reports = [_report(1, "Diarrhea outbreak in our building",
                           ["diarrhea"], ["gastrointestinal"], days_ago=1)]
        result = pipeline.scan_cross_domain(complaints, reports)
        assert result["stats"]["candidate_pairs"] == 0
        assert not result["alerts"]

    def test_temporal_anomaly_alert_from_series(self):
        pipeline = get_pipeline()
        dates = [(datetime(2026, 10, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
                 for i in range(25)]
        counts = [4] * 25
        counts[22] = 26  # spike
        result = pipeline.scan_cross_domain([], [], daily_series=[
            {"key": "Millbrook", "points": list(zip(dates, counts))}])
        anomalies = [a for a in result["alerts"] if a["type"] == "TEMPORAL_ANOMALY"]
        assert anomalies
        assert anomalies[0]["evidence"][0]["observed"] == 26

    def test_disclaimer_always_present(self):
        pipeline = get_pipeline()
        result = pipeline.scan_cross_domain([], [])
        assert result["disclaimer"] == DISCLAIMER
