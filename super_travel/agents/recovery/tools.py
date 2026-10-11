"""Tools for the Manage & Recover agent.

Read tools are plain functions of the trip. Write tools only touch internal trip state
(incidents, expenses); anything irreversible goes out as a PendingAction for the user to confirm.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import cache
from pathlib import Path
from typing import Any, Literal

from super_travel.core import expenses as expense_math
from super_travel.core.tools.fx import convert
from super_travel.core.trip_context import TripContext
from super_travel.agents.recovery.rules import compensation

DATA_DIR = Path(__file__).parent / "data"


@cache
def _alternative_flights() -> list[dict[str, Any]]:
    return json.loads((DATA_DIR / "alternative_flights.json").read_text())["flights"]


def _segment(trip: TripContext, segment_id: str) -> dict[str, Any]:
    for seg in trip.segments:
        if seg["id"] == segment_id:
            return seg
    raise ValueError(f"No segment {segment_id}; valid ids: {[s['id'] for s in trip.segments]}")


class RecoveryTools:
    """Tools bound to one trip. Methods are wrapped with @beta_tool by the agent."""

    def __init__(self, trip: TripContext, convert_fn=convert) -> None:
        self.trip = trip
        self._convert = convert_fn

    # ---- read ---------------------------------------------------------------

    def get_flight_status(self, segment_id: str) -> str:
        """Get the live status of a booked flight segment: schedule plus any reported delay,
        cancellation or gate change. Demo: status comes from simulated events.

        Args:
            segment_id: Segment id from the trip, e.g. "s2".
        """
        seg = _segment(self.trip, segment_id)
        status = seg.get("live_status") or {"status": "scheduled", "note": "No disruption reported (mock feed)."}
        return json.dumps({k: seg.get(k) for k in ("id", "number", "carrier", "from", "to", "depart", "arrive", "travelers")} | {"live_status": status})

    def search_alternative_flights(self, from_iata: str, to_iata: str, date: str) -> str:
        """Search alternative flights between two airports on a date, for replanning options.
        Recovery does not book: hand rebooking to the planning agent. Demo: mock schedule data.

        Args:
            from_iata: Origin airport code, e.g. "LIS".
            to_iata: Destination airport code; connections via other airports are included.
            date: YYYY-MM-DD, local departure date.
        """
        results = [
            f for f in _alternative_flights()
            if f["from"] == from_iata.upper() and f["depart"].startswith(date)
            and (f["to"] == to_iata.upper() or to_iata.upper() in f.get("connects_to", ""))
        ]
        return json.dumps({"flights": results, "note": "MOCK DATA - fictional schedules."})

    def check_compensation(
        self,
        segment_id: str,
        event: Literal["delay", "cancellation", "denied_boarding"],
        arrival_delay_minutes: int = 0,
        extraordinary_circumstances: bool = False,
        notice_days: int | None = None,
        reroute_arrival_delay_minutes: int | None = None,
    ) -> str:
        """Determine passenger rights for a disrupted segment under EU261, the US DOT refund rule
        and related rules. Computed by deterministic code: always use this instead of reasoning
        about eligibility yourself, and quote its amounts exactly.

        Args:
            segment_id: Segment id from the trip.
            event: What happened.
            arrival_delay_minutes: Delay at the final destination, in minutes.
            extraordinary_circumstances: True for weather, ATC, security or strikes outside the airline.
            notice_days: For cancellations, days of notice before scheduled departure.
            reroute_arrival_delay_minutes: For cancellations, how late the offered reroute arrives.
        """
        seg = _segment(self.trip, segment_id)
        common = {"from_iata": seg["from"]["iata"], "to_iata": seg["to"]["iata"], "event": event,
                  "passengers": len(seg.get("travelers", [])) or 1}
        results = [
            compensation.assess_eu261(
                **common, carrier_code=seg["carrier_code"], arrival_delay_minutes=arrival_delay_minutes,
                extraordinary_circumstances=extraordinary_circumstances, notice_days=notice_days,
                reroute_arrival_delay_minutes=reroute_arrival_delay_minutes,
            ).to_dict(),
            compensation.assess_us_dot(**common, change_minutes=arrival_delay_minutes).to_dict(),
        ]
        return json.dumps({"segment_id": segment_id, "assessments": [r for r in results if r["applies"]] or results})

    def get_baggage_rights(self, kind: Literal["delayed", "lost", "damaged"]) -> str:
        """Get claim windows, liability limits and first steps for a baggage problem (Montreal Convention).

        Args:
            kind: delayed, lost or damaged.
        """
        return json.dumps(compensation.baggage_rights(kind))

    def reconcile_expenses(self) -> str:
        """Compute each traveler's net balance in the trip's home currency and the transfers that
        settle everyone up. Positive balance = is owed money. Computed by deterministic code."""
        home = self.trip.home.currency
        try:
            net = expense_math.balances(self.trip.expenses, home, self._convert)
        except Exception as exc:
            return json.dumps({"error": f"Could not reconcile: {exc}"})
        names = {t.id: t.name for t in self.trip.travelers}
        return json.dumps({
            "currency": home,
            "balances": {names.get(p, p): float(b) for p, b in net.items()},
            "transfers": [t | {"from": names.get(t["from"], t["from"]), "to": names.get(t["to"], t["to"])}
                          for t in expense_math.settle_up(net)],
            "expense_count": len(self.trip.expenses),
            "note": "Converted at ECB reference rates; card statements may differ by 1-3%.",
        })

    # ---- write (internal trip state only) ------------------------------------

    def open_incident(
        self,
        kind: Literal["flight_delay", "flight_cancellation", "missed_connection", "denied_boarding",
                      "baggage_delayed", "baggage_lost", "baggage_damaged", "booking_problem", "other"],
        summary: str,
        segment_id: str = "",
        traveler_ids: list[str] | None = None,
        reference: str = "",
    ) -> str:
        """Open an incident on the trip so it can be tracked through claims and follow-ups.
        Check existing incidents in the trip first; don't open a duplicate.

        Args:
            kind: Incident type.
            summary: One-line description.
            segment_id: Affected segment id, if any.
            traveler_ids: Affected travelers; empty means everyone on the segment.
            reference: Airline/airport reference such as a PIR number.
        """
        incident = {
            "id": f"i{len(self.trip.incidents) + 1}", "kind": kind, "summary": summary,
            "segment_id": segment_id or None, "traveler_ids": traveler_ids or [],
            "reference": reference or None, "status": "open", "claims": [],
            "opened_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self.trip.incidents.append(incident)
        return json.dumps(incident)

    def record_expense(
        self,
        description: str,
        amount: float,
        currency: str,
        payer: str,
        date: str,
        category: str,
        split: list[str] | None = None,
        incident_id: str = "",
        claimable: bool = False,
    ) -> str:
        """Record an expense on the trip, e.g. from a receipt or an out-of-pocket disruption cost.
        Use a negative amount for a refund received.

        Args:
            description: What it was.
            amount: Amount in the original currency.
            currency: ISO 4217 code.
            payer: Traveler id who paid.
            date: YYYY-MM-DD.
            category: e.g. food, transport, lodging, delayed_baggage, refund.
            split: Traveler ids sharing it equally; defaults to just the payer.
            incident_id: Link to an incident if this cost was caused by one.
            claimable: True if it can be claimed back from an airline, insurer or card.
        """
        if payer not in {t.id for t in self.trip.travelers}:
            raise ValueError(f"Unknown payer {payer}")
        expense = {
            "id": f"e{len(self.trip.expenses) + 1}", "date": date, "description": description,
            "amount": amount, "currency": currency.upper(), "category": category, "payer": payer,
            "split": split or [payer], "linked_to": incident_id or None, "claimable": claimable,
            "receipt_id": None, "recorded_by_agent": "recovery",
        }
        self.trip.expenses.append(expense)
        return json.dumps(expense)

    def as_list(self) -> list:
        return [
            self.get_flight_status, self.search_alternative_flights, self.check_compensation,
            self.get_baggage_rights, self.reconcile_expenses, self.open_incident, self.record_expense,
        ]
