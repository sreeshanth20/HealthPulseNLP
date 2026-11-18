"""Civic complaint classification.

Two interchangeable backends with identical output schema:
1. ``JoblibClassifier`` — TF-IDF (1-2 grams) + LogisticRegression trained on
   the synthetic dataset by ``ml/training/train_classical.py`` (runs fully
   offline; artifact committed at ml/models/complaint_classifier/).
2. ``RuleClassifier`` — keyword scoring fallback used when the artifact is
   missing (e.g. fresh clone without running the training step).

A HuggingFace transformer path (MuRIL / DeBERTa) is provided in
``ml/training/train_complaint_classifier_hf.py`` and loads transparently if a
fine-tuned checkpoint exists under ml/models/transformer_checkpoints/.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from ml.config import config
from ml.preprocessing.lexicons import COMPLAINT_KEYWORDS
from ml.preprocessing.text import normalize_text, romanize_to_english

logger = logging.getLogger(__name__)


class RuleClassifier:
    """Transparent keyword scorer — explainable fallback baseline."""

    def __init__(self) -> None:
        self.method = "rule-keywords"

    def predict(self, text: str) -> dict:
        clean = normalize_text(romanize_to_english(text))
        scores: dict[str, float] = {}
        for label, keywords in COMPLAINT_KEYWORDS.items():
            if label == "other":
                continue
            hits = sum(1 for kw in keywords if kw in clean)
            scores[label] = hits
        best = max(scores.items(), key=lambda kv: kv[1]) if scores else ("other", 0)
        label = best[0] if best[1] > 0 else "other"
        total = sum(scores.values()) or 1
        confidence = round(best[1] / total, 4) if best[1] > 0 else 0.2
        return {
            "label": label,
            "confidence": confidence,
            "scores": {k: round(v / total, 4) for k, v in scores.items()},
            "method": self.method,
            "matched_terms": [kw for kw in COMPLAINT_KEYWORDS.get(label, []) if kw in clean][:6],
        }


class JoblibClassifier:
    """TF-IDF + LogisticRegression artifact loader."""

    def __init__(self, path: Path | None = None) -> None:
        import joblib

        self.path = path or config.complaint_classifier_path
        payload = joblib.load(self.path)
        self.vectorizer = payload["vectorizer"]
        self.clf = payload["clf"]
        self.labels = payload["labels"]
        self.method = "tfidf-logreg"
        meta_path = self.path.parent / "metrics.json"
        self.metrics: dict | None = None
        if meta_path.exists():
            try:
                self.metrics = json.loads(meta_path.read_text())
            except Exception:  # noqa: BLE001
                self.metrics = None

    def predict(self, text: str) -> dict:
        vec = self.vectorizer.transform([text])
        probs = self.clf.predict_proba(vec)[0]
        pairs = sorted(zip(self.labels, probs), key=lambda kv: kv[1], reverse=True)
        label, confidence = pairs[0]
        return {
            "label": label,
            "confidence": round(float(confidence), 4),
            "scores": {k: round(float(v), 4) for k, v in pairs},
            "method": self.method,
            "matched_terms": [],
        }


class ComplaintClassifier:
    """Facade: transformer checkpoint > joblib artifact > rules."""

    def __init__(self) -> None:
        self._impl = None
        self._load()

    def _load(self) -> None:
        hf_dir = config.PROJECT_ROOT / "ml" / "models" / "transformer_checkpoints" / "complaint_classifier"
        if (hf_dir / "config.json").exists():
            try:
                from transformers import AutoModelForSequenceClassification, AutoTokenizer  # type: ignore
                import torch  # type: ignore

                self._tok = AutoTokenizer.from_pretrained(hf_dir)
                self._model = AutoModelForSequenceClassification.from_pretrained(hf_dir)
                self._model.eval()
                with open(hf_dir / "label_map.json") as fh:
                    self._hf_labels = json.load(fh)
                self._impl = "hf-transformer"
                logger.info("Complaint classifier: HF transformer from %s", hf_dir)
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("HF checkpoint present but failed to load: %s", exc)
        if config.complaint_classifier_path.exists():
            try:
                self._impl = JoblibClassifier()
                logger.info("Complaint classifier: %s", config.complaint_classifier_path.name)
                return
            except Exception as exc:  # noqa: BLE001
                logger.warning("Joblib artifact failed to load: %s", exc)
        self._impl = RuleClassifier()
        logger.info("Complaint classifier: rule fallback")

    @property
    def method(self) -> str:
        if isinstance(self._impl, str):
            return self._impl
        return getattr(self._impl, "method", "unknown")

    def predict(self, text: str) -> dict:
        if self._impl is None:
            raise RuntimeError("classifier not initialised")
        if isinstance(self._impl, str):  # HF transformer path
            import torch  # type: ignore

            inputs = self._tok(text, return_tensors="pt", truncation=True, max_length=256)
            with torch.no_grad():
                logits = self._model(**inputs).logits
            probs = torch.softmax(logits, dim=-1)[0].tolist()
            pairs = sorted(zip(self._hf_labels, probs), key=lambda kv: kv[1], reverse=True)
            label, confidence = pairs[0]
            return {
                "label": label,
                "confidence": round(float(confidence), 4),
                "scores": {k: round(float(v), 4) for k, v in pairs},
                "method": self._impl,
                "matched_terms": [],
            }
        return self._impl.predict(text)
