"""Document clustering (HDBSCAN with a DBSCAN fallback).

Clusters report/complaint embeddings to surface community-level groupings.
HDBSCAN is used when the optional extra is installed; otherwise sklearn's
DBSCAN on cosine-distance features provides the same interface.
"""

from __future__ import annotations

import numpy as np


def cluster_documents(embeddings: np.ndarray, min_cluster_size: int | None = None) -> dict:
    """Cluster row-stacked embeddings.

    Returns {labels: list[int], method: str, n_clusters, noise_count, sizes}.
    Label -1 marks noise (unclustered).
    """
    n = len(embeddings)
    if n == 0:
        return {"labels": [], "method": "none", "n_clusters": 0, "noise_count": 0, "sizes": {}}

    if min_cluster_size is None:
        from ml.config import config

        min_cluster_size = min(config.min_cluster_size, max(2, n // 4))

    # 1) HDBSCAN (preferred; handles variable-density clusters)
    try:
        import hdbscan  # type: ignore

        clusterer = hdbscan.HDBSCAN(
            min_cluster_size=min_cluster_size, min_samples=1, metric="euclidean",
            cluster_selection_method="leaf",
        )
        labels = clusterer.fit_predict(np.asarray(embeddings, dtype=np.float64))
        return _summarize(labels.tolist(), "hdbscan")
    except Exception:  # noqa: BLE001 - optional dependency
        pass

    # 2) DBSCAN fallback on cosine distance with an adaptive eps
    from sklearn.cluster import DBSCAN
    from sklearn.neighbors import NearestNeighbors

    X = np.asarray(embeddings, dtype=np.float32)
    norm = X / (np.linalg.norm(X, axis=1, keepdims=True) + 1e-12)
    k = max(2, min(6, n - 1))
    try:
        nn = NearestNeighbors(n_neighbors=k)
        nn.fit(norm)
        dist, _ = nn.kneighbors(norm)
        eps = float(np.median(dist[:, -1])) or 0.5
    except Exception:  # noqa: BLE001
        eps = 0.5
    labels = DBSCAN(eps=eps, min_samples=max(1, min_cluster_size - 1), metric="cosine").fit_predict(norm)
    return _summarize(labels.tolist(), "dbscan-fallback")


def _summarize(labels: list[int], method: str) -> dict:
    from collections import Counter

    counts = Counter(l for l in labels if l != -1)
    sizes = {str(k): v for k, v in sorted(counts.items())}
    return {
        "labels": labels,
        "method": method,
        "n_clusters": len(counts),
        "noise_count": sum(1 for l in labels if l == -1),
        "sizes": sizes,
    }
