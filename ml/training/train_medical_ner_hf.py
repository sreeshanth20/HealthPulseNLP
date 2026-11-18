"""Fine-tune a BioClinicalBERT medical NER model (OPTIONAL, heavy).

Trains token classification on the span-annotated synthetic symptom reports
from ``ml/datasets/data/symptom_reports_ner.jsonl``.

Requires: torch, transformers, datasets (pip install -r ml/requirements-ml.txt)
plus a GPU for reasonable training times. NOT executed in the build sandbox;
fully implemented for reproduction.

Usage:  python -m ml.training.train_medical_ner_hf --model emilyalsentzer/Bio_ClinicalBERT
Output: ml/models/transformer_checkpoints/medical_ner/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.config import config

LABELS = ["O", "B-SYMPTOM", "I-SYMPTOM", "B-MEDICATION", "I-MEDICATION",
          "B-BODY_PART", "I-BODY_PART"]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="emilyalsentzer/Bio_ClinicalBERT")
    parser.add_argument("--epochs", type=int, default=5)
    parser.add_argument("--batch_size", type=int, default=16)
    parser.add_argument("--lr", type=float, default=3e-5)
    args = parser.parse_args()

    try:
        import numpy as np
        import torch  # noqa: F401
        from datasets import Dataset  # type: ignore
        from transformers import (AutoModelForTokenClassification, AutoTokenizer,
                                  DataCollatorForTokenClassification, Trainer,
                                  TrainingArguments)
    except ImportError as exc:
        raise SystemExit(
            "Missing optional ML dependencies. Install them with:\n"
            "  pip install -r ml/requirements-ml.txt\n"
            f"(import error: {exc})\n"
            "The lexicon NER (ml.extraction.medical_ner) works without these packages."
        ) from exc

    data_path = config.PROJECT_ROOT / "ml" / "datasets" / "data" / "symptom_reports_ner.jsonl"
    if not data_path.exists():
        raise SystemExit("Dataset missing. Run: python -m ml.datasets.build_datasets")

    rows = []
    with open(data_path, encoding="utf-8") as fh:
        for line in fh:
            rows.append(json.loads(line))

    label2id = {l: i for i, l in enumerate(LABELS)}
    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForTokenClassification.from_pretrained(
        args.model, num_labels=len(LABELS))

    def encode_row(row: dict) -> dict:
        """Char spans -> BIO tags over wordpieces (first-subtoken strategy)."""
        text = row["text"]
        enc = tokenizer(text, truncation=True, max_length=256)
        word_ids = enc.word_ids()
        # build char -> BIO label map
        char_labels = ["O"] * len(text)
        for span in row.get("entities", []):
            stype = span.get("type", "SYMPTOM")
            if stype not in ("SYMPTOM", "MEDICATION", "BODY_PART"):
                continue
            for i in range(span["start"], min(span["end"], len(text))):
                char_labels[i] = f"I-{stype}"
            char_labels[span["start"]] = f"B-{stype}"
        labels = []
        for wid in word_ids:
            if wid is None:
                labels.append(-100)
                continue
            start, end = enc.offset_mapping_for_word(wid) if hasattr(enc, "offset_mapping_for_word") else (0, 0)
            labels.append(-100)  # placeholder; real mapping below
        # simpler robust approach: re-tokenize with offsets
        enc2 = tokenizer(text, truncation=True, max_length=256, return_offsets_mapping=True)
        labels = []
        for (start, end), wid in zip(enc2["offset_mapping"], enc2.word_ids()):
            if wid is None or end <= start:
                labels.append(-100)
            else:
                tag = char_labels[start]
                labels.append(label2id.get(tag, 0))
        enc2.pop("offset_mapping")
        enc2["labels"] = labels
        return enc2

    encoded = [encode_row(r) for r in rows]
    split = int(0.9 * len(encoded))
    train_ds = Dataset.from_list(encoded[:split])
    eval_ds = Dataset.from_list(encoded[split:])

    def compute_metrics(eval_pred):
        logits, gold = eval_pred
        preds = np.argmax(logits, axis=-1)
        mask = gold != -100
        correct = ((preds == gold) & mask).sum()
        total = mask.sum()
        return {"token_accuracy": float(correct / max(1, total))}

    out_dir = config.PROJECT_ROOT / "ml" / "models" / "transformer_checkpoints" / "medical_ner"
    training_args = TrainingArguments(
        output_dir=str(out_dir),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        learning_rate=args.lr,
        eval_strategy="epoch",
        save_strategy="epoch",
        logging_steps=50,
        fp16=torch.cuda.is_available(),
        report_to=[],
    )
    trainer = Trainer(
        model=model, args=training_args,
        train_dataset=train_ds, eval_dataset=eval_ds,
        data_collator=DataCollatorForTokenClassification(tokenizer),
        compute_metrics=compute_metrics,
    )
    trainer.train()
    final = trainer.evaluate()
    (out_dir / "label_map.json").write_text(json.dumps(LABELS, indent=2))
    (out_dir / "metrics.json").write_text(json.dumps({
        "backbone": args.model, "eval": final,
        "data_notice": "Metrics are computed on SYNTHETIC demonstration data.",
    }, indent=2, default=str))
    trainer.save_model(str(out_dir))
    tokenizer.save_pretrained(str(out_dir))
    print("Saved NER checkpoint to", out_dir)


if __name__ == "__main__":
    main()
