"""Location extraction for complaints and reports.

Combines a curated gazetteer (synthetic demo city 'Riverton') with common
surface patterns ("near X market", "in Ward 3", pincode matching). The demo
gazetteer is intentionally small and clearly fictional; swap in a real one for
production deployments.
"""

from __future__ import annotations

import re

from ml.preprocessing.gazetteer import GAZETTEER, Place, haversine_km, lookup
from ml.preprocessing.text import normalize_text

_PLACE_RE = re.compile(
    r"(?:in|at|near|behind|opposite|beside|on|from)\s+"
    r"((?:[a-z][a-z ]{0,30}?)"
    r"(?: street| road| nagar| colony| ward| area| market| park| school| lane| cross| layout|"
    r" beach| hills| town| gate| fields| brook| view| side))\b"
)
_PINCODE_RE = re.compile(r"\b([1-9]\d{5})\b")
_WARD_RE = re.compile(r"\bward\s*[-#]?(\d{1,2})\b")

# pincode -> district for the demo city
_PIN_TO_PLACE = {p.pincode: p for p in GAZETTEER.values()}


def extract_location(text: str, lat: float | None = None, lng: float | None = None) -> dict:
    """Extract the best-guess location for a text.

    Returns {raw_text, district, lat, lng, pincode, confidence, source}.
    Explicit lat/lng arguments win over textual mentions.
    """
    clean = normalize_text(text or "")
    result: dict = {
        "raw_text": None, "district": None, "lat": lat, "lng": lng,
        "pincode": None, "confidence": 0.0, "source": None,
    }

    place: Place | None = None
    if lat is not None and lng is not None:
        district, distance = nearest_place(lat, lng)
        result.update({
            "district": district, "confidence": round(max(0.0, 1.0 - distance / 5.0), 2),
            "source": "coordinates",
        })
        return result

    pin = _PINCODE_RE.search(clean)
    if pin and pin.group(1) in _PIN_TO_PLACE:
        place = _PIN_TO_PLACE[pin.group(1)]
        result["pincode"] = pin.group(1)
        result["source"] = "pincode"
        result["confidence"] = 0.9

    direct = lookup(clean.split(",")[0]) or lookup(clean)
    if direct is None:
        for name in GAZETTEER:
            if re.search(rf"\b{re.escape(name)}\b", clean):
                direct = lookup(name)
                break
    if direct is not None and (place is None or result["source"] != "pincode"):
        place = direct
        result["source"] = "gazetteer-name"
        result["confidence"] = 0.85

    if place is None:
        m = _PLACE_RE.search(clean)
        if m:
            phrase = m.group(1).strip()
            for p in GAZETTEER.values():
                alias_hit = any(a in phrase for a in p.aliases)
                if alias_hit or p.name.lower() in phrase:
                    place = p
                    break
            result["raw_text"] = phrase
            result["source"] = "phrase-pattern"
            result["confidence"] = 0.6 if place else 0.3

    if place is not None:
        result["district"] = place.name
        result["lat"] = place.lat
        result["lng"] = place.lng

    return result


def nearest_place(lat: float, lng: float) -> tuple[str, float]:
    """Nearest demo district name and distance in km."""
    best_name, best_d = None, float("inf")
    for p in GAZETTEER.values():
        d = haversine_km(lat, lng, p.lat, p.lng)
        if d < best_d:
            best_name, best_d = p.name, d
    return best_name, best_d  # type: ignore[return-value]


def geocode_district(district: str) -> tuple[float, float] | None:
    place = lookup(district)
    return (place.lat, place.lng) if place else None
