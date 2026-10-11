import json
from datetime import date
from decimal import Decimal

import pytest

from super_travel.agents import REGISTRY
from super_travel.agents.recovery.agent import RecoveryAgent
from super_travel.agents.recovery.rules.compensation import assess_eu261, assess_us_dot, baggage_rights
from super_travel.agents.recovery.tools import RecoveryTools
from super_travel.core import expenses
from super_travel.core.trip_context import load_trip
from tests.fake_api import fake_messages_api, text, tool_use

FIXED_FX = lambda amount, frm, to: amount * (1.10 if frm == "EUR" and to == "USD" else 1.0)  # noqa: E731


# ---- EU261 / DOT rules --------------------------------------------------------

def eu(**kw):
    base = dict(from_iata="LIS", to_iata="BCN", carrier_code="VY", event="delay", passengers=2)
    return assess_eu261(**(base | kw))


def test_eu261_demo_delay_250_each():
    a = eu(arrival_delay_minutes=250)
    assert a.applies and a.eligible_for_compensation
    assert (a.amount_per_passenger, a.total, a.currency) == (250, 500, "EUR")
    assert a.right_to_care and not a.right_to_refund


@pytest.mark.parametrize("minutes,eligible", [(179, False), (180, True)])
def test_eu261_three_hour_threshold(minutes, eligible):
    assert eu(arrival_delay_minutes=minutes).eligible_for_compensation is eligible


def test_eu261_extraordinary_circumstances_no_compensation_but_care():
    a = eu(arrival_delay_minutes=300, extraordinary_circumstances=True)
    assert not a.eligible_for_compensation and a.right_to_care and a.right_to_refund


def test_eu261_long_haul_bands():
    assert eu(from_iata="BCN", to_iata="SFO", carrier_code="IB", arrival_delay_minutes=250).amount_per_passenger == 600
    assert eu(from_iata="BCN", to_iata="SFO", carrier_code="IB", arrival_delay_minutes=200).amount_per_passenger == 300


def test_eu261_inbound_depends_on_carrier():
    assert eu(from_iata="SFO", to_iata="LIS", carrier_code="TP", arrival_delay_minutes=250).applies
    assert not eu(from_iata="SFO", to_iata="LIS", carrier_code="UA", arrival_delay_minutes=250).applies


def test_eu261_cancellation_notice_rules():
    assert not eu(event="cancellation", notice_days=15).eligible_for_compensation
    assert not eu(event="cancellation", notice_days=3, reroute_arrival_delay_minutes=90).eligible_for_compensation
    assert eu(event="cancellation", notice_days=3, reroute_arrival_delay_minutes=200).amount_per_passenger == 250
    assert eu(event="cancellation", notice_days=3).right_to_refund


def test_us_dot_refund_rule():
    intl = dict(from_iata="BCN", to_iata="SFO", passengers=2)
    assert assess_us_dot(**intl, event="cancellation").right_to_refund
    assert not assess_us_dot(**intl, event="delay", change_minutes=300).right_to_refund
    assert assess_us_dot(**intl, event="delay", change_minutes=360).right_to_refund
    assert not assess_us_dot(from_iata="LIS", to_iata="BCN", passengers=1, event="cancellation").applies


def test_baggage_rights_windows():
    assert "21 days" in baggage_rights("delayed")["claim_window"]
    assert "7 days" in baggage_rights("damaged")["claim_window"]


# ---- split math -----------------------------------------------------------------

def test_equal_split_cents_add_up():
    s = expenses.shares_for({"amount": 100, "currency": "USD", "payer": "a", "split": ["a", "b", "c"]})
    assert sum(s.values()) == Decimal("100.00") and sorted(s.values()) == [Decimal("33.33")] * 2 + [Decimal("33.34")]


def test_refund_reverses_split_exactly():
    exps = [
        {"amount": 100, "currency": "USD", "payer": "a", "split": ["a", "b", "c"]},
        {"amount": -10, "currency": "USD", "payer": "a", "split": ["a", "b", "c"]},
    ]
    net = expenses.balances(exps, "USD", lambda x, f, t: x)
    assert net == {"a": Decimal("60.00"), "b": Decimal("-30.00"), "c": Decimal("-30.00")}


def test_shares_and_amounts_rules():
    s = expenses.shares_for({"amount": 90, "currency": "USD", "payer": "a",
                             "split_rule": {"type": "shares", "shares": {"a": 2, "b": 1}}})
    assert s == {"a": Decimal("60.00"), "b": Decimal("30.00")}
    with pytest.raises(ValueError):
        expenses.shares_for({"amount": 90, "currency": "USD", "payer": "a",
                             "split_rule": {"type": "amounts", "amounts": {"a": 50, "b": 30}}})


