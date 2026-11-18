"""Fine-tune the Sentence-Transformer embedding model (OPTIONAL, heavy).

Trains on the synthetic cross-domain sentence pairs so that environmental
complaint text and symptom-report text land closer together in embedding
space. This is the main lever for improving cross-domain recall.

Requires: torch, sentence-transformers (pip install -r ml/requirements-ml.txt).
NOT executed in the build sandbox; fully implemented.

Usage:  python -m ml.training.train_embedding_model \
            --base sentence-transformers/all-MiniLM-L6-v2
Output: ml/models/transformer_checkpoints/embedder/
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from ml.config import config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="sentence-transformers/all-MiniLM-L6-v2")
    parser.add_argument("--epochs", type=int, default=2)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()

    try:
        from datasets import load_dataset  # noqa: F401
        from sentence_transformers import (InputExample, losses,  # type: ignore
                                           SentenceTransformer)
        from torch.utils.data import DataLoader  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Missing optional ML dependencies. Install them with:\n"
            "  pip install -r ml/requirements-ml.txt\n"
            f"(import error: {exc})\n"
            "The deterministic hashing embedder works without these packages."
        ) from exc

    pairs_path = config.PROJECT_ROOT / "ml" / "datasets" / "data" / "cross_domain_pairs.jsonl"
    if not pairs_path.exists():
        raise SystemExit("Dataset missing. Run: python -m ml.datasets.build_datasets")

    positives: list[InputExample] = []
    with open(pairs_path, encoding="utf-8") as fh:
        for line in fh:
            row = json.loads(line)
            if row["label"] == 1:
                positives.append(InputExample(texts=[row["text_a"], row["text_b"]]))

    model = SentenceTransformer(args.base)
    loader = DataLoader(positives, shuffle=True, batch_size=args.batch_size)
    loss = losses.MultipleNegativesRankingLoss(model)

    out_dir = config.PROJECT_ROOT / "ml" / "models" / "transformer_checkpoints" / "embedder"
    model.fit(train_objectives=[(loader, loss)], epochs=args.epochs, warmup_steps=100,
              output_path=str(out_dir), show_progress_bar=True)
    (out_dir / "training_info.json").write_text(json.dumps({
        "base_model": args.base,
        "epochs": args.epochs,
        "pairs_used": len(positives),
        "loss": "MultipleNegativesRankingLoss",
        "data_notice": "Trained on SYNTHETIC demonstration pairs.",
    }, indent=2))
    print("Saved fine-tuned embedder to", out_dir)


if __name__ == "__main__":
    main()
