"""Text preprocessing utilities: normalization, language detection, tokenization.

Supports English plus romanized Hindi/Indic surface forms commonly seen in
citizen-submitted complaint text (e.g. "pani me badi smell hai").
"""

from __future__ import annotations

import re
import unicodedata

# Script ranges for common Indic languages.
_SCRIPT_RANGES = {
    "hi": (0x0900, 0x097F),   # Devanagari
    "ta": (0x0B80, 0x0BFF),   # Tamil
    "te": (0x0C00, 0x0C7F),   # Telugu
    "bn": (0x0980, 0x09FF),   # Bengali
    "kn": (0x0C80, 0x0CFF),   # Kannada
    "ml": (0x0D00, 0x0D7F),   # Malayalam
}

_EN_STOPWORDS = {
    "the", "is", "in", "and", "of", "to", "for", "with", "there", "this",
    "that", "it", "are", "was", "on", "at", "from", "has", "have", "be",
    "we", "our", "no", "not", "very", "please", "but", "a", "an", "since",
    "near", "people", "area", "days", "day",
}

# Romanized Hindi/Indic -> canonical English (word-level substitution).
ROMANIZED_MAP = {
    "bukhar": "fever", "feverish": "fever", "dast": "diarrhea", "loosemotion": "diarrhea",
    "loosemotions": "diarrhea", "ulti": "vomiting", "ulantii": "vomiting", "vomitting": "vomiting",
    "pet": "stomach", "sardard": "headache", "sar": "head", "dard": "pain", "khansi": "cough",
    "khaansi": "cough", "zukam": "cold", "galal": "throat", " Gala ": " throat ",
    "pani": "water", "kachra": "garbage", "kudabul": "garbage", "ganda": "dirty",
    "ganDagi": "dirt", "machhar": "mosquito", "machar": "mosquito", "machhardani": "mosquitoes",
    "nali": "drain", "nale": "drain", "gandagi": "dirt", "badboo": "smell", "badbu": "smell",
    "smell": "smell", "peechab": "sewage", "najla": "cold", "sardi": "cold",
    "kamzori": "weakness", "chakkar": "dizziness", " Sir ": " head ",
    "sukha": "dry", "peela": "yellow", "khoon": "blood", "sahas": "breath",
    "saans": "breath", "jalan": "burning", "khujli": "itching", "chakate": "rash",
    "daane": "rash", "shoth": "swelling",
}

_WS_RE = re.compile(r"\s+")
_TOKEN_RE = re.compile(r"[A-Za-z\u00C0-\u024F\u0900-\u097F\u0B80-\u0D7F]+|\d+")


def normalize_text(text: str) -> str:
    """Unicode NFKC + lowercase + whitespace collapse."""
    if not text:
        return ""
    text = unicodedata.normalize("NFKC", text)
    text = text.lower().strip()
    text = _WS_RE.sub(" ", text)
    return text


def romanize_to_english(text: str) -> str:
    """Map common romanized Hindi/Indic words to canonical English forms."""
    if not text:
        return ""
    lowered = text.lower()

    def _sub(match: re.Match) -> str:
        word = match.group(0)
        return ROMANIZED_MAP.get(word, word)

    return re.sub(r"[a-zA-Z]+", _sub, lowered)


def tokenize(text: str) -> list[str]:
    """Simple multilingual word tokenizer preserving offsets is done elsewhere;
    this returns plain tokens."""
    if not text:
        return []
    return _TOKEN_RE.findall(text)


def detect_language(text: str) -> str:
    """Script-based detection with English fallback.

    Returns an ISO-ish code: en, hi, ta, te, bn, kn, ml.
    """
    if not text:
        return "en"
    counts: dict[str, int] = {}
    for ch in text:
        code = ord(ch)
        for lang, (lo, hi) in _SCRIPT_RANGES.items():
            if lo <= code <= hi:
                counts[lang] = counts.get(lang, 0) + 1
                break
    if counts:
        return max(counts, key=counts.get)
    tokens = [t for t in tokenize(text.lower()) if len(t) > 1]
    if not tokens:
        return "en"
    ratio = sum(1 for t in tokens if t in _EN_STOPWORDS) / len(tokens)
    return "en"


def word_ngrams(tokens: list[str], n_max: int = 2) -> list[str]:
    """Unigram + bigram strings joined with spaces."""
    out = list(tokens)
    for n in range(2, n_max + 1):
        for i in range(len(tokens) - n + 1):
            out.append(" ".join(tokens[i : i + n]))
    return out


def tokens_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """Tokenize with character offsets (start, end) for span extraction."""
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]
