"""Central ML configuration (no external YAML dependency required)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
BASE_DIR = ML_DIR.parent  # HealthPulse-AI project root
PROJECT_ROOT = BASE_DIR   # alias kept for readability at call sites


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


@dataclass
class MLConfig:
    """Tunables for every pipeline. Environment variables override defaults."""

    PROJECT_ROOT: Path = BASE_DIR

    # --- embeddings -----------------------------------------------------------
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    hashing_dim: int = 384
    use_transformers: str = "auto"  # auto | force | off

    # --- classification -------------------------------------------------------
    complaint_classifier_path: Path = ML_DIR / "models" / "complaint_classifier" / "tfidf_lr.joblib"
    dedupe_threshold: float = _env_float("DEDUPE_THRESHOLD", 0.75)
    duplicate_gate_cosine: float = 0.90  # allow cross-category duplicates above this

    # --- cross-domain association ---------------------------------------------
    association_threshold: float = _env_float("ASSOCIATION_THRESHOLD", 0.55)
    max_association_km: float = _env_float("MAX_ASSOCIATION_KM", 3.0)
    max_association_days: int = 21
    w_semantic: float = 0.45
    w_spatial: float = 0.20
    w_temporal: float = 0.20
    w_theme: float = 0.15

    # --- anomaly ---------------------------------------------------------------
    anomaly_z_threshold: float = 2.5
    anomaly_min_history: int = 7

    # --- clustering --------------------------------------------------------------
    min_cluster_size: int = 3

    # --- urgency thresholds -----------------------------------------------------
    urgency_thresholds: tuple = ((0.75, "CRITICAL"), (0.45, "HIGH"), (0.25, "MEDIUM"))

    def __post_init__(self) -> None:
        env_path = os.environ.get("COMPLAINT_CLASSIFIER_PATH")
        if env_path:
            candidate = Path(env_path)
            if not candidate.is_absolute():
                candidate = PROJECT_ROOT / "backend" / env_path
                if not candidate.exists():
                    candidate = ML_DIR / "models" / "complaint_classifier" / Path(env_path).name
            self.complaint_classifier_path = candidate


config = MLConfig()

DISCLAIMER = (
    "HealthPulse association scores are statistical co-occurrence indicators "
    "computed from publicly submitted civic complaints and voluntarily shared "
    "symptom reports. They are NOT clinical risk probabilities, NOT diagnoses, "
    "and correlation between environmental complaints and symptom reports never "
    "implies causation. All outputs require investigation by qualified officials."
)
