"""Fine-tune a HuggingFace transformer complaint classifier (OPTIONAL, heavy).

Candidate backbones (see docs/ML_GUIDE.md for trade-offs):
- google/muril-base-cased       (multilingual; best for romanized/Indic text)
- microsoft/deberta-v3-base     (strong English general model)
- indobenchmark/indobert-base   (Indic alternative)

Requires: torch, transformers, datasets (pip install -r ml/requirements-ml.txt)
and network access to download the pretrained backbone. A GPU is strongly
recommended. This script was NOT executed in the build sandbox (no GPU / the
heavy stack is optional); it is fully implemented and documented.

Usage:  python -m ml.training.train_complaint_classifier_hf \
            --model google/muril-base-cased --epochs 4 --batch_size 16
Output: ml/models/transformer_checkpoints/complaint_classifier/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.config import config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="google/muril-base-cased")
    parser.add_argument("--epochs", type=int, default=4)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=2e-5)
    parser.add_argument("--max_length", type=int, default=128)
    args = parser.parse_args()

    try:
        import numpy as np  # noqa: F401
        import torch  # noqa: F401
        from datasets import Dataset  # type: ignore
        from sklearn.metrics import accuracy_score, f1_score
        from sklearn.preprocessing import LabelEncoder  # type: ignore
        from transformers import (AutoModelForSequenceClassification, AutoTokenizer,
                                  DataCollatorWithPadding, Trainer, TrainingArguments)
    except ImportError as exc:
        raise SystemExit(
            "Missing optional ML dependencies. Install them with:\n"
            "  pip install -r ml/requirements-ml.txt\n"
            f"(import error: {exc})\n"
            "The classical TF-IDF classifier (ml.training.train_classical) works "
            "without these packages."
        ) from exc

    data_dir = config.PROJECT_ROOT / "ml" / "datasets" / "data"
    train_path = data_dir / "complaints_train.jsonl"
    eval_path = data_dir / "complaints_eval.jsonl"
    if not train_path.exists():
        raise SystemExit("Dataset missing. Run: python -m ml.datasets.build_datasets")

    def load(path: Path) -> tuple[list[str], list[str]]:
        texts, labels = [], []
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                row = json.loads(line)
                texts.append(row["text"])
                labels.append(row["category"])
        return texts, labels

    X_train, y_train_raw = load(train_path)
    X_eval, y_eval_raw = load(eval_path)

    le = LabelEncoder()
    le.fit(y_train_raw + y_eval_raw)
    y_train, y_eval = le.transform(y_train_raw), le.transform(y_eval_raw)
    labels = list(le.classes_)

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model, num_labels=len(labels))

    def tokenize_fn(texts: list[str]):
        return tokenizer(texts, truncation=True, max_length=args.max_length)

    train_ds = Dataset.from_dict({"text": X_train, "label": y_train}).map(
        lambda b: tokenizer(b["text"], truncation=True, max_length=args.max_length),
        batched=True, remove_columns=["text"])
    eval_ds = Dataset.from_dict({"text": X_eval, "label": y_eval}).map(
        lambda b: tokenizer(b["text"], truncation=True, max_length=args.max_length),
        batched=True, remove_columns=["text"])

    def compute_metrics(eval_pred):
        logits, gold = eval_pred
        preds = np.argmax(logits, axis=-1)
        return {
            "accuracy": float(accuracy_score(gold, preds)),
            "macro_f1": float(f1_score(gold, preds, average="macro")),
        }

    out_dir = config.PROJECT_ROOT / "ml" / "models" / "transformer_checkpoints" / "complaint_classifier"
    training_args = TrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size * 2,
        learning_rate=args.lr,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="macro_f1",
        logging_steps=50,
        fp16=torch.cuda.is_available(),
        report_to=[],
    )
    trainer = Trainer(
        model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=eval_ds,
        data_collator=DataCollatorWithPadding(tokenizer),
        compute_metrics=compute_metrics,
    )
    trainer.train()

    final = trainer.evaluate()
    (out_dir / "label_map.json").write_text(json.dumps(labels, ensure_ascii=False, indent=2))
    (out_dir / "metrics.json").write_text(json.dumps({
        "backbone": args.model,
        "epochs": args.epochs,
        "eval": final,
        "data_notice": "Metrics are computed on SYNTHETIC demonstration data.",
    }, indent=2, default=str))
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    print("Saved checkpoint to", out_dir)
    print(json.dumps(final, indent=2, default=str))


if __name__ == "__main__":
    main()
