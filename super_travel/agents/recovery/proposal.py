"""Deterministic Manage & Recover proposals for the control API (no model call).

Eligibility and amounts come only from rules/compensation.py. Anything that would leave
Wonder (claims, messages) is returned as a ProposedAction for a person to approve.
"""

from __future__ import annotations

from datetime import timedelta

from super_travel.agents.recovery.rules import compensation
from super_travel.control.schemas import RecoveryInput, RecoveryProposal

BAGGAGE_KIND = {"baggage_delayed": "delayed", "baggage_lost": "lost", "baggage_damaged": "damaged"}


def _rights(a: compensation.Assessment) -> dict:
    minor = lambda amount: {"amount_minor": round(amount * 100), "currency": a.currency} if a.eligible_for_compensation else None
    return {
        "regulation": a.regulation, "applies": a.applies, "eligible_for_compensation": a.eligible_for_compensation,
        "per_passenger": minor(a.amount_per_passenger), "total": minor(a.total), "passengers": a.passengers,
        "right_to_care": a.right_to_care, "right_to_refund": a.right_to_refund,
        "reasoning": a.reasoning or ["No applicable rule."], "caveats": a.caveats,
    }


class RecoveryProposalAgent:
    name = "recovery"

    def __init__(self, mode="fixture"):
        self.mode = mode

    def propose(self, request: RecoveryInput, now) -> RecoveryProposal:
        d = request.disruption
        if d is None:
            return self._readiness(request)
        if d.kind in BAGGAGE_KIND:
            return self._baggage(request, BAGGAGE_KIND[d.kind], now)
        return self._flight(request, now)

    def _readiness(self, request):
        start, end = request.start_date, request.end_date
        tasks = []
        if start:
            tasks += [
                {"item_id": "rec-home-mail", "title": "Hold mail and deliveries", "system": "manage_recover", "due_date": start - timedelta(days=3), "priority": "should"},
                {"item_id": "rec-home-house", "title": "Set thermostat, water plants, unplug appliances", "system": "manage_recover", "due_date": start - timedelta(days=1), "priority": "nice"},
                {"item_id": "rec-docs-copy", "title": "Save copies of bookings and insurance offline", "system": "manage_recover", "due_date": start - timedelta(days=1), "priority": "should"},
            ]
        if end:
            tasks.append({"item_id": "rec-post-refunds", "title": "Check for refunds or credits owed after the trip", "system": "manage_recover", "due_date": end + timedelta(days=3), "priority": "should"})
        return RecoveryProposal(
            reply="No disruptions reported. Home-prep and follow-up tasks are ready; report a delay, cancellation or bag problem to get rights and a claim draft.",
            assumptions=["Readiness checklist only; no flight data is monitored."],
            sources=[], data_mode="fixture", rights=[], baggage=None, actions=[], checklist_tasks=tasks,
        )

    def _flight(self, request, now):
        d, f = request.disruption, request.disruption.flight
        common = {"from_iata": f.from_iata, "to_iata": f.to_iata, "event": d.kind, "passengers": d.passengers}
        try:
            eu = compensation.assess_eu261(**common, carrier_code=f.carrier_code, arrival_delay_minutes=d.arrival_delay_minutes,
                                           extraordinary_circumstances=d.extraordinary_circumstances, notice_days=d.notice_days,
                                           reroute_arrival_delay_minutes=d.reroute_arrival_delay_minutes)
            us = compensation.assess_us_dot(**common, change_minutes=d.arrival_delay_minutes)
        except KeyError as exc:
            raise ValueError(str(exc)) from exc
        rights = [_rights(a) for a in (eu, us) if a.applies]
        actions, tasks = [], []
        what = {"delay": f"arrived {d.arrival_delay_minutes} minutes late", "cancellation": "was cancelled",
                "denied_boarding": "denied boarding to our party"}[d.kind]
        when = f" on {f.scheduled_date.isoformat()}" if f.scheduled_date else ""
        if eu.applies and eu.eligible_for_compensation:
            amount = {"amount_minor": round(eu.total * 100), "currency": "EUR"}
            actions.append({
                "item_id": "rec-claim-eu261", "kind": "send_claim", "high_stakes": True, "amount": amount,
                "summary": f"Send EU261 claim to {f.carrier_code} for {d.passengers} passenger{'s' if d.passengers > 1 else ''}",
                "recipient": f"{f.carrier_code} customer relations",
                "draft": (f"Flight {f.number} {f.from_iata}-{f.to_iata}{when} {what}"
                          f"{' for a reason within the airline’s control' if not d.extraordinary_circumstances else ''}. "
                          f"Under Regulation (EC) 261/2004 we claim EUR {eu.amount_per_passenger:.0f} per passenger for "
                          f"{d.passengers} passenger{'s' if d.passengers > 1 else ''} (EUR {eu.total:.0f} total)"
                          f"{f', booking reference {d.reference}' if d.reference else ''}. Passenger names: [add from booking]."),
            })
            tasks.append({"item_id": "rec-claim-followup", "title": f"Follow up on the {f.carrier_code} EU261 claim if there's no reply", "system": "manage_recover",
                          "due_date": (now + timedelta(days=30)).date(), "priority": "should"})
        if any(r["right_to_refund"] for r in rights) and d.kind == "cancellation":
            actions.append({"item_id": "rec-refund", "kind": "request_refund", "high_stakes": True, "summary": f"Ask {f.carrier_code} for a refund or reroute",
                            "recipient": f"{f.carrier_code} customer relations", "draft": f"Flight {f.number}{when} was cancelled. Please confirm a full refund to the original payment method, or rebooking on the next available flight."})
        if any(r["right_to_care"] for r in rights):
            tasks.append({"item_id": "rec-receipts", "title": "Keep receipts for meals and calls while waiting", "system": "manage_recover", "due_date": now.date(), "priority": "must"})
        eligible = [r for r in rights if r["eligible_for_compensation"]]
        reply = (f"{f.number} {what}. " + (f"The airline owes EUR {eu.total:.0f} under EU261; a claim draft is ready for review."
                 if eligible else "No cash compensation applies, but check the care and refund rights below."))
        return RecoveryProposal(reply=reply, assumptions=["Rights are computed by Wonder's rules code from the details reported; verify them against the airline's notice."],
                                sources=[], data_mode="fixture", rights=rights, baggage=None, actions=actions, checklist_tasks=tasks)

    def _baggage(self, request, kind, now):
        d = request.disruption
        rights = compensation.baggage_rights(kind)
        flight = f" on {d.flight.number}" if d.flight else ""
        ref = f" (report {d.reference})" if d.reference else ""
        deadline = {"delayed": 21, "lost": 21, "damaged": 7}[kind]
        carrier = d.flight.carrier_code if d.flight else "the airline"
        return RecoveryProposal(
            reply=f"Bag {kind}{flight}{ref}. Buy what you need and keep receipts; the claim must be in writing within {deadline} days{' of getting the bag back' if kind != 'lost' else ''}.",
            assumptions=["Liability cap under the Montreal Convention; the airline may require its own form."],
            sources=[], data_mode="fixture", rights=[], baggage=rights,
            actions=[{"item_id": "rec-claim-bag", "kind": "send_claim", "high_stakes": True, "summary": f"Send {kind}-baggage claim to {carrier}",
                      "recipient": f"{carrier} baggage services",
                      "draft": f"Our bag{flight} was {kind}{ref}. Under the Montreal Convention we claim reasonable costs for essentials bought meanwhile; itemised receipts attached."}],
            checklist_tasks=[{"item_id": "rec-bag-receipts", "title": "Keep every receipt for essentials", "system": "manage_recover", "due_date": now.date(), "priority": "must"},
                             {"item_id": "rec-bag-deadline", "title": f"Submit the written baggage claim (within {deadline} days)", "system": "manage_recover",
                              "due_date": (now + timedelta(days=deadline)).date(), "priority": "must"}],
        )
