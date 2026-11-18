"""HealthPulse ML/NLP package.

Modular, dependency-light NLP pipelines for:
- civic complaint classification
- medical entity / symptom extraction
- urgency classification
- semantic embeddings + duplicate detection
- temporal anomaly detection
- cross-domain (environment <-> health) association engine

Heavy transformer-based training/inference (DeBERTa, MuRIL, BioClinicalBERT,
Sentence-Transformers) is fully implemented in ``ml/training`` and guarded at
import time: the package falls back to deterministic classical models when the
optional extras are not installed. See ``ml/README.md`` and ``docs/ML_GUIDE.md``.
"""

__version__ = "1.0.0"
