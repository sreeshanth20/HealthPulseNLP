# HealthPulse AI — ML/NLP Guide

Every pipeline is modular, dependency-light, explainable and testable in isolation.
The platform is **fully functional offline**; transformer upgrades are optional extras.

## 1. Layout

```
ml/
├── config.py                 # all thresholds/weights in one place (env-overridable)
├── preprocessing/            # text normalization, language ID, lexicons, gazetteer
├── embeddings/               # sentence-transformers OR deterministic hashing embedder
├── classification/           # complaint classifier + urgency scorer
├── extraction/               # medical NER + location extractor
├── similarity/               # duplicate detector + semantic search
├── anomaly/                  # temporal anomaly detection
├── clustering/               # HDBSCAN / DBSCAN fallback
├── summarization/            # extractive summarizer
├── crossdomain/              # cross-domain intelligence engine
├── inference/                # HealthPulseNLP facade (backend entry point)
├── datasets/                 # synthetic dataset builder + curated demo corpus
├── training/                 # classical trainer + 3 HF fine-tuning scripts
├── evaluation/               # offline evaluation harness
└── models/                   # committed classical artifact; HF checkpoints land here
```

## 2. Pipelines and model choices

### 2.1 Complaint classification

- **Offline default (deployed):** TF-IDF (word 1–2 grams, 20k features, sublinear tf)
  + LogisticRegression (C=8), trained on the synthetic dataset.
- **Rule fallback:** keyword scoring over the complaint lexicon (used if the artifact
  is missing) — always explainable.
- **Optional upgrade:** `ml/training/train_complaint_classifier_hf.py` fine-tunes
  `google/muril-base-cased` (recommended for romanized/Indic text) or
  `microsoft/deberta-v3-base`. If a checkpoint exists under
  `ml/models/transformer_checkpoints/complaint_classifier/`, the facade loads it
  automatically.

**Real metrics (executed in the build sandbox):**

| Metric | Value |
| --- | --- |
| Train rows / eval rows | 1,494 / 315 (synthetic, seed 42) |
| Training time | 0.4 s |
| Eval accuracy | **1.0000** |
| Eval macro-F1 | **1.0000** |

> ⚠️ These numbers are computed on **template-generated synthetic data** — the eval
> split uses the same phrase templates as training, so near-perfect scores demonstrate
> pipeline correctness, NOT real-world performance. For honest numbers, train on real
> labelled complaint data (the training script accepts any JSONL of
> `{"text": ..., "category": ...}` rows).

### 2.2 Medical entity / symptom extraction

- **Offline default (deployed):** longest-match lexicon NER over a curated vocabulary
  (~22 canonical symptoms with EN + romanized-HI surface forms, medications, body parts,
  severity terms) producing **character-span annotations**, plus regex extractors for
  DURATION (`for three days`), VITAL (`fever 102`) and AGE (`6-year-old`).
- **Optional upgrade:** BioClinicalBERT token classification
  (`ml/training/train_medical_ner_hf.py`) on the span-annotated synthetic reports;
  checkpoint at `ml/models/transformer_checkpoints/medical_ner/` loads automatically.

### 2.3 Embeddings & semantic similarity

- **Offline default:** deterministic **feature-hashing embedder** (384-dim, md5-bucketed,
  sign-hashed, tf-weighted, L2-normalized). Stable across runs and machines; good enough
  for demo-scale similarity, but it is NOT semantically pretrained — cross-domain recall
  is carried by the spatial/temporal/theme signals.
- **Optional upgrade:** Sentence-Transformers (`all-MiniLM-L6-v2`) and a **cross-domain
  fine-tune** on the generated complaint↔report pairs
  (`ml/training/train_embedding_model.py`, MultipleNegativesRankingLoss) — the main lever
  for improving cross-domain sensitivity.

### 2.4 Urgency triage

Deliberately rule-based and fully auditable: critical-term hits (+0.55), serious-condition
terms (+0.12 each, capped), public-health risk terms (+0.15), severity qualifiers,
duration signals, affected-population signals, category prior. Output: score 0–1,
label LOW < 0.25 ≤ MEDIUM < 0.45 ≤ HIGH < 0.75 ≤ CRITICAL, and **human-readable reasons**
(e.g. *"serious-condition terms: admitted, dehydration"*, *"multiple people or children
appear affected"*).

### 2.5 Duplicate detection

Blended score: `0.60·cosine + 0.20·Jaccard + 0.10·same-category + 0.10·geo(≤1 km)`,
with a cross-category gate (requires cosine ≥ 0.90) and a configurable threshold
(default 0.75). Every candidate returns per-signal values for UI display.

### 2.6 Temporal anomaly detection

Per series (e.g. district daily complaint counts): trailing-baseline z-score,
EWMA control limits, and Poisson-CUSUM. **Anomaly verdict requires z-score plus a second
detector** (or lift ≥ 3×) to suppress false positives. Returns observed vs expected, lift,
and which detectors fired.

### 2.7 Clustering

HDBSCAN (leaf selection) when installed; otherwise sklearn DBSCAN with an adaptive eps
(median k-th neighbor cosine distance). Used to group related embeddings for
spatial-cluster views.

### 2.8 Summarization

Extractive only (no LLM): sentence scoring by medical-term density + severity terms +
position + length normalization; the medical digest template always ends with
*"not a diagnosis and does not replace clinical review."*

## 3. Cross-domain association scoring

```
association = 0.45 · semantic_similarity
            + 0.20 · spatial_proximity      (1 − km/3)
            + 0.20 · temporal_proximity     (1 − days/21)
            + 0.15 · theme_match            (env-category ↔ symptom-category prior)
```

Pairs ≥ 0.55 form clusters via connected components; each alert ships its top pairs with
the full contribution breakdown. Theme priors: water→GI/febrile, garbage/drainage→GI/
dermal/vector, mosquito→vector/febrile — explicitly a **co-occurrence prior, not causation**.

## 4. Fine-tuning (optional, not executed in the build sandbox)

Requires `pip install -r ml/requirements-ml.txt` (torch, transformers,
sentence-transformers, datasets, accelerate, hdbscan) and ideally a GPU. All three
scripts follow the same pattern: load the generated JSONL → tokenize → HF Trainer →
save checkpoint + label map + metrics to `ml/models/transformer_checkpoints/<name>/`,
where the inference facade auto-detects them.

```bash
python -m ml.training.train_complaint_classifier_hf --model google/muril-base-cased --epochs 4
python -m ml.training.train_medical_ner_hf        --model emilyalsentzer/Bio_ClinicalBERT
python -m ml.training.train_embedding_model       --base sentence-transformers/all-MiniLM-L6-v2
```

Datasets are regenerated deterministically with `python -m ml.datasets.build_datasets`
(seed 42). Replace with real labelled data for production-grade models.

## 5. Offline evaluation

```bash
python -m ml.evaluation.evaluate     # writes ml/evaluation/reports/latest.json
```

Uses the committed classifier artifact against the eval split; the JSON includes
per-class metrics and the synthetic-data notice.
