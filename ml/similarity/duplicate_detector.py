"""Duplicate complaint detection and semantic search.

Duplicates are scored as a weighted blend of:
- semantic cosine similarity between embeddings (weight 0.60)
- lexical Jaccard overlap of content tokens (weight 0.20)
- same-category bonus (weight 0.10)
- geographic proximity bonus within 1 km (weight 0.10)

Gates: cross-category candidates require cosine >= duplicate_gate_cosine
(0.90) so genuinely different categories are only flagged when the text is
nearly identical. The decision ships with per-signal evidence values.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone

import numpy as np

from ml.config import config
from ml.embeddings.embedder import cosine, get_embedder
from ml.preprocessing.gazetteer import haversine_km
from ml.preprocessing.text import normalize_text, tokenize


@dataclass
class SimilarItem:
    id: int | str
    text: str
    category: str | None = None
    district: str | None = None
    lat: float | None = None
    lng: float | None = None
    created_at: datetime | None = None
    embedding: list[float] | None = None
    similarity: float = 0.0
    jaccard: float = 0.0
    category_match: bool = False
    distance_km: float | None = None
    age_days: float | None = None
    signals: dict = field(default_factory=dict)
    is_duplicate: bool = False


def _token_set(text: str) -> set[str]:
    return {t for t in tokenize(normalize_text(text)) if len(t) > 2}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _days_between(a: datetime | None, b: datetime | None) -> float | None:
    if a is None or b is None:
        return None
    a2 = a if a.tzinfo else a.replace(tzinfo=timezone.utc)
    b2 = b if b.tzinfo else b.replace(tzinfo=timezone.utc)
    return abs((a2 - b2).total_seconds()) / 86400.0


class DuplicateDetector:
    """Candidate duplicate finder against an in-memory corpus."""

    def __init__(self, embedder=None) -> None:
        self.embedder = embedder or get_embedder()

    def _corpus_vector(self, item: SimilarItem) -> list[float]:
        if item.embedding:
            return item.embedding
        return [float(x) for x in self.embedder.encode_one(item.text)]

    def find_duplicates(self, text: str, corpus: list[dict],
                        category: str | None = None,
                        lat: float | None = None, lng: float | None = None,
                        created_at: datetime | None = None) -> list[dict]:
        """Return corpus items scored as potential duplicates, best first."""
        vec = np.asarray(self.embedder.encode_one(text), dtype=np.float32)
        text_tokens = _token_set(text)
        results: list[SimilarItem] = []

        for row in corpus:
            item = SimilarItem(
                id=row.get("id"),
                text=row.get("text") or row.get("description") or "",
                category=row.get("category"),
                district=row.get("district"),
                lat=row.get("lat"),
                lng=row.get("lng"),
                created_at=row.get("created_at"),
                embedding=row.get("embedding"),
            )
            if not item.text:
                continue
            item.similarity = float(cosine(vec, np.asarray(self._corpus_vector(item), dtype=np.float32)))
            item.jaccard = jaccard(text_tokens, _token_set(item.text))
            item.category_match = bool(category and item.category and category == item.category)

            if item.lat is not None and lat is not None:
                item.distance_km = haversine_km(lat, lng or lat, item.lat, item.lng or item.lat)
            item.age_days = _days_between(created_at, item.created_at)

            geo_bonus = 0.0
            if item.distance_km is not None:
                geo_bonus = max(0.0, 1.0 - item.distance_km / 1.0)
            temporal_bonus = 0.0
            if item.age_days is not None:
                temporal_bonus = max(0.0, 1.0 - item.age_days / 30.0)

            blended = (
                0.60 * item.similarity
                + 0.20 * item.jaccard
                + 0.10 * (1.0 if item.category_match else 0.0)
                + 0.10 * geo_bonus
            )
            # near-identical text crosses category gates
            if not item.category_match and item.similarity < config.duplicate_gate_cosine:
                blended *= 0.5
            item.signals = {
                "semantic_similarity": round(item.similarity, 4),
                "jaccard": round(item.jaccard, 4),
                "category_match": item.category_match,
                "distance_km": round(item.distance_km, 3) if item.distance_km is not None else None,
                "age_days": round(item.age_days, 2) if item.age_days is not None else None,
                "temporal_bonus": round(temporal_bonus, 4),
                "blended_score": round(blended, 4),
            }
            item.similarity = blended
            results.append(item)

        results.sort(key=lambda r: r.similarity, reverse=True)
        out: list[dict] = []
        for r in results:
            if r.similarity < 0.25:
                continue
            r.is_duplicate = r.similarity >= config.dedupe_threshold
            out.append({
                "id": r.id,
                "text": r.text,
                "category": r.category,
                "district": r.district,
                "score": round(r.similarity, 4),
                "is_duplicate": r.is_duplicate,
                "signals": r.signals,
            })
        return out


class SemanticSearch:
    """Top-k semantic search over an in-memory corpus."""

    def __init__(self, embedder=None) -> None:
        self.embedder = embedder or get_embedder()

    def top_k(self, query: str, corpus: list[dict], k: int = 5,
              min_score: float = 0.25) -> list[dict]:
        if not corpus:
            return []
        vec = np.asarray(self.embedder.encode_one(query), dtype=np.float32)
        scored = []
        for row in corpus:
            emb = row.get("embedding")
            if emb is None:
                emb = np.asarray(self.embedder.encode_one(row.get("text", "")), dtype=np.float32)
            sim = float(cosine(vec, np.asarray(emb, dtype=np.float32)))
            if sim >= min_score:
                scored.append({"id": row.get("id"), "text": row.get("text"),
                               "meta": {k: v for k, v in row.items()
                                        if k not in ("text", "embedding")},
                               "score": round(sim, 4)})
        scored.sort(key=lambda s: s["score"], reverse=True)
        return scored[:k]
