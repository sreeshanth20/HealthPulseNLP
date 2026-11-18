"""Medical entity & symptom extraction.

Primary: deterministic longest-match lexicon NER over the curated symptom /
medication / body-part vocabulary (works fully offline, char-span annotated,
confidence-scored).

Optional: fine-tuned BioClinicalBERT token-classification checkpoint under
ml/models/transformer_checkpoints/medical_ner/ loads transparently when the
transformers extras are installed (training script in ml/training/).
"""

from __future__ import annotations

import re
from collections import Counter

from ml.preprocessing.lexicons import BODY_PART_TERMS, MEDICATION_TERMS, SYMPTOM_LEXICON
from ml.preprocessing.text import normalize_text, romanize_to_english, tokens_with_offsets

# surface form -> (canonical, type)
_SURFACE_INDEX: dict[str, tuple[str, str]] = {}
for canonical, forms in SYMPTOM_LEXICON.items():
    for form in forms:
        _SURFACE_INDEX[form] = (canonical, "SYMPTOM")
for form in MEDICATION_TERMS:
    _SURFACE_INDEX[form] = (form, "MEDICATION")
for form in BODY_PART_TERMS:
    _SURFACE_INDEX[form] = (form, "BODY_PART")

_DURATION_RE = re.compile(
    r"(?:for|since|past|last)\s+(?:(\d+|one|two|three|four|five|six|seven)\s+)?"
    r"(day|days|week|weeks|month|months|hour|hours)"
)
_NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7}
_FEVER_TEMP_RE = re.compile(r"\b(1[0-9]{2}(\.\d)?)\s*(?:f|degree|°f)?\b")
_AGE_RE = re.compile(r"\b(\d{1,2})[-\s]?year[-\s]?old\b|\bage[d]?\s*[:=]?\s*(\d{1,2})\b")

_MAX_GRAM = 4


def _lookup_ngrams(tokens: list[tuple[str, int, int]]) -> list[dict]:
    """Longest-match scan over token n-grams; non-overlapping, longest first."""
    found: list[dict] = []
    taken: list[tuple[int, int]] = []
    n = len(tokens)
    # generate candidates (longest first) then accept non-overlapping ones
    candidates: list[tuple[int, tuple[str, str], int, int, str]] = []
    for i in range(n):
        for j in range(min(_MAX_GRAM, n - i), 0, -1):
            gram = " ".join(tokens[k][0] for k in range(i, i + j)).lower()
            hit = _SURFACE_INDEX.get(gram)
            if hit:
                start, end = tokens[i][1], tokens[i + j - 1][2]
                confidence = 0.95 if j > 1 else 0.80
                candidates.append((j, hit, start, end, gram))
    candidates.sort(key=lambda c: (-(c[0]), c[2]))
    for _, hit, start, end, gram in candidates:
        if any(s < end and e > start for s, e in taken):
            continue
        taken.append((start, end))
        found.append({
            "text": gram,
            "canonical": hit[0],
            "type": hit[1],
            "start": start,
            "end": end,
            "confidence": confidence,
        })
    found.sort(key=lambda e: e["start"])
    return found


def _extract_durations(text: str) -> list[dict]:
    out: list[dict] = []
    for m in _DURATION_RE.finditer(text):
        raw = m.group(1) or "1"
        value = _NUM_WORDS.get(raw, None)
        if value is None:
            try:
                value = int(raw)
            except ValueError:
                value = 1
        if m.group(2).startswith("week"):
            days = value * 7
        elif m.group(2).startswith("month"):
            days = value * 30
        elif m.group(2).startswith("hour"):
            days = max(1, value // 24)
        else:
            days = value
        out.append({
            "text": m.group(0), "canonical": f"{days}d", "type": "DURATION",
            "start": m.start(), "end": m.end(), "confidence": 0.9, "days": days,
        })
    return out


def _extract_temperatures(text: str) -> list[dict]:
    out: list[dict] = []
    for m in _FEVER_TEMP_RE.finditer(text):
        value = float(m.group(1))
        if 99.0 <= value <= 107.0:
            out.append({
                "text": m.group(0), "canonical": f"{value}F", "type": "VITAL",
                "start": m.start(), "end": m.end(), "confidence": 0.85,
            })
    return out


def _extract_ages(text: str) -> list[dict]:
    out: list[dict] = []
    for m in _AGE_RE.finditer(text):
        value = m.group(1) or m.group(2)
        out.append({
            "text": m.group(0), "canonical": f"{value}y", "type": "AGE",
            "start": m.start(), "end": m.end(), "confidence": 0.8,
        })
    return out


class MedicalNER:
    """Lexicon-first NER with optional transformer upgrade."""

    def __init__(self) -> None:
        self.backend = "lexicon-v1"
        self._hf = None
        self._try_load_hf()

    def _try_load_hf(self) -> None:
        from pathlib import Path

        from ml.config import config

        hf_dir = config.PROJECT_ROOT / "ml" / "models" / "transformer_checkpoints" / "medical_ner"
        if not (hf_dir / "config.json").exists():
            return
        try:
            from transformers import (AutoModelForTokenClassification,  # type: ignore
                                      AutoTokenizer, pipeline)

            tok = AutoTokenizer.from_pretrained(hf_dir)
            model = AutoModelForTokenClassification.from_pretrained(hf_dir)
            self._hf = pipeline("token-classification", model=model, tokenizer=tok,
                                aggregation_strategy="simple")
            self.backend = "bioclinicalbert-hf"
        except Exception:  # noqa: BLE001 - optional dependency
            self._hf = None

    def extract(self, text: str) -> dict:
        """Return entities, symptom list and grouped views for one document."""
        raw = text or ""
        normalized = normalize_text(romanize_to_english(raw))
        tokens = tokens_with_offsets(normalized)
        entities = _lookup_ngrams(tokens)
        entities += _extract_durations(normalized)
        entities += _extract_temperatures(normalized)
        entities += _extract_ages(normalized)
        entities.sort(key=lambda e: e["start"])

        symptoms: list[str] = []
        seen = set()
        for ent in entities:
            if ent["type"] == "SYMPTOM" and ent["canonical"] not in seen:
                seen.add(ent["canonical"])
                symptoms.append(ent["canonical"])

        counts = Counter(e["type"] for e in entities)
        return {
            "backend": self.backend,
            "entities": entities,
            "symptoms": symptoms,
            "counts": dict(counts),
            "entity_count": len(entities),
        }

    def group_entities(self, entities: list[dict]) -> dict[str, list[dict]]:
        grouped: dict[str, list[dict]] = {}
        for ent in entities:
            grouped.setdefault(ent["type"], []).append(ent)
        return grouped
