"""Unified NLP inference pipeline (facade over all ml subpackages).

The backend calls this single class; tests exercise it directly. Heavy
components load lazily and degrade gracefully:

    HealthPulseNLP().health()
    -> {"embedder": "hashing-v1", "classifier": "tfidf-logreg",
        "ner": "lexicon-v1", "transformers_available": false, ...}
"""

from __future__ import annotations

import logging
import threading
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class HealthPulseNLP:
    def __init__(self) -> None:
        self._embedder = None
        self._classifier = None
        self._ner = None
        self._detector = None
        self._search = None
        self._engine = None
        self._lock = threading.Lock()

    # ------------------------------------------------------------------ #
    # lazy singletons                                                      #
    # ------------------------------------------------------------------ #
    @property
    def embedder(self):
        if self._embedder is None:
            from ml.embeddings.embedder import get_embedder

            self._embedder = get_embedder()
        return self._embedder

    @property
    def classifier(self):
        if self._classifier is None:
            from ml.classification.complaint_classifier import ComplaintClassifier

            self._classifier = ComplaintClassifier()
        return self._classifier

    @property
    def ner(self):
        if self._ner is None:
            from ml.extraction.medical_ner import MedicalNER

            self._ner = MedicalNER()
        return self._ner

    @property
    def detector(self):
        if self._detector is None:
            from ml.similarity.duplicate_detector import DuplicateDetector

            self._detector = DuplicateDetector(self.embedder)
        return self._detector

    @property
    def search(self):
        if self._search is None:
            from ml.similarity.duplicate_detector import SemanticSearch

            self._search = SemanticSearch(self.embedder)
        return self._search

    @property
    def engine(self):
        if self._engine is None:
            from ml.crossdomain.engine import CrossDomainEngine

            self._engine = CrossDomainEngine(self.embedder)
        return self._engine

    # ------------------------------------------------------------------ #
    # public operations                                                    #
    # ------------------------------------------------------------------ #
    def analyze_complaint(self, text: str, lat: float | None = None,
                          lng: float | None = None,
                          created_at: datetime | None = None) -> dict:
        from ml.classification.urgency import score_urgency
        from ml.extraction.location_extractor import extract_location
        from ml.preprocessing.text import detect_language, normalize_text, romanize_to_english

        created_at = created_at or datetime.now(timezone.utc)
        prediction = self.classifier.predict(text)
        category = prediction["label"]
        urgency = score_urgency(text, category=category)
        location = extract_location(text, lat=lat, lng=lng)
        embedding = [float(x) for x in self.embedder.encode_one(text)]
        return {
            "normalized_text": normalize_text(romanize_to_english(text)),
            "language": detect_language(text),
            "category": category,
            "category_confidence": prediction["confidence"],
            "category_scores": prediction["scores"],
            "classifier_method": prediction["method"],
            "matched_terms": prediction.get("matched_terms", []),
            "urgency": urgency,
            "location": location,
            "embedding": embedding,
            "analyzed_at": created_at.isoformat(),
        }

    def analyze_symptom_report(self, text: str, lat: float | None = None,
                               lng: float | None = None) -> dict:
        from ml.classification.urgency import score_urgency
        from ml.extraction.location_extractor import extract_location
        from ml.preprocessing.lexicons import SYMPTOM_TO_CATEGORIES
        from ml.preprocessing.text import detect_language, normalize_text, romanize_to_english
        from ml.summarization.summarizer import summarize_medical_report

        ner = self.ner.extract(text)
        urgency = score_urgency(text)
        summary = summarize_medical_report(text, ner["entities"], urgency)
        categories: list[str] = []
        for symptom in ner["symptoms"]:
            for cat in SYMPTOM_TO_CATEGORIES.get(symptom, []):
                if cat not in categories:
                    categories.append(cat)
        location = extract_location(text, lat=lat, lng=lng)
        embedding = [float(x) for x in self.embedder.encode_one(text)]
        return {
            "normalized_text": normalize_text(romanize_to_english(text)),
            "language": detect_language(text),
            "entities": ner["entities"],
            "symptoms": ner["symptoms"],
            "symptom_categories": categories,
            "ner_backend": ner["backend"],
            "entity_count": ner["entity_count"],
            "urgency": urgency,
            "summary": summary["summary"],
            "digest": summary.get("digest"),
            "location": location,
            "embedding": embedding,
        }

    def find_duplicates(self, text: str, corpus: list[dict], category: str | None = None,
                        lat: float | None = None, lng: float | None = None,
                        created_at: datetime | None = None) -> list[dict]:
        return self.detector.find_duplicates(text, corpus, category=category,
                                             lat=lat, lng=lng, created_at=created_at)

    def related_items(self, text: str, corpus: list[dict], k: int = 5) -> list[dict]:
        return self.search.top_k(text, corpus, k=k)

    def scan_cross_domain(self, complaints: list[dict], reports: list[dict],
                          daily_series: list[dict] | None = None) -> dict:
        return self.engine.scan(complaints, reports, daily_series)

    def cluster(self, embeddings_list: list[list[float]] | None = None) -> dict:
        import numpy as np
        from ml.clustering.clusterer import cluster_documents

        if embeddings_list:
            return cluster_documents(np.asarray(embeddings_list, dtype=np.float32))
        return cluster_documents(np.zeros((0, 1), dtype=np.float32))

    def summarize(self, text: str) -> dict:
        from ml.summarization.summarizer import summarize

        return summarize(text)

    # ------------------------------------------------------------------ #
    # diagnostics                                                          #
    # ------------------------------------------------------------------ #
    def health(self) -> dict:
        try:
            classifier_method = self.classifier.method
        except Exception as exc:  # noqa: BLE001
            classifier_method = f"error: {exc}"
        try:
            embedder_backend = self.embedder.backend
        except Exception as exc:  # noqa: BLE001
            embedder_backend = f"error: {exc}"
        try:
            import importlib.util

            transformers_available = importlib.util.find_spec("transformers") is not None
        except Exception:  # noqa: BLE001
            transformers_available = False
        return {
            "embedder": embedder_backend,
            "classifier": classifier_method,
            "ner": self.ner.backend,
            "transformers_available": transformers_available,
            "classifier_metrics": getattr(self.classifier, "metrics", None)
            if not isinstance(getattr(self.classifier, "metrics", None), property)
            else None,
        }


_pipeline: HealthPulseNLP | None = None
_pipeline_lock = threading.Lock()


def get_pipeline() -> HealthPulseNLP:
    """Process-wide singleton used by the FastAPI services."""
    global _pipeline
    if _pipeline is None:
        with _pipeline_lock:
            if _pipeline is None:
                _pipeline = HealthPulseNLP()
    return _pipeline
