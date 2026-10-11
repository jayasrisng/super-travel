"""The orchestrator: talks to the user, delegates to specialists, merges their results.

- User messages go through Claude, which routes via a single `delegate(agent, task)` tool.
- App events are routed deterministically (EVENT_ROUTES), then handoffs are followed one level.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Any

from anthropic import beta_tool

from super_travel.agents import EVENT_ROUTES, PLANNED, REGISTRY
from super_travel.core import llm
from super_travel.core.agent import Agent, AgentResult, Handoff, PendingAction
from super_travel.core.trip_context import TripContext

SYSTEM_PROMPT = (Path(__file__).parent / "prompt.md").read_text()
MAX_DELEGATIONS_PER_TURN = 6
MAX_ITERATIONS = 10


@dataclass
class Delegation:
    agent: str
    task: str
    status: str  # "ok" | "unavailable" | "error" | "limit"
    result: AgentResult | None = None
    error: str = ""


@dataclass
class TurnResult:
    reply: str
    delegations: list[Delegation] = field(default_factory=list)
    pending_actions: list[dict[str, Any]] = field(default_factory=list)  # each with an id, for confirm cards
    open_handoffs: list[Handoff] = field(default_factory=list)  # to agents that aren't built or weren't followed
    user_content: str = ""  # the exact user turn sent to the model (for append-only history)

    @property
    def cards(self) -> dict[str, list[dict[str, Any]]]:
        """Structured payloads per agent, for the UI."""
        out: dict[str, list[dict[str, Any]]] = {}
        for d in self.delegations:
            if d.result is not None:
                out.setdefault(d.agent, []).append(d.result.data)
        return out


def _delegate_description(registry: dict[str, Agent]) -> str:
    lines = ["Delegate a task to a specialist agent and get its result. Agents:"]
    lines += [f"- {name}: {agent.description}" for name, agent in sorted(registry.items())]
    lines += [f"- {name} (NOT YET AVAILABLE): {desc}" for name, desc in sorted(PLANNED.items())]
    return "\n".join(lines)


class Orchestrator:
    def __init__(self, registry: dict[str, Agent] | None = None) -> None:
        self.registry = registry if registry is not None else REGISTRY
        self._agent_names = sorted({*self.registry, *PLANNED})
        self._delegate_schema = {
            "type": "object",
            "properties": {
                "agent": {"type": "string", "enum": self._agent_names},
                "task": {"type": "string", "description": "Self-contained instruction for the agent, including relevant context from the conversation."},
            },
            "required": ["agent", "task"],
            "additionalProperties": False,
        }
        self._delegate_description = _delegate_description(self.registry)

    # ---- user chat ----------------------------------------------------------------

    def chat(self, message: str, trip: TripContext, history: list[dict[str, str]] | None = None,
             today: date | None = None) -> TurnResult:
        """One user turn. `history` is prior turns as [{"role": "user"|"assistant", "content": str}],
        append-only; the caller adds this turn's message and reply afterwards (see Session)."""
        today = today or date.today()
        delegations: list[Delegation] = []
        user_content = self._user_turn(message, trip, today)

        def delegate(agent: str, task: str) -> str:
            return json.dumps(self._delegate(agent, task, trip, today, delegations), ensure_ascii=False)

        delegate_tool = beta_tool(delegate, name="delegate", description=self._delegate_description,
                                  input_schema=self._delegate_schema)
        runner = llm.client().beta.messages.tool_runner(
            model=llm.MODEL,
            max_tokens=16000,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=[delegate_tool],
            messages=[*(history or []), {"role": "user", "content": user_content}],
            output_config={"effort": "low"},
            max_iterations=MAX_ITERATIONS,
            **llm.FALLBACK_KWARGS,
        )
        final = runner.until_done()
        if final.stop_reason == "refusal":
            reply = "Sorry, I can't help with that request."
        else:
            reply = "\n\n".join(b.text for b in final.content if b.type == "text").strip()
        result = self._turn_result(reply, delegations)
        result.user_content = user_content
        return result

    # ---- app events -----------------------------------------------------------------

    def handle_event(self, event: dict[str, Any], trip: TripContext, today: date | None = None) -> TurnResult:
        """Route an app event to its owning agent, then follow its handoffs one level deep."""
        today = today or date.today()
        name = EVENT_ROUTES.get(event["type"])
        if name is None or name not in self.registry:
            raise ValueError(f"No agent handles event type {event['type']!r}")
        delegations: list[Delegation] = []
        first = Delegation(agent=name, task=f"event {event['type']}", status="ok")
        first.result = self.registry[name].handle_event(event, trip, today)  # type: ignore[attr-defined]
        delegations.append(first)
        for handoff in first.result.handoffs:
            self._delegate(handoff.to_agent, handoff.task, trip, today, delegations)
        return self._turn_result(first.result.reply, delegations)

    # ---- internals --------------------------------------------------------------------

    def _delegate(self, agent: str, task: str, trip: TripContext, today: date,
                  delegations: list[Delegation]) -> dict[str, Any]:
        if len(delegations) >= MAX_DELEGATIONS_PER_TURN:
            delegations.append(Delegation(agent, task, "limit"))
            return {"status": "limit", "message": "Delegation limit reached for this turn; answer with what you have."}
        if agent not in self.registry:
            delegations.append(Delegation(agent, task, "unavailable"))
            return {"status": "unavailable", "message": f"The {agent} agent is not built yet."}
        try:
            result = self.registry[agent].run(task, trip, today)  # type: ignore[call-arg]
        except Exception as exc:  # a failing specialist shouldn't kill the whole turn
            delegations.append(Delegation(agent, task, "error", error=str(exc)))
            return {"status": "error", "message": f"The {agent} agent failed: {exc}"}
        delegations.append(Delegation(agent, task, "ok", result=result))
        return {
            "status": "ok",
            "reply": result.reply,
            "pending_actions": [{"kind": a.kind, "summary": a.summary} for a in result.pending_actions],
            "handoffs": [{"to_agent": h.to_agent, "task": h.task} for h in result.handoffs],
        }

    def _turn_result(self, reply: str, delegations: list[Delegation]) -> TurnResult:
        pending: list[dict[str, Any]] = []
        followed = {(d.agent, d.task) for d in delegations if d.status == "ok"}
        called_agents = {d.agent for d in delegations if d.status == "ok"}
        open_handoffs: list[Handoff] = []
        for d in delegations:
            if d.status == "unavailable":
                open_handoffs.append(Handoff(d.agent, d.task))
            if d.result is None:
                continue
            for a in d.result.pending_actions:
                pending.append(_action_card(f"pa{len(pending) + 1}", d.agent, a))
            for h in d.result.handoffs:
                if (h.to_agent, h.task) not in followed and h.to_agent not in called_agents:
                    open_handoffs.append(h)
        return TurnResult(reply=reply, delegations=delegations, pending_actions=pending,
                          open_handoffs=_dedupe(open_handoffs))

    @staticmethod
    def _user_turn(message: str, trip: TripContext, today: date) -> str:
        travelers = ", ".join(f"{t.name} ({t.id})" for t in trip.travelers)
        stops = ", ".join(f"{d.city} {d.arrive}..{d.depart}" for d in trip.destinations)
        return (
            f"<context>Today: {today.isoformat()}. Trip: {trip.name} [{trip.status}]. "
            f"Travelers: {travelers}. Stops: {stops}.</context>\n\n{message}"
        )


def _action_card(id: str, agent: str, action: PendingAction) -> dict[str, Any]:
    return {"id": id, "agent": agent, "kind": action.kind, "summary": action.summary, "payload": action.payload}


def _dedupe(handoffs: list[Handoff]) -> list[Handoff]:
    seen, out = set(), []
    for h in handoffs:
        if (h.to_agent, h.task) not in seen:
            seen.add((h.to_agent, h.task))
            out.append(h)
    return out


class Session:
    """A conversation about one trip. Keeps text-only history (append-only, cache-friendly)."""

    def __init__(self, trip: TripContext, orchestrator: Orchestrator | None = None) -> None:
        self.trip = trip
        self.orchestrator = orchestrator or Orchestrator()
        self.history: list[dict[str, str]] = []

    def send(self, message: str, today: date | None = None) -> TurnResult:
        result = self.orchestrator.chat(message, self.trip, self.history, today)
        self.history += [{"role": "user", "content": result.user_content},
                         {"role": "assistant", "content": result.reply or "(no reply)"}]
        return result

    def event(self, event: dict[str, Any], today: date | None = None) -> TurnResult:
        return self.orchestrator.handle_event(event, self.trip, today)
