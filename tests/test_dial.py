"""Dial voice provider against a fake Dial API (no real calls)."""

from datetime import UTC, date, datetime

import pytest

from super_travel.agents.voice import VoiceQuoteAgent
from super_travel.agents.voice.dial import (
    DialCallProvider,
    configured_insurers,
    outbound_instruction,
)
from super_travel.agents.voice.extract import extract_quote
from super_travel.control.schemas import VoiceQuoteInput

REQUEST = VoiceQuoteInput(destination="Barcelona, Spain", start_date=date(2026, 10, 11), end_date=date(2026, 10, 17),
                          child_count=1, child_ages=[6])
NOW = datetime(2026, 10, 11, 12, tzinfo=UTC)

GOOD_CALL = [
    {"speaker": "agent", "text": "Hi, I'm Wonder's AI travel assistant calling for a quote."},
    {"speaker": "user", "text": "Sure. For one adult and one child for seven days that's 41 euros total."},
    {"speaker": "agent", "text": "What is the medical limit, and is repatriation included?"},
    {"speaker": "user", "text": "Medical cover is 60,000 euros including repatriation, and it meets Schengen requirements."},
    {"speaker": "agent", "text": "Can the certificate be issued immediately?"},
    {"speaker": "user", "text": "Yes, we email the PDF right away."},
]
CHEAP_BAD_CALL = [
    {"speaker": "agent", "text": "Hi, calling for a quote."},
    {"speaker": "user", "text": "It's 25 euros. Medical cover is 20,000 euros, no repatriation, and it's not Schengen certified."},
]


class FakeDial:
    """Scripted Dial API: POST /api/v1/calls then GET polls that progress to Terminated."""

    def __init__(self, scripts, post_status=201):
        self.scripts, self.post_status = scripts, post_status
        self.posts, self.calls, self.polls = [], {}, {}

    def __call__(self, method, path, body, headers):
        if method == "POST":
            self.posts.append({"body": body, "headers": headers or {}})
            if self.post_status not in (200, 201):
                return self.post_status, {"error": "insufficient_credit"}
            key = (headers or {}).get("Idempotency-Key")
            existing = next((cid for cid, c in self.calls.items() if key and c["key"] == key), None)
            if existing:
                return 200, {"call": self._view(existing)}
            cid = f"call_{len(self.calls) + 1}"
            ending, turns = self.scripts[body["to"]]
            self.calls[cid] = {"key": key, "to": body["to"], "ending": ending, "turns": turns}
            self.polls[cid] = 0
            return 201, {"call": {"id": cid, "status": {"state": "Queued"}}}
        cid = path.rsplit("/", 1)[-1]
        self.polls[cid] += 1
        return 200, {"call": self._view(cid)}

    def _view(self, cid):
        c, n = self.calls[cid], self.polls[cid]
        if n < 2:
            return {"id": cid, "status": {"state": "In-Progress" if n else "Ringing"}}
        done = {"id": cid, "duration": 64, "status": {"state": "Terminated", "terminationType": c["ending"]}}
        return done | ({"transcriptTurns": c["turns"]} if n >= 3 and c["ending"] == "completed" else {})


INSURERS = "Sol & Sea (Kavish)=+16105550100;Harbor (Dana)=+16105550101;Northwind (Sam)=+16105550102"


def provider(fake):
    return DialCallProvider("sk_live_test", "pn_wonder", transport=fake, poll_seconds=0, sleep=lambda s: None,
                            extractor=extract_quote)


def test_configured_insurers_parsing():
    insurers = configured_insurers(INSURERS)
    assert [i.phone for i in insurers] == ["+16105550100", "+16105550101", "+16105550102"]
    with pytest.raises(ValueError):
        configured_insurers("Bad=5550100")


