"""Geospatial helpers (delegates to the ml gazetteer implementation)."""

from ml.preprocessing.gazetteer import (ALL_DISTRICTS, GAZETTEER,  # noqa: F401
                                        Place, haversine_km, lookup,
                                        nearest_district)
