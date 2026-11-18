"""Semantic embeddings.

Primary backend: Sentence-Transformers (optional heavy dependency).
Fallback backend: deterministic feature-hashing embedder (numpy only) so the
whole platform works offline and in CI. The fallback is stable across runs
(md5-based token hashing) and good enough for demo similarity search, but it
is NOT semantically pretrained — see docs/ML_GUIDE.md for the upgrade path.
"""

from __future__ import annotations

import hashlib
import math
from typing import Iterable, Sequence

import numpy as np

from ml.config import config
from ml.preprocessing.text import normalize_text, word_ngrams


class HashingEmbedder:
    """Deterministic tf-weighted feature hashing into a fixed-size L2 vector."""

    def __init__(self, dim: int | None = None) -> None:
        self.dim = dim or config.hashing_dim
        self.backend = "hashing-v1"

    def _bucket(self, feature: str) -> tuple[int, float]:
        digest = hashlib.md5(feature.encode("utf-8")).digest()
        idx = int.from_bytes(digest[:4], "little") % self.dim
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        return idx, sign

    def encode_one(self, text: str) -> np.ndarray:
        vec = np.zeros(self.dim, dtype=np.float32)
        clean = normalize_text(text)
        if not clean:
            return vec
        from ml.preprocessing.text import tokenize

        tokens = tokenize(clean)
        features = word_ngrams(tokens, n_max=2)
        tf: dict[int, float] = {}
        for feature in features:
            idx, sign = self._bucket(feature)
            tf[idx] = tf.get(idx, 0.0) + sign
        for idx, weight in tf.items():
            vec[idx] = weight
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec /= norm
        return vec

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        return np.stack([self.encode_one(t) for t in texts]) if isinstance(texts, list) else np.stack([self.encode_one(t) for t in texts])


class SentenceTransformerEmbedder:
    """Sentence-Transformers backend (requires the optional ML extras)."""

    def __init__(self, model_name: str | None = None) -> None:
        from sentence_transformers import SentenceTransformer  # type: ignore

        # The application must remain fully functional without a network
        # connection.  SentenceTransformer otherwise probes the Hub even when
        # all required weights are cached, which can turn a dashboard request
        # into repeated connection retries.  If this optional model is not
        # available locally, get_embedder() selects HashingEmbedder below.
        self.model = SentenceTransformer(
            model_name or config.embedding_model,
            local_files_only=True,
        )
        self.backend = f"sentence-transformers:{model_name or config.embedding_model}"

    def encode_one(self, text: str) -> np.ndarray:
        return np.asarray(self.model.encode(text, normalize_embeddings=True))

    def encode(self, texts: Iterable[str]) -> np.ndarray:
        return np.asarray(self.model.encode(list(texts), normalize_embeddings=True))


def get_embedder() -> "SentenceTransformerEmbedder | HashingEmbedder":
    """Return the best available embedder (transformers when installed)."""
    if config.use_transformers != "off":
        try:
            return SentenceTransformerEmbedder()
        except Exception:
            if config.use_transformers == "force":
                raise
    return HashingEmbedder()


def cosine_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Pairwise cosine similarity between two row-stacked matrices."""
    a_n = a / (np.linalg.norm(a, axis=1, keepdims=True) + 1e-12)
    b_n = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-12)
    return a_n @ b_n.T


def cosine(a: Sequence[float], b: Sequence[float]) -> float:
    va = np.asarray(a, dtype=np.float32)
    vb = np.asarray(b, dtype=np.float32)
    denom = (np.linalg.norm(va) * np.linalg.norm(vb)) or 1.0
    return float(np.dot(va, vb) / denom)


def bucketed(feature: str, dim: int) -> int:
    """Stable bucket for a feature string (shared by tests/tools)."""
    return int.from_bytes(hashlib.md5(feature.encode()).digest()[:4], "little") % dim
