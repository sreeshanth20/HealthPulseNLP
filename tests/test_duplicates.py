"""Duplicate detection + semantic search tests."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from ml.inference.pipeline import get_pipeline
from ml.similarity.duplicate_detector import jaccard

NOW = datetime.now(timezone.utc)


def _corpus():
    return [
        {"id": 1, "text": "Tap water in Millbrook smells like sewage, blackish water",
         "category": "water_contamination", "district": "Millbrook",
         "lat": 17.6968, "lng": 83.2204, "created_at": NOW - timedelta(days=3)},
        {"id": 2, "text": "Deep pothole near Old Town school, accidents reported",
         "category": "road_infrastructure", "district": "Old Town",
         "lat": 17.7032, "lng": 83.2091, "created_at": NOW - timedelta(days=1)},
        {"id": 3, "text": "Water from tap smells like sewage in Millbrook, blackish",
         "category": "water_contamination", "district": "Millbrook",
         "lat": 17.6970, "lng": 83.2201, "created_at": NOW - timedelta(days=2)},
        {"id": 4, "text": "Street light dead near Northgate market, dark street",
         "category": "street_lighting", "district": "Northgate",
         "lat": 17.7120, "lng": 83.2188, "created_at": NOW - timedelta(days=5)},
    ]


class TestDuplicateDetection:
    def test_near_duplicate_flagged(self):
        detector = get_pipeline().detector
        results = detector.find_duplicates(
            "Tap water in Millbrook smells like sewage, water is blackish and dirty",
            _corpus(), category="water_contamination", lat=17.6968, lng=83.2204,
            created_at=NOW)
        top = results[0]
        assert top["id"] in (1, 3)
        assert top["is_duplicate"] is True
        assert top["signals"]["category_match"] is True
        assert top["signals"]["distance_km"] < 1.0

    def test_different_topic_not_flagged(self):
        detector = get_pipeline().detector
        results = detector.find_duplicates(
            "Garbage truck has not come to Eastfields for two weeks, bins overflowing",
            _corpus(), category="garbage_sanitation", lat=17.6849, lng=83.2318,
            created_at=NOW)
        assert all(r["is_duplicate"] is False for r in results)

    def test_candidates_sorted_by_score(self):
        detector = get_pipeline().detector
        results = detector.find_duplicates(
            "Water smells like sewage in Millbrook", _corpus(),
            category="water_contamination", lat=17.6968, lng=83.2204, created_at=NOW)
        scores = [r["score"] for r in results]
        assert scores == sorted(scores, reverse=True)

    def test_jaccard(self):
        assert jaccard({"a", "b", "c"}, {"a", "b", "c"}) == 1.0
        assert jaccard({"a", "b"}, {"c", "d"}) == 0.0


class TestSemanticSearch:
    def test_top_k_relevant_first(self):
        search = get_pipeline().search
        results = search.top_k("sewage smell in drinking water", _corpus(), k=3)
        assert results
        assert results[0]["id"] in (1, 3)

    def test_empty_corpus(self):
        search = get_pipeline().search
        assert search.top_k("anything", [], k=3) == []
