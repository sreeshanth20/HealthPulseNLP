"""Explainable urgency classification for complaints and symptom reports.

Pure rule/feature scorer (no opaque model): every score ships with the
concrete evidence terms that raised it, so moderators can audit decisions.
"""

from __future__ import annotations

import re

from ml.config import config
from ml.preprocessing.lexicons import SEVERITY_TERMS
from ml.preprocessing.text import normalize_text, romanize_to_english

_CRITICAL_TERMS = [
    "unconscious", "blood in", "vomiting blood", "severe bleeding", "not breathing",
    "chest pain", "convulsion", "seizure", "unbearable", "emergency", "collapsed",
]
_HIGH_TERMS = [
    "hospital", "admitted", "admission", "high fever", "103", "104", "severe",
    "blood", "worsening", "three days", "no improvement", "dehydrat", "children are",
    "elderly", "spreading", "many people", "whole family", "multiple people",
    "dehydration", "dengue", "malaria", "typhoid", "cholera", "dysentery",
]
_HEALTH_RISK_TERMS = [
    "drinking", "drinking water", "contaminated", "sewage mixed", "worms in water",
    "dengue", "malaria", "typhoid", "cholera",
]

_NUM_DAYS = re.compile(r"(?:for|since|from)\s+(?:the\s+)?(?:last\s+)?(\d+)\s*(day|week|hour)")


def _score_terms(clean: str, terms: list[str]) -> list[str]:
    return [t for t in terms if t in clean]


def score_urgency(text: str, category: str | None = None,
                  affected_people_hint: bool = False) -> dict:
    """Return {label, score, reasons[]} for a complaint or symptom report."""
    clean = normalize_text(romanize_to_english(text or ""))
    score = 0.0
    reasons: list[str] = []

    critical = _score_terms(clean, _CRITICAL_TERMS)
    if critical:
        score += 0.55
        reasons.append(f"critical severity terms: {', '.join(critical[:4])}")

    high = _score_terms(clean, _HIGH_TERMS)
    if high:
        score += min(0.30, 0.12 * len(high))
        reasons.append(f"serious-condition terms: {', '.join(high[:4])}")

    health_risk = _score_terms(clean, _HEALTH_RISK_TERMS)
    if health_risk:
        score += 0.15
        reasons.append(f"public-health risk terms: {', '.join(health_risk[:4])}")

    sev_hits = [term for term in SEVERITY_TERMS if term in clean]
    if sev_hits:
        top = max(SEVERITY_TERMS[t] for t in sev_hits)
        score += 0.15 * top
        reasons.append(f"severity qualifiers: {', '.join(sev_hits[:4])}")

    m = _NUM_DAYS.search(clean)
    if m:
        days = int(m.group(1)) * (7 if m.group(2) == "week" else 1 if m.group(2) == "day" else 0.2)
        if days >= 7:
            score += 0.12
            reasons.append(f"long duration ({m.group(0)})")
        elif days >= 3:
            score += 0.06
            reasons.append(f"multi-day duration ({m.group(0)})")

    if affected_people_hint or re.search(
            r"\b(many|several|lot of|dozens|entire|neighbourhood|colony|everyone|"
            r"children|kids|infant|baby|babies)\b", clean):
        score += 0.12
        reasons.append("multiple people or children appear affected")

    if category in ("water_contamination", "mosquito menace", "drainage_sewage"):
        score += 0.08
        reasons.append(f"health-sensitive category ({category})")

    score = min(1.0, round(score, 3))

    label = "LOW"
    for threshold, name in config.urgency_thresholds:
        if score >= threshold:
            label = name
            break
    if label == "LOW":
        reasons.append("no aggravating signals found")

    return {"label": label, "score": score, "reasons": reasons[:6]}
