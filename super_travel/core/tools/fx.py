"""Exchange rates via Frankfurter (ECB reference rates; free, no key). Shared by agents 4 and 5."""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from functools import lru_cache

FRANKFURTER_URL = "https://api.frankfurter.dev/v1/latest"


@lru_cache(maxsize=128)
def fetch_rate(from_currency: str, to_currency: str) -> tuple[float, str]:
    """Returns (rate, as_of_date). Raises on network errors or unknown currencies."""
    from_currency, to_currency = from_currency.upper(), to_currency.upper()
    if from_currency == to_currency:
        return 1.0, "n/a"
    query = urllib.parse.urlencode({"from": from_currency, "to": to_currency})
    # Frankfurter's CDN rejects urllib's default User-Agent with a 403.
    request = urllib.request.Request(f"{FRANKFURTER_URL}?{query}", headers={"User-Agent": "super-travel/0.1"})
    with urllib.request.urlopen(request, timeout=10) as resp:
        body = json.load(resp)
    return float(body["rates"][to_currency]), body["date"]


def convert(amount: float, from_currency: str, to_currency: str) -> float:
    rate, _ = fetch_rate(from_currency, to_currency)
    return round(amount * rate, 2)
