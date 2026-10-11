"""Client-side tools for the Travel Essentials agent. Plain functions so they're testable without the API."""

from __future__ import annotations

import json
from functools import cache
from pathlib import Path
from typing import Any

from super_travel.core.tools.fx import fetch_rate

DATA_DIR = Path(__file__).parent / "data"


@cache
def _country_data() -> dict[str, Any]:
    return json.loads((DATA_DIR / "country_info.json").read_text())


@cache
def _esim_plans() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "esim_plans.json").read_text())["plans"]


def get_country_info(country_code: str) -> str:
    """Get stable reference facts for a country: emergency numbers, plug types, voltage,
    driving side, tipping norms, tap water and currency. Does NOT cover advisories, entry
    rules, health notices or embassy contacts - use web search for those.

    Args:
        country_code: ISO 3166-1 alpha-2 code, e.g. "PT".
    """
    info = _country_data().get(country_code.upper())
    if info is None:
        return json.dumps({"error": f"No static data for {country_code}; use web search instead."})
    return json.dumps({"country_code": country_code.upper(), **info})


def get_exchange_rate(from_currency: str, to_currency: str, amount: float = 1.0) -> str:
    """Get the latest ECB reference exchange rate and convert an amount.
    Card and ATM rates are typically 1-3% worse than this reference rate.

    Args:
        from_currency: ISO 4217 code, e.g. "USD".
        to_currency: ISO 4217 code, e.g. "EUR".
        amount: Amount in from_currency to convert.
    """
    try:
        rate, as_of = fetch_rate(from_currency, to_currency)
    except Exception as exc:  # network or unknown currency: tell the model, don't crash the loop
        return json.dumps({"error": f"Rate lookup failed: {exc}"})
    return json.dumps({
        "from": from_currency.upper(), "to": to_currency.upper(), "rate": rate,
        "amount": amount, "converted": round(amount * rate, 2), "as_of": as_of,
        "source": "European Central Bank via frankfurter.dev",
    })


def find_esim_plans(country_codes: list[str], trip_days: int) -> str:
    """Find eSIM data plans that cover every listed country for at least the trip length.
    Results are sorted by price. Demo data: providers and prices are mock.

    Args:
        country_codes: ISO alpha-2 codes for all countries on the trip, e.g. ["PT", "ES"].
        trip_days: Number of days connectivity is needed.
    """
    wanted = {c.upper() for c in country_codes}
    matches = [
        p for p in _esim_plans()
        if wanted.issubset(p["countries"]) and p["days"] >= trip_days
    ]
    matches.sort(key=lambda p: p["price_usd"])
    if not matches:
        return json.dumps({"plans": [], "note": "No single plan covers all countries for that long; consider one plan per country."})
    return json.dumps({"plans": matches, "note": "MOCK DATA - providers and prices are fictional."})
