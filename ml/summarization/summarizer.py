"""Extractive summarization (no paid LLM dependency).

Sentence scoring combines: medical-term density, urgency/severity terms,
position (first sentences carry context) and length normalization. Returns
the top sentences plus a structured digest built from extracted entities.
"""

from __future__ import annotations

import re

from ml.preprocessing.lexicons import SYMPTOM_LEXICON, SEVERITY_TERMS
from ml.preprocessing.text import normalize_text, romanize_to_english

_SENT_RE = re.compile(r"(?<=[.!?])\s+|\n+")


def _split_sentences(text: str) -> list[str]:
    parts = [s.strip() for s in _SENT_RE.split(text or "") if s.strip()]
    return parts


def _all_symptom_forms() -> set[str]:
    forms: set[str] = set()
    for variants in SYMPTOM_LEXICON.values():
        forms.update(variants)
    return forms


_SYMPTOM_FORMS = _all_symptom_forms()


def _score_sentence(sentence: str, position: int, total: int) -> float:
    clean = normalize_text(romanize_to_english(sentence))
    tokens = len(clean.split()) or 1
    hits = sum(1 for form in _SYMPTOM_FORMS if form in clean)
    severity = sum(1 for t in SEVERITY_TERMS if t in clean)
    score = 2.0 * hits + 1.5 * severity
    score += 1.2 if position == 0 else 0.5 if position < total * 0.34 else 0.0
    score *= min(1.5, max(0.5, tokens / 18.0))  # gentle length normalization
    return score


def summarize(text: str, max_sentences: int = 3) -> dict:
    """Extractive summary of a (medical or civic) free-text report."""
    sentences = _split_sentences(text)
    if not sentences:
        return {"summary": "", "key_sentences": [], "method": "extractive-v1"}
    if len(sentences) <= max_sentences:
        return {
            "summary": " ".join(sentences),
            "key_sentences": sentences,
            "method": "extractive-v1",
        }
    scored = [(i, s, _score_sentence(s, i, len(sentences))) for i, s in enumerate(sentences)]
    scored.sort(key=lambda t: t[2], reverse=True)
    picked = sorted(scored[:max_sentences], key=lambda t: t[0])
    return {
        "summary": " ".join(s for _, s, _ in picked),
        "key_sentences": [s for _, s, _ in picked],
        "method": "extractive-v1",
    }


def summarize_medical_report(text: str, entities: list[dict] | None = None,
                             urgency: dict | None = None) -> dict:
    """Structured digest for symptom reports (still extractive, no diagnosis)."""
    base = summarize(text, max_sentences=3)
    symptoms: list[str] = []
    durations: list[str] = []
    for ent in (entities or []):
        if ent.get("type") == "SYMPTOM" and ent.get("canonical") not in symptoms:
            symptoms.append(ent["canonical"])
        if ent.get("type") == "DURATION":
            durations.append(ent.get("canonical", ent.get("text", "")))
    digest_parts: list[str] = []
    if symptoms:
        digest_parts.append(f"Reported symptoms: {', '.join(symptoms[:8])}.")
    if durations:
        digest_parts.append(f"Reported duration: {', '.join(sorted(set(durations))[:3])}.")
    if urgency:
        digest_parts.append(f"Triage urgency: {urgency['label']} (score {urgency['score']}).")
    digest_parts.append("This summary is extracted from the patient's own words; "
                        "it is not a diagnosis and does not replace clinical review.")
    return {
        **base,
        "digest": " ".join(digest_parts),
        "symptoms": symptoms,
        "durations": durations,
    }
