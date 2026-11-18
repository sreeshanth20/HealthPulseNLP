"""Offline evaluation harness.

Loads the saved classical classifier (or falls back to the rule baseline),
evaluates it against the synthetic eval split and writes a JSON report to
ml/evaluation/reports/latest.json.

Usage:  python -m ml.evaluation.evaluate
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from ml.config import config

REPORTS_DIR = Path(__file__).resolve().parent / "reports"


def evaluate() -> dict:
    from sklearn.metrics import classification_report, f1_score

    from ml.classification.complaint_classifier import ComplaintClassifier

    data_path = config.PROJECT_ROOT / "ml" / "datasets" / "data" / "complaints_eval.jsonl"
    if not data_path.exists():
        raise SystemExit("Dataset missing. Run: python -m ml.datasets.build_datasets")

    texts, gold = [], []
    with open(data_path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            texts.append(row["text"])
            gold.append(row["category"])

    classifier = ComplaintClassifier()
    preds = [classifier.predict(t)["label"] for t in texts]
    macro_f1 = float(f1_score(gold, preds, average="macro"))
    accuracy = sum(1 for g, p in zip(gold, preds) if g == p) / len(gold)
    report = classification_report(gold, preds, output_dict=True, zero_division=0)

    result = {
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "classifier_method": classifier.method,
        "n_eval": len(texts),
        "accuracy": round(accuracy, 4),
        "macro_f1": round(macro_f1, 4),
        "per_class": report,
        "data_notice": "Computed on SYNTHETIC demonstration data; not real-world performance.",
    }
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    (REPORTS_DIR / "latest.json").write_text(json.dumps(result, indent=2, ensure_ascii=False))
    print(f"[{classifier.method}] accuracy={accuracy:.4f} macro_f1={macro_f1:.4f} (n={len(texts)})")
    return result


if __name__ == "__main__":
    evaluate()