def test_settle_up_balances_to_zero():
    net = {"a": Decimal("50"), "b": Decimal("-20"), "c": Decimal("-30")}
    transfers = expenses.settle_up(net)
    assert sum(t["amount"] for t in transfers) == 50
    assert {t["from"] for t in transfers} == {"b", "c"} and {t["to"] for t in transfers} == {"a"}


# ---- tools ---------------------------------------------------------------------

def test_tools_against_demo_trip():
    trip = load_trip()
    t = RecoveryTools(trip, convert_fn=FIXED_FX)
    comp = json.loads(t.check_compensation("s2", "delay", arrival_delay_minutes=250))
    assert comp["assessments"][0]["total"] == 500
    alts = json.loads(t.search_alternative_flights("LIS", "BCN", "2026-11-17"))["flights"]
    assert {f["number"] for f in alts} >= {"TP1032", "VY8465", "IB3107"}
    rec = json.loads(t.reconcile_expenses())
    assert rec["currency"] == "USD" and sum(rec["balances"].values()) == pytest.approx(0, abs=0.01)
    assert len(rec["transfers"]) == 1


def test_write_tools_only_touch_internal_state():
    trip = load_trip()
    t = RecoveryTools(trip, convert_fn=FIXED_FX)
    inc = json.loads(t.open_incident("baggage_delayed", "Arjun's bag missing at BCN", "s2", ["t_arjun"], "BCNVY10293"))
    exp = json.loads(t.record_expense("Toiletries", 38.4, "eur", "t_arjun", "2026-11-17", "delayed_baggage",
                                      incident_id=inc["id"], claimable=True))
    assert trip.incidents[-1]["id"] == inc["id"] and trip.expenses[-1]["id"] == exp["id"]
    assert exp["currency"] == "EUR" and exp["split"] == ["t_arjun"]
    with pytest.raises(ValueError):
        t.record_expense("x", 1, "EUR", "nobody", "2026-11-17", "food")


def test_registered():
    assert isinstance(REGISTRY["recovery"], RecoveryAgent)


# ---- full agent loop against a fake API ---------------------------------------

RESULT = {
    "reply": "Your flight is 4h late. You're each owed EUR 250 under EU261.",
    "pending_actions": [{"kind": "send_claim", "summary": "EU261 claim to Vueling, 2 passengers", "recipient": "Vueling",
                         "incident_id": "i1", "draft": "Dear Vueling...", "amount": 500, "currency": "EUR"}],
    "checklist_items": [{"title": "Follow up on Vueling EU261 claim", "due": "2026-12-15", "traveler_id": "", "priority": "should"}],
    "handoffs": [{"to_agent": "explore", "task": "Check the 20:30 dinner still works with a 17:05 arrival"}],
}


def test_handle_event_end_to_end(monkeypatch):
    trip = load_trip()
    event = json.load(open("fixtures/demo_events.json"))["events"][0]
    script = [
        tool_use("get_flight_status", {"segment_id": "s2"}, "t1"),
        tool_use("open_incident", {"kind": "flight_delay", "summary": "VY8461 delayed 250 min", "segment_id": "s2"}, "t2"),
        tool_use("submit_recovery", {k: v for k, v in RESULT.items() if k != "reply"}, "t3"),  # invalid: no reply
        tool_use("submit_recovery", RESULT, "t4"),
        text("Done."),
    ]
    with fake_messages_api(script, monkeypatch) as seen:
        result = RecoveryAgent().handle_event(event, trip, today=date(2026, 11, 17))

    body = seen[0]["body"]
    assert body["model"] == "claude-opus-5-5" and body["fallbacks"] == "default"
    assert body["output_config"] == {"effort": "high"} and seen[0]["beta"] == "server-side-fallback-2026-07-01"
    assert body["messages"][0]["content"].count("EVENT:") == 1 and "expected" not in body["messages"][0]["content"]
    assert "250" in json.loads(seen[1]["body"]["messages"][-1]["content"][0]["content"])["live_status"]["arrival_delay_minutes"].__str__()
    retry = seen[3]["body"]["messages"][-1]["content"][0]
    assert retry["is_error"] is True

    assert trip.segments[1]["live_status"]["status"] == "delayed"
    assert trip.incidents[0]["kind"] == "flight_delay"
    assert result.pending_actions[0].kind == "send_claim" and result.pending_actions[0].payload["amount"] == 500
    assert result.handoffs[0].to_agent == "explore"
    assert [t["title"] for t in result.data["checklist_added"]] == ["Follow up on Vueling EU261 claim"]


def test_agent_without_submit_raises(monkeypatch):
    from super_travel.core.specialist import SpecialistError
    with fake_messages_api([text("I'm not sure.")], monkeypatch):
        with pytest.raises(SpecialistError):
            RecoveryAgent().run("help", load_trip(), today=date(2026, 11, 17))