def test_live_calls_quotes_and_recommendation(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)  # keyword-rule extraction, offline
    fake = FakeDial({"+16105550100": ("completed", GOOD_CALL), "+16105550101": ("completed", CHEAP_BAD_CALL),
                     "+16105550102": ("no-answer", [])})
    agent = VoiceQuoteAgent(provider=provider(fake), insurers=configured_insurers(INSURERS))
    proposal = agent.propose(REQUEST, NOW, run_id="run-1")

    assert proposal.data_mode == "live" and len(fake.posts) == 3
    first = fake.posts[0]
    assert first["body"]["fromNumber"] == "pn_wonder" and first["body"]["maxCallDurationSeconds"] == 120
    assert first["headers"]["Idempotency-Key"]
    assert "Sarah" not in first["body"]["outboundInstruction"] and "30,000" in first["body"]["outboundInstruction"]

    calls = {c.insurer: c for c in proposal.calls}
    good, bad, none = calls["Sol & Sea (Kavish)"], calls["Harbor (Dana)"], calls["Northwind (Sam)"]
    assert good.outcome == "quoted" and good.provider_call_id and good.quote.premium.amount_minor == 4100
    assert good.quote.medical_cover.amount_minor == 6_000_000 and good.quote.meets_requirements
    assert bad.outcome == "quoted" and not bad.quote.meets_requirements
    assert none.outcome == "no_answer" and none.quote is None
    assert proposal.recommended_quote_id == good.quote.quote_id
    assert good.transcript[1].speaker == "insurer"


def test_retry_reuses_idempotency_key_so_no_second_call(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    fake = FakeDial({"+16105550100": ("completed", GOOD_CALL)})
    insurers = configured_insurers("Sol & Sea=+16105550100")
    VoiceQuoteAgent(provider=provider(fake), insurers=insurers).propose(REQUEST, NOW, run_id="run-1")
    VoiceQuoteAgent(provider=provider(fake), insurers=insurers).propose(REQUEST, NOW, run_id="run-1")
    assert len(fake.calls) == 1 and len(fake.posts) == 2  # second POST replayed the same call


def test_dial_rejection_is_reported_not_raised(monkeypatch):
    fake = FakeDial({}, post_status=402)
    proposal = VoiceQuoteAgent(provider=provider(fake), insurers=configured_insurers("A=+16105550100")).propose(
        REQUEST, NOW, run_id="r")
    assert proposal.calls[0].outcome == "failed" and "credit" in proposal.calls[0].transcript[0].text
    assert proposal.recommended_quote_id is None


def test_unconfirmed_fields_fail_safe(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    turns = [{"speaker": "insurer", "text": "We can do it for 30 euros."}]
    quote = extract_quote(configured_insurers("A=+16105550100")[0], turns)
    assert quote["premium"]["amount_minor"] == 3000 and not quote["repatriation"]
    assert any("not confirmed" in n for n in quote["notes"])


def test_provider_from_env_requires_numbers(monkeypatch):
    from super_travel.agents.voice import provider_from_env
    monkeypatch.setenv("DIAL_ENABLED", "true")
    monkeypatch.setenv("DIAL_API_KEY", "sk_live_x")
    monkeypatch.setenv("DIAL_SENDER_NUMBER", "pn_x")
    monkeypatch.setenv("DIAL_INSURER_NUMBERS", "")
    with pytest.raises(RuntimeError):
        provider_from_env()
    monkeypatch.setenv("DIAL_INSURER_NUMBERS", INSURERS)
    provider, insurers = provider_from_env()
    assert provider.data_mode == "live" and len(insurers) == 3
    monkeypatch.setenv("DIAL_ENABLED", "false")
    assert provider_from_env()[0].data_mode == "fixture"


def test_instruction_mentions_requirements_not_personal_data():
    text = outbound_instruction(configured_insurers("A=+16105550100")[0], REQUEST, "It's 1 adult and 1 child aged 6.")
    assert "do not agree to buy" in text.lower() and "passport" in text.lower()


def test_claude_extraction_path(monkeypatch):
    import json

    from tests.fake_api import fake_messages_api, text
    payload = {"quoted": True, "premium": 38.5, "currency": "EUR", "medical_cover": 50000, "repatriation": True,
               "schengen_compliant": True, "instant_certificate": None}
    with fake_messages_api([text(json.dumps(payload))], monkeypatch) as seen:
        quote = extract_quote(configured_insurers("A=+16105550100")[0], [{"speaker": "insurer", "text": "38.50 euros"}])
    body = seen[0]["body"]
    assert body["output_config"]["format"]["type"] == "json_schema" and body["fallbacks"] == "default"
    assert quote["premium"]["amount_minor"] == 3850 and quote["document_delivery"] == "email_24h"
    assert any("Claude" in n for n in quote["notes"]) and any("Immediate certificate" in n for n in quote["notes"])
