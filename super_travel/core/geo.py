"""Airport lookups and great-circle distance."""

from __future__ import annotations

import json
import math
from functools import cache
from pathlib import Path

_AIRPORTS_PATH = Path(__file__).parent / "data" / "airports.json"


@cache
def airports() -> dict[str, dict]:
    data = json.loads(_AIRPORTS_PATH.read_text())
    data.pop("_meta", None)
    return data


def airport(iata: str) -> dict:
    try:
        return airports()[iata.upper()]
    except KeyError:
        raise KeyError(f"Unknown airport {iata}; add it to core/data/airports.json") from None


def distance_km(from_iata: str, to_iata: str) -> float:
    a, b = airport(from_iata), airport(to_iata)
    lat1, lon1, lat2, lon2 = map(math.radians, (a["lat"], a["lon"], b["lat"], b["lon"]))
    h = math.sin((lat2 - lat1) / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


# Destination city -> country, timezone and a central point. Demo subset; extend as needed.
DESTINATIONS: dict[str, dict] = {
    "barcelona": {"country": "ES", "timezone": "Europe/Madrid", "currency": "EUR", "lat": 41.3851, "lon": 2.1734},
    "madrid": {"country": "ES", "timezone": "Europe/Madrid", "currency": "EUR", "lat": 40.4168, "lon": -3.7038},
    "lisbon": {"country": "PT", "timezone": "Europe/Lisbon", "currency": "EUR", "lat": 38.7223, "lon": -9.1393},
    "porto": {"country": "PT", "timezone": "Europe/Lisbon", "currency": "EUR", "lat": 41.1579, "lon": -8.6291},
    "paris": {"country": "FR", "timezone": "Europe/Paris", "currency": "EUR", "lat": 48.8566, "lon": 2.3522},
    "rome": {"country": "IT", "timezone": "Europe/Rome", "currency": "EUR", "lat": 41.9028, "lon": 12.4964},
    "berlin": {"country": "DE", "timezone": "Europe/Berlin", "currency": "EUR", "lat": 52.52, "lon": 13.405},
    "london": {"country": "GB", "timezone": "Europe/London", "currency": "GBP", "lat": 51.5072, "lon": -0.1276},
    "tokyo": {"country": "JP", "timezone": "Asia/Tokyo", "currency": "JPY", "lat": 35.6762, "lon": 139.6503},
    "bangkok": {"country": "TH", "timezone": "Asia/Bangkok", "currency": "THB", "lat": 13.7563, "lon": 100.5018},
    "mexico city": {"country": "MX", "timezone": "America/Mexico_City", "currency": "MXN", "lat": 19.4326, "lon": -99.1332},
    "new york": {"country": "US", "timezone": "America/New_York", "currency": "USD", "lat": 40.7128, "lon": -74.006},
}


def destination(name: str | None) -> dict | None:
    """Look up 'Barcelona' or 'Barcelona, Spain'. Returns None when unknown."""
    if not name:
        return None
    return DESTINATIONS.get(name.split(",")[0].strip().lower())
