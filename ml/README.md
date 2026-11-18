# ml/ — HealthPulse NLP & ML package

Independent, modular NLP pipelines consumed by the FastAPI backend via
`ml/inference/pipeline.py` (`HealthPulseNLP` facade). Fully functional with scikit-learn
only; transformer upgrades are optional (`pip install -r ml/requirements-ml.txt`).

## Checkpoints

```
models/
├── complaint_classifier/
│   ├── tfidf_lr.joblib      # COMMITTED artifact — trained in the build sandbox
│   │                        #   (TF-IDF 1-2gram + LogisticRegression, synthetic data)
│   └── metrics.json         # REAL evaluation metrics + synthetic-data notice
└── transformer_checkpoints/ # populated by ml/training/*_hf.py (optional)
    ├── complaint_classifier/   # auto-detected by the classifier facade if present
    ├── medical_ner/            # auto-detected by the NER facade if present
    └── embedder/               # fine-tuned Sentence-Transformer (set EMBEDDING_MODEL)
```

The classical artifact is small, deterministic and committed so a fresh clone works
offline. Re-train anytime (seconds, no GPU):

```bash
python -m ml.datasets.build_datasets      # regenerate synthetic data (seed 42)
python -m ml.training.train_classical     # retrain + overwrite artifact + metrics
python -m ml.evaluation.evaluate          # refresh ml/evaluation/reports/latest.json
```

See `docs/ML_GUIDE.md` for every pipeline, thresholds, weights and the transformer
upgrade path.
