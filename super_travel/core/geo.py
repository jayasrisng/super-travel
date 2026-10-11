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
