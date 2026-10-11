import json
from datetime import date

import pytest

from super_travel.core.agent import AgentResult, Handoff, PendingAction
from super_travel.core.trip_context import load_trip
from super_travel.orchestrator import Orchestrator, Session
from super_travel.orchestrator import orchestrator as orch_module
from tests.fake_api import fake_messages_api, text, tool_use

TODAY = date(2026, 11, 17)


class StubAgent:
    def __init__(self, name, reply="ok", handoffs=(), actions=(), fail=False):
        self.name, self.description = name, f"{name} stub"
        self._reply, self._handoffs, self._actions, self._fail = reply, list(handoffs), list(actions), fail
        self.calls = []

    def run(self, task, trip, today=None):
        self.calls.append(task)
        if self._fail:
            raise RuntimeError("boom")
        return AgentResult(reply=self._reply, handoffs=self._handoffs, pending_actions=self._actions,
                           data={"agent": self.name})

    def handle_event(self, event, trip, today=None):
        return self.run(f"EVENT {event['type']}", trip, today)


def delegate(agent, task, id):
    return tool_use("delegate", {"agent": agent, "task": task}, id)


def test_chat_delegates_and_merges(monkeypatch):
    claim = PendingAction("send_claim", "EU261 claim to Vueling", {"amount": 500})
    recovery = StubAgent("recovery", reply="You're owed EUR 250 each.", actions=[claim])
    essentials = StubAgent("essentials", reply="Use your eSIM.")
    o = Orchestrator({"recovery": recovery, "essentials": essentials})
    script = [
        {"content": [delegate("recovery", "Delay claim for VY8461", "t1")["content"][0],
                     delegate("essentials", "Does the eSIM cover an extra day?", "t2")["content"][0]],
         "stop_reason": "tool_use"},
        text("You're owed EUR 250 each. Ready to send: EU261 claim to Vueling."),
    ]
    with fake_messages_api(script, monkeypatch) as seen:
        result = o.chat("Flight delayed 4h, what now?", load_trip(), today=TODAY)

    req = seen[0]["body"]
    assert req["output_config"] == {"effort": "low"}
    tool = req["tools"][0]
    assert tool["name"] == "delegate"
    assert tool["input_schema"]["properties"]["agent"]["enum"] == ["essentials", "explore", "packing", "planning", "recovery"]
    assert "NOT YET AVAILABLE" in tool["description"]
    assert "Today: 2026-11-17" in req["messages"][-1]["content"]

    results = [json.loads(c["content"]) for c in seen[1]["body"]["messages"][-1]["content"]]
    assert [r["status"] for r in results] == ["ok", "ok"]
    assert recovery.calls == ["Delay claim for VY8461"] and essentials.calls
    assert result.reply.startswith("You're owed")
    assert result.pending_actions == [{"id": "pa1", "agent": "recovery", "kind": "send_claim",
                                       "summary": "EU261 claim to Vueling", "payload": {"amount": 500}}]
    assert set(result.cards) == {"recovery", "essentials"}


def test_unavailable_agent_and_failing_agent(monkeypatch):
    o = Orchestrator({"recovery": StubAgent("recovery", fail=True)})
    script = [delegate("planning", "Rebook BCN-SFO", "t1"), delegate("recovery", "x", "t2"), text("Partly done.")]
    with fake_messages_api(script, monkeypatch) as seen:
        result = o.chat("Rebook me", load_trip(), today=TODAY)
    assert json.loads(seen[1]["body"]["messages"][-1]["content"][0]["content"])["status"] == "unavailable"
    assert json.loads(seen[2]["body"]["messages"][-1]["content"][0]["content"])["status"] == "error"
    assert [d.status for d in result.delegations] == ["unavailable", "error"]
    assert result.open_handoffs == [Handoff("planning", "Rebook BCN-SFO")]


def test_delegation_limit(monkeypatch):
    monkeypatch.setattr(orch_module, "MAX_DELEGATIONS_PER_TURN", 2)
    o = Orchestrator({"recovery": StubAgent("recovery")})
    script = [delegate("recovery", f"t{i}", f"id{i}") for i in range(3)] + [text("done")]
    with fake_messages_api(script, monkeypatch) as seen:
        result = o.chat("go", load_trip(), today=TODAY)
    assert [d.status for d in result.delegations] == ["ok", "ok", "limit"]


def test_event_routes_to_recovery_and_follows_handoffs():
    recovery = StubAgent("recovery", reply="Bag delayed; claim filed draft ready.",
                         handoffs=[Handoff("essentials", "Check coverage"), Handoff("packing", "Buy toiletries")])
    essentials = StubAgent("essentials")
    o = Orchestrator({"recovery": recovery, "essentials": essentials})
    result = o.handle_event({"type": "baggage_delayed", "data": {}}, load_trip(), today=TODAY)
    assert recovery.calls == ["EVENT baggage_delayed"] and essentials.calls == ["Check coverage"]
    assert [d.status for d in result.delegations] == ["ok", "ok", "unavailable"]
    assert result.open_handoffs == [Handoff("packing", "Buy toiletries")]
    with pytest.raises(ValueError):
        o.handle_event({"type": "unknown"}, load_trip())


def test_session_history_is_append_only(monkeypatch):
    s = Session(load_trip(), Orchestrator({"recovery": StubAgent("recovery")}))
    with fake_messages_api([text("Hi! How can I help?"), text("Sure.")], monkeypatch) as seen:
        s.send("hello", today=TODAY)
        s.send("thanks", today=TODAY)
    first, second = seen[0]["body"]["messages"], seen[1]["body"]["messages"]
    assert second[0] == first[0] and second[0]["content"].endswith("hello")
    assert second[1] == {"role": "assistant", "content": "Hi! How can I help?"}
    assert len(s.history) == 4


def test_orchestrator_with_real_recovery_agent(monkeypatch):
    """Orchestrator -> RecoveryAgent -> rules, all through one scripted fake API."""
    from super_travel.agents.recovery.agent import RecoveryAgent

    recovery_result = {
        "reply": "EUR 250 each under EU261.", "checklist_items": [], "handoffs": [],
        "pending_actions": [{"kind": "send_claim", "summary": "EU261 claim, 2 pax", "recipient": "Vueling",
                             "incident_id": "", "draft": "Dear Vueling", "amount": 500, "currency": "EUR"}],
    }
    script = [
        delegate("recovery", "VY8461 arrived 250 min late; what are we owed?", "o1"),       # orchestrator
        tool_use("check_compensation", {"segment_id": "s2", "event": "delay", "arrival_delay_minutes": 250}, "r1"),
        tool_use("submit_recovery", recovery_result, "r2"),                                   # recovery
        text("Submitted."),                                                                   # recovery ends
        text("You're owed EUR 250 each. Ready to send: EU261 claim, 2 pax."),                 # orchestrator ends
    ]
    o = Orchestrator({"recovery": RecoveryAgent()})
    with fake_messages_api(script, monkeypatch) as seen:
        result = o.chat("Our flight was 4h late, what are we owed?", load_trip(), today=TODAY)
    rules_output = json.loads(seen[2]["body"]["messages"][-1]["content"][0]["content"])
    assert rules_output["assessments"][0]["total"] == 500
    assert [t["name"] for t in seen[0]["body"]["tools"]] == ["delegate"]
    assert {"check_compensation", "submit_recovery", "web_search"} <= {t["name"] for t in seen[1]["body"]["tools"]}
    assert result.pending_actions[0]["kind"] == "send_claim" and "EUR 250" in result.reply
