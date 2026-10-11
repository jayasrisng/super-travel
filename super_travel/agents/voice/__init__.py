"""Voice agent: phones travel insurers for an urgent quote.

The calling itself sits behind `CallProvider`. The fixture provider simulates calls to
fictional insurers with templated transcripts; a real telephony/voice provider (e.g. the
Dial sponsor integration) can implement the same interface. Requirement checks and the
recommendation are deterministic code, never model output.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import date
from typing import Protocol
from uuid import NAMESPACE_URL, uuid5

from super_travel.control.schemas import VoiceQuoteInput, VoiceQuoteProposal


@dataclass(frozen=True)
class Insurer:
    key: str
    name: str
    phone: str
    behaviour: str  # fixture: "quote" | "decline" | "no_answer"; real calls: "dial"
    adult_cents_per_day: int = 0
    child_cents_per_day: int = 0
    medical_eur: int = 0
    deductible_eur: int = 0
    repatriation: bool = False
    schengen_compliant: bool = False
    delivery: str = "instant_pdf"
    decline_reason: str = ""


# Fictional insurers and numbers (555 range). Not real companies or prices.
FIXTURE_INSURERS = [
    Insurer("harbor", "Harbor Mutual Travel", "+1 555 010 2231", "quote", 210, 100, 20_000, 0, True, False),
    Insurer("solsea", "Sol & Sea Assurance", "+34 555 010 448", "quote", 320, 160, 50_000, 0, True, True),
    Insurer("atlas", "Atlas Cover International", "+44 555 010 7720", "quote", 450, 225, 100_000, 0, True, True),
    Insurer("meridian", "Meridian Travel Protect", "+1 555 010 9064", "decline",
            decline_reason="We can only sell a policy before the trip starts."),
    Insurer("northwind", "Northwind Insure", "+353 555 010 316", "no_answer"),
]


class CallProvider(Protocol):
    data_mode: str
    concurrency: int

    def call(self, insurer: Insurer, request: VoiceQuoteInput, brief: str, idempotency_key: str = "") -> dict: ...


def _eur(amount: int) -> str:
    return f"€{amount:,}"


class FixtureCallProvider:
    """Simulated calls with deterministic, templated transcripts."""

    data_mode = "fixture"
    concurrency = 1

    def call(self, insurer: Insurer, request: VoiceQuoteInput, brief: str, idempotency_key: str = "") -> dict:
        agent = lambda text: {"speaker": "voice_agent", "text": text}
        them = lambda text: {"speaker": "insurer", "text": text}
        opening = agent(f"Hi, I'm Wonder's AI travel assistant calling for a client. {brief} "
                        "They need travel insurance they can show at border control right now.")
        if insurer.behaviour == "no_answer":
            return {"outcome": "no_answer", "duration_seconds": 45, "provider_call_id": None, "transcript": [
                agent("Ringing… no answer after 45 seconds. Moving to the next insurer.")], "quote": None}
        if insurer.behaviour == "decline":
            return {"outcome": "declined", "duration_seconds": 72, "provider_call_id": None, "transcript": [
                opening, them(f"Thanks for calling {insurer.name}. {insurer.decline_reason}"),
                agent("Understood, thank you for your time.")], "quote": None}

        days = _days(request)
        premium = days * (request.adult_count * insurer.adult_cents_per_day
                          + (request.child_count + request.infant_count) * insurer.child_cents_per_day)
        transcript = [
            opening,
            them(f"{insurer.name}, happy to help. Can you confirm the travel dates and who's covered?"),
            agent(brief),
            them(f"For {days} days that's €{premium / 100:.2f} in total. Medical cover is {_eur(insurer.medical_eur)}"
                 f"{', including repatriation' if insurer.repatriation else ''}, with no deductible."),
            agent("Does that meet the Schengen standard, and can the certificate be issued immediately?"),
            them(("Yes, it meets the Schengen requirements" if insurer.schengen_compliant
                  else "It's not certified as Schengen-compliant")
                 + (", and the PDF certificate is issued the moment it's bound." if insurer.delivery == "instant_pdf"
                    else ", and documents are emailed within 24 hours.")),
            agent("Thank you. I'll pass this to the client's travel advisor for approval and call back to bind it."),
        ]
        quote = {
            "quote_id": f"{insurer.key}-{days}d",
            "insurer": insurer.name,
            "premium": {"amount_minor": premium, "currency": "EUR"},
            "medical_cover": {"amount_minor": insurer.medical_eur * 100, "currency": "EUR"},
            "deductible": {"amount_minor": insurer.deductible_eur * 100, "currency": "EUR"},
            "repatriation": insurer.repatriation,
            "schengen_compliant": insurer.schengen_compliant,
            "document_delivery": insurer.delivery,
            "meets_requirements": False,
            "notes": [],
        }
        return {"outcome": "quoted", "duration_seconds": 150 + 7 * len(insurer.name), "transcript": transcript,
                "quote": quote, "provider_call_id": None}


def _days(request: VoiceQuoteInput) -> int:
    if request.start_date and request.end_date:
        return (request.end_date - request.start_date).days + 1
    return 7


def _party(request: VoiceQuoteInput) -> str:
    parts = [f"{request.adult_count} adult{'s' if request.adult_count != 1 else ''}"]
    kids = request.child_count + request.infant_count
    if kids:
        ages = f" aged {', '.join(map(str, request.child_ages))}" if request.child_ages else ""
        parts.append(f"{kids} child{'ren' if kids != 1 else ''}{ages}")
    return " and ".join(parts)


def _dates(start: date | None, end: date | None) -> str:
    if not (start and end):
        return "for about a week"
    return f"from {start.strftime('%b %-d')} to {end.strftime('%b %-d, %Y')}"


def check(quote: dict, request: VoiceQuoteInput) -> dict:
    """Deterministic requirement check; fills meets_requirements and notes (keeping any extraction notes)."""
    extra = quote.get("notes", [])
    notes = []
    if quote["medical_cover"]["currency"] != request.min_medical.currency or \
            quote["medical_cover"]["amount_minor"] < request.min_medical.amount_minor:
        notes.append(f"Medical cover below the {_eur(request.min_medical.amount_minor // 100)} minimum.")
    if not quote["repatriation"]:
        notes.append("No repatriation cover.")
    if not quote["schengen_compliant"]:
        notes.append("Not certified as Schengen-compliant.")
    if request.need_document_now and quote["document_delivery"] != "instant_pdf":
        notes.append("Certificate not available immediately.")
    return {**quote, "meets_requirements": not notes, "notes": (notes or ["Meets every requirement."]) + extra}


def provider_from_env():
    """Dial when DIAL_ENABLED=true (real calls to DIAL_INSURER_NUMBERS only), else simulated calls."""
    if os.getenv("DIAL_ENABLED", "false").lower() != "true":
        return FixtureCallProvider(), FIXTURE_INSURERS
    from super_travel.agents.voice.dial import DialCallProvider, configured_insurers

    insurers = configured_insurers()
    if not insurers:
        raise RuntimeError("DIAL_ENABLED=true needs DIAL_INSURER_NUMBERS (team test numbers)")
    return DialCallProvider.from_env(), insurers


class VoiceQuoteAgent:
    name = "voice"
    needs_run_id = True

    def __init__(self, mode="fixture", provider: CallProvider | None = None, insurers=None):
        self.mode = mode
        if provider is None:
            provider, default_insurers = provider_from_env()
            insurers = insurers or default_insurers
        self.provider = provider
        self.insurers = insurers or FIXTURE_INSURERS

    def describe(self) -> str:
        if self.provider.data_mode == "live":
            return f"Live calls via Dial to {len(self.insurers)} configured test numbers; quotes read from transcripts"
        return "Simulated calls to fictional insurers; no real calls, purchases or policies"

    def propose(self, request: VoiceQuoteInput, now, run_id: str = "") -> VoiceQuoteProposal:
        destination = (request.destination or "the Schengen area").split(",")[0]
        brief = f"It's {_party(request)}, travelling in {destination} {_dates(request.start_date, request.end_date)}."

        def one(insurer: Insurer) -> dict:
            # Stable per run + insurer, so a retried run never dials the same insurer twice.
            key = str(uuid5(NAMESPACE_URL, f"wonder-voice/{run_id}/{insurer.phone}")) if run_id else ""
            result = self.provider.call(insurer, request, brief, key)
            if result["quote"]:
                result["quote"] = check(result["quote"], request)
            return {"item_id": f"call-{insurer.key}", "insurer": insurer.name, "phone": insurer.phone, **result}

        with ThreadPoolExecutor(max_workers=max(1, getattr(self.provider, "concurrency", 1))) as pool:
            calls = list(pool.map(one, self.insurers))

        eligible = [c["quote"] for c in calls if c["quote"] and c["quote"]["meets_requirements"]]
        best = min(eligible, key=lambda q: (q["premium"]["amount_minor"], q["insurer"])) if eligible else None
        quoted = sum(1 for c in calls if c["outcome"] == "quoted")
        reply = (f"Called {len(calls)} insurers, got {quoted} quotes. Cheapest that meets the requirements: "
                 f"{best['insurer']} at €{best['premium']['amount_minor'] / 100:.2f}." if best
                 else f"Called {len(calls)} insurers; none offered cover that meets the requirements.")
        live = self.provider.data_mode == "live"
        return VoiceQuoteProposal(
            reply=reply,
            assumptions=[
                "Real calls placed through Dial to the agency's configured numbers; prices are what each insurer said "
                "on the call and must be confirmed before binding." if live
                else "Simulated calls to fictional insurers; transcripts and prices are demo data.",
                "Nothing is bought until the advisor approves a quote."],
            sources=[],
            data_mode=self.provider.data_mode,
            requirements=[
                f"Medical cover of at least {_eur(request.min_medical.amount_minor // 100)} with repatriation (Schengen standard)",
                "Valid across the Schengen area for the whole trip",
                *(["Certificate available immediately (traveler is at the border)"] if request.need_document_now else []),
            ],
            calls=calls,
            recommended_quote_id=best["quote_id"] if best else None,
        )
