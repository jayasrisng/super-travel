"""Real outbound calls through Dial (https://docs.getdial.ai).

Only numbers listed in DIAL_INSURER_NUMBERS are ever dialled (team test numbers playing
insurers). The voice agent never gives payment or personal details and never buys anything:
it asks for a quote and says the advisor will call back to bind it.

Config (.env):
  DIAL_ENABLED=true
  DIAL_API_KEY=sk_live_...           # never commit
  DIAL_SENDER_NUMBER=pn_... | +1...  # the Dial number to call from (ID, E.164 or nickname)
  DIAL_INSURER_NUMBERS="Sol & Sea Assurance=+16105550100;Atlas Cover=+16105550101"
  DIAL_MAX_CALL_SECONDS=120          # per-call cap
"""

from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import Callable

from super_travel.agents.voice import Insurer
from super_travel.agents.voice.extract import extract_quote
from super_travel.control.schemas import VoiceQuoteInput

DEFAULT_BASE_URL = "https://api.getdial.ai"
TERMINAL_STATES = {"Terminated"}


class DialError(RuntimeError):
    pass


def configured_insurers(raw: str | None = None) -> list[Insurer]:
    """Parse 'Name=+1555...;Other=+1555...' into insurers. Only these numbers are dialled."""
    raw = os.getenv("DIAL_INSURER_NUMBERS", "") if raw is None else raw
    insurers = []
    for chunk in filter(None, (c.strip() for c in raw.split(";"))):
        name, _, phone = chunk.rpartition("=")
        phone = phone.strip()
        if not name.strip() or not phone.startswith("+") or not phone[1:].isdigit():
            raise ValueError(f"Bad DIAL_INSURER_NUMBERS entry {chunk!r}; use 'Name=+15555550100'")
        key = "".join(ch for ch in name.lower() if ch.isalnum())[:24] or "insurer"
        insurers.append(Insurer(key=key, name=name.strip(), phone=phone, behaviour="dial"))
    return insurers


def outbound_instruction(insurer: Insurer, request: VoiceQuoteInput, brief: str) -> str:
    minimum = request.min_medical.amount_minor // 100
    return (
        f"You are Wonder's AI travel assistant, calling {insurer.name} on behalf of a travel agency to get a "
        "travel-insurance quote for a client who is at border control right now and needs proof of cover. "
        f"Client details: {brief} Do not give names, dates of birth, passport numbers or payment details, "
        "and do not agree to buy anything: say the client's travel advisor will call back to bind the policy. "
        "Ask, one at a time: 1) the total price in euros for the whole trip, 2) the medical expenses limit, "
        f"which must be at least {minimum:,} euros, 3) whether repatriation is included, 4) whether the policy "
        "meets Schengen travel-insurance requirements, 5) whether a certificate can be issued immediately as a PDF. "
        "Repeat the price and medical limit back to confirm them. Be brief and polite. If they cannot quote, "
        "thank them and end the call. End the call once you have the answers."
    )


