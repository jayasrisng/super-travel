"""Deterministic passenger-rights rules. Eligibility comes from code, never from the LLM.

Implemented:
- EU261/2004 (EU/EEA/CH): delay, cancellation, denied boarding, right to care, right to refund.
- US DOT refund rule (2024): automatic refund for cancellations and significant changes.
- Montreal Convention: delayed / lost / damaged baggage claim windows and liability cap.

Not implemented (returned as caveats): UK261, Canada APPR, the EU261 "departed up to N hours earlier"
reroute conditions, and per-airline goodwill policies.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Literal

from super_travel.core.geo import airport, distance_km

EU261_COUNTRIES = {
    "AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE", "IT", "LV",
    "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE",
    "IS", "NO", "CH",  # EEA + Switzerland apply EU261
}
# Operating carrier code -> country of licence (demo subset).
CARRIER_COUNTRY = {
    "TP": "PT", "VY": "ES", "IB": "ES", "UX": "ES", "FR": "IE", "EI": "IE", "AF": "FR", "KL": "NL",
    "LH": "DE", "AZ": "IT", "SK": "SE", "BA": "GB", "U2": "GB", "UA": "US", "AA": "US", "DL": "US",
    "AS": "US", "B6": "US", "WN": "US", "JL": "JP", "NH": "JP", "TG": "TH", "AI": "IN", "AM": "MX",
}

EventType = Literal["delay", "cancellation", "denied_boarding"]


@dataclass
class Assessment:
    regulation: str
    applies: bool
    eligible_for_compensation: bool = False
    amount_per_passenger: float = 0.0
    currency: str = ""
    passengers: int = 1
    total: float = 0.0
    right_to_care: list[str] = field(default_factory=list)
    right_to_refund: bool = False
    reasoning: list[str] = field(default_factory=list)
    caveats: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


def _distance_band(km: float, intra_eu: bool) -> tuple[int, int, int]:
    """Returns (amount EUR, care threshold minutes, long-haul reduction threshold minutes)."""
    if km <= 1500:
        return 250, 120, 0
    if intra_eu or km <= 3500:
        return 400, 180, 0
    return 600, 240, 240


def assess_eu261(
    *,
    from_iata: str,
    to_iata: str,
    carrier_code: str,
    event: EventType,
    passengers: int,
    arrival_delay_minutes: int = 0,
    extraordinary_circumstances: bool = False,
    notice_days: int | None = None,
    reroute_arrival_delay_minutes: int | None = None,
    voluntary: bool = False,
) -> Assessment:
    origin, dest = airport(from_iata)["country"], airport(to_iata)["country"]
    carrier_country = CARRIER_COUNTRY.get(carrier_code.upper())
    departs_eu = origin in EU261_COUNTRIES
    arrives_eu_on_eu_carrier = dest in EU261_COUNTRIES and carrier_country in EU261_COUNTRIES
    a = Assessment(regulation="EU261", applies=departs_eu or arrives_eu_on_eu_carrier, passengers=passengers)

    if carrier_country is None:
        a.caveats.append(f"Carrier {carrier_code} not in the carrier table; EU-carrier status assumed non-EU.")
    if not a.applies:
        a.reasoning.append(f"Flight {from_iata}->{to_iata} neither departs the EU nor arrives on an EU carrier.")
        return a
    a.reasoning.append("Departs from an EU/EEA/CH airport." if departs_eu else "Arrives in the EU on an EU carrier.")

    km = distance_km(from_iata, to_iata)
    intra_eu = departs_eu and dest in EU261_COUNTRIES
    amount, care_threshold, reduction_threshold = _distance_band(km, intra_eu)
    a.reasoning.append(f"Distance {km:.0f} km{' (intra-EU)' if intra_eu else ''}: band EUR {amount}.")

    if event == "delay":
        if arrival_delay_minutes >= care_threshold:
            a.right_to_care = ["meals and refreshments", "two phone calls or emails"]
        if arrival_delay_minutes >= 300:
            a.right_to_refund = True
            a.reasoning.append("Delay of 5h+: right to a refund instead of travelling.")
        if arrival_delay_minutes < 180:
            a.reasoning.append(f"Arrival delay {arrival_delay_minutes} min is under 3h: no compensation.")
            return _finish(a, 0)
        if reduction_threshold and arrival_delay_minutes < reduction_threshold:
            amount //= 2
            a.reasoning.append("Long-haul delay between 3h and 4h: compensation reduced by 50%.")
        a.reasoning.append(f"Arrival delay {arrival_delay_minutes} min is 3h or more.")
        a.caveats.append("Care thresholds are measured from departure delay; arrival delay used as a proxy.")
    elif event == "cancellation":
        a.right_to_refund = True
        a.right_to_care = ["meals and refreshments", "two phone calls or emails", "hotel and transfers if overnight"]
        if notice_days is not None and notice_days >= 14:
            a.reasoning.append("Cancellation notified 14+ days before departure: no compensation.")
            return _finish(a, 0)
        reroute = reroute_arrival_delay_minutes
        if reroute is not None and notice_days is not None:
            if 7 <= notice_days < 14 and reroute <= 240:
                a.reasoning.append("Notified 7-13 days ahead and rerouted to arrive within 4h: no compensation.")
                a.caveats.append("Also requires the reroute to depart no more than 2h earlier; not checked.")
                return _finish(a, 0)
            if notice_days < 7 and reroute <= 120:
                a.reasoning.append("Notified under 7 days ahead and rerouted to arrive within 2h: no compensation.")
                a.caveats.append("Also requires the reroute to depart no more than 1h earlier; not checked.")
                return _finish(a, 0)
        if reroute is not None and reroute <= {250: 120, 400: 180, 600: 240}[amount]:
            amount //= 2
            a.reasoning.append("Reroute arrives within the Article 7(2) window: compensation reduced by 50%.")
        a.reasoning.append("Cancellation with short notice: compensation due.")
    elif event == "denied_boarding":
        a.right_to_refund = True
        if voluntary:
            a.reasoning.append("Volunteered to give up the seat: compensation is whatever was agreed with the airline.")
            return _finish(a, 0)
        a.reasoning.append("Involuntary denied boarding: compensation due.")

    if extraordinary_circumstances:
        a.reasoning.append("Extraordinary circumstances (e.g. weather, ATC strike): no compensation, care still owed.")
        return _finish(a, 0)
    return _finish(a, amount)


def _finish(a: Assessment, amount: float) -> Assessment:
    a.amount_per_passenger = float(amount)
    a.currency = "EUR"
    a.total = float(amount * a.passengers)
    a.eligible_for_compensation = amount > 0
    return a


def assess_us_dot(
    *,
    from_iata: str,
    to_iata: str,
    event: EventType,
    passengers: int,
    change_minutes: int = 0,
    accepted_alternative: bool = False,
) -> Assessment:
    countries = {airport(from_iata)["country"], airport(to_iata)["country"]}
    a = Assessment(regulation="US DOT refund rule", applies="US" in countries, passengers=passengers)
    a.caveats.append("US law gives no cash compensation for delays; some airlines offer meal or hotel vouchers.")
    if not a.applies:
        a.reasoning.append("Flight does not touch the US.")
        return a
    domestic = countries == {"US"}
    threshold = 180 if domestic else 360
    if event == "cancellation":
        a.right_to_refund = not accepted_alternative
        a.reasoning.append("Cancelled: automatic cash refund unless an alternative was accepted.")
    elif event == "delay" and change_minutes >= threshold:
        a.right_to_refund = not accepted_alternative
        a.reasoning.append(
            f"Significant change ({change_minutes} min >= {threshold} min {'domestic' if domestic else 'international'}): "
            "refund if the traveler doesn't accept it."
        )
    else:
        a.reasoning.append("No significant change: no refund right.")
    return a


MONTREAL_BAGGAGE_LIMIT_SDR = 1519  # per passenger, ICAO-revised limit effective 28 Dec 2024


def baggage_rights(kind: Literal["delayed", "lost", "damaged"]) -> dict:
    windows = {
        "delayed": "Written claim within 21 days of receiving the bag. Keep receipts for reasonable interim purchases (toiletries, essential clothing).",
        "lost": "A bag still missing after 21 days is treated as lost. File a written claim with an itemised list of contents and values.",
        "damaged": "Written complaint within 7 days of receiving the bag, with photos.",
    }
    return {
        "regulation": "Montreal Convention",
        "kind": kind,
        "claim_window": windows[kind],
        "liability_cap": f"{MONTREAL_BAGGAGE_LIMIT_SDR} SDR per passenger (roughly USD 2,000; SDR rate varies)",
        "first_step": "Report at the airport before leaving and get a Property Irregularity Report (PIR) reference.",
        "also_check": ["travel insurance baggage-delay cover", "credit card baggage-delay benefits"],
    }
