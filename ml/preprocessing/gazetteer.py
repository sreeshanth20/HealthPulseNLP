"""Synthetic demo gazetteer.

Riverton is a FICTIONAL demo city created for the HealthPulse AI demonstration
dataset. Coordinates are synthetic; they do not correspond to any real locality.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Place:
    name: str
    district: str
    lat: float
    lng: float
    pincode: str
    aliases: tuple[str, ...] = ()


# A compact fictional city: 8 districts around a synthetic centre.
GAZETTEER: dict[str, Place] = {}
_place_rows = [
    ("Harbourview", 17.6901, 83.2105, "530001", ("harbour", "harbor view", "harbour view")),
    ("Millbrook", 17.6968, 83.2204, "530002", ("mill brook", "millbrook ward")),
    ("Eastfields", 17.6849, 83.2318, "530003", ("east fields", "eastfield")),
    ("Old Town", 17.7032, 83.2091, "530004", ("oldtown", "old city")),
    ("Northgate", 17.7120, 83.2188, "530005", ("north gate", "northgate ward")),
    ("Riverside", 17.6790, 83.2002, "530006", ("river side", "riverbank")),
    ("Greenhills", 17.7058, 83.2325, "530007", ("green hills", "greenhill")),
    ("Southbay", 17.6735, 83.2189, "530008", ("south bay", "southbay beach")),
]
for name, lat, lng, pin, aliases in _place_rows:
    GAZETTEER[name.lower()] = Place(name, name, lat, lng, pin, tuple(aliases))

ALL_DISTRICTS: list[str] = [p.name for p in GAZETTEER.values()]

_DISTRICT_LOOKUP: dict[str, Place] = {}
for _p in GAZETTEER.values():
    _DISTRICT_LOOKUP[_p.name.lower()] = _p
    for _a in _p.aliases:
        _DISTRICT_LOOKUP[_a] = _p


def lookup(place_text: str) -> Place | None:
    """Case-insensitive lookup by district name or alias."""
    if not place_text:
        return None
    return _DISTRICT_LOOKUP.get(place_text.strip().lower())


def nearest_district(lat: float, lng: float) -> tuple[str, float]:
    """Nearest district and its distance in km (haversine)."""
    import math

    best: tuple[str, float] | None = None
    for p in GAZETTEER.values():
        d = haversine_km(lat, lng, p.lat, p.lng)
        if best is None or d < best[1]:
            best = (p.name, d)
    return best  # type: ignore[return-value]


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two WGS84 points, in kilometres."""
    import math

    r = 6371.0088
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))