class DialCallProvider:
    data_mode = "live"
    concurrency = 2  # free Dial accounts allow 2 concurrent calls

    def __init__(
        self,
        api_key: str,
        from_number: str,
        *,
        base_url: str = DEFAULT_BASE_URL,
        max_call_seconds: int = 120,
        poll_seconds: float = 3.0,
        wait_seconds: float = 300.0,
        transport: Callable | None = None,
        extractor: Callable = extract_quote,
        sleep: Callable[[float], None] = time.sleep,
    ):
        if not api_key or not from_number:
            raise DialError("DIAL_API_KEY and DIAL_SENDER_NUMBER are required")
        self.api_key, self.from_number = api_key, from_number
        self.base_url = base_url.rstrip("/")
        self.max_call_seconds, self.poll_seconds, self.wait_seconds = max_call_seconds, poll_seconds, wait_seconds
        self.transport = transport or self._http
        self.extractor, self.sleep = extractor, sleep

    @classmethod
    def from_env(cls) -> DialCallProvider:
        return cls(
            os.getenv("DIAL_API_KEY", ""),
            os.getenv("DIAL_SENDER_NUMBER", ""),
            base_url=os.getenv("DIAL_API_URL", DEFAULT_BASE_URL),
            max_call_seconds=int(os.getenv("DIAL_MAX_CALL_SECONDS", "120")),
        )

    def _http(self, method: str, path: str, body: dict | None = None, headers: dict | None = None) -> tuple[int, dict]:
        request = urllib.request.Request(
            self.base_url + path,
            data=json.dumps(body).encode() if body is not None else None,
            method=method,
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json",
                     "User-Agent": "wonder-voice-agent/0.1", **(headers or {})},
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                return response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            try:
                payload = json.load(exc)
            except Exception:  # noqa: BLE001
                payload = {}
            return exc.code, payload

    def call(self, insurer: Insurer, request: VoiceQuoteInput, brief: str, idempotency_key: str = "") -> dict:
        status, payload = self.transport(
            "POST", "/api/v1/calls",
            {"to": insurer.phone, "fromNumber": self.from_number, "language": "en-US",
             "outboundInstruction": outbound_instruction(insurer, request, brief),
             "maxCallDurationSeconds": self.max_call_seconds},
            {"Idempotency-Key": idempotency_key} if idempotency_key else None,
        )
        if status not in (200, 201):
            reason = payload.get("error") if isinstance(payload, dict) else None
            reason = reason if isinstance(reason, str) else f"HTTP {status}"
            hint = {402: "Dial account is out of credit.", 403: "Dial can't reach this number's region.",
                    429: "Dial concurrent-call limit reached.", 401: "Dial API key was rejected."}.get(status, "")
            return {"outcome": "failed", "duration_seconds": 0, "provider_call_id": None, "quote": None,
                    "transcript": [{"speaker": "voice_agent", "text": f"Could not place the call: {hint or reason}"}]}

        call = payload["call"]
        call = self._wait(call["id"], call)
        state = call.get("status") or {}
        ended = state.get("terminationType")
        turns = call.get("transcriptTurns") or []
        transcript = [
            {"speaker": "voice_agent" if t.get("speaker") == "agent" else "insurer", "text": t.get("text", "")[:2000]}
            for t in turns if t.get("text")
        ][:40]
        base = {"duration_seconds": min(int(call.get("duration") or 0), 3600), "provider_call_id": call.get("id")}
        if state.get("state") not in TERMINAL_STATES:
            return {**base, "outcome": "failed", "quote": None,
                    "transcript": transcript or [{"speaker": "voice_agent", "text": "Call did not finish in time."}]}
        if ended in ("no-answer", "busy", "canceled") or not any(t["speaker"] == "insurer" for t in transcript):
            return {**base, "outcome": "no_answer", "quote": None,
                    "transcript": transcript or [{"speaker": "voice_agent", "text": f"No answer ({ended or 'no speech'})."}]}
        if ended == "failed":
            return {**base, "outcome": "failed", "quote": None, "transcript": transcript}
        quote = self.extractor(insurer, transcript)
        return {**base, "outcome": "quoted" if quote else "declined", "quote": quote, "transcript": transcript}

    def _wait(self, call_id: str, call: dict) -> dict:
        """Poll until the call is over and (if there was speech) its transcript has landed."""
        deadline = time.monotonic() + self.wait_seconds
        terminated_at = None
        while time.monotonic() < deadline:
            state = (call.get("status") or {}).get("state")
            if state in TERMINAL_STATES:
                terminated_at = terminated_at or time.monotonic()
                answered = (call.get("status") or {}).get("terminationType") == "completed"
                # call.transcribed follows call.ended by a few seconds; give it up to 30s.
                if not answered or call.get("transcriptTurns") or time.monotonic() - terminated_at > 30:
                    return call
            self.sleep(self.poll_seconds)
            status, payload = self.transport("GET", f"/api/v1/calls/{call_id}", None, None)
            if status == 200 and isinstance(payload, dict) and payload.get("call"):
                call = payload["call"]
        return call
