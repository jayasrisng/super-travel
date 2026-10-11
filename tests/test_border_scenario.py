"""Sarah at the border: message -> triage -> voice agent quotes -> advisor approval -> policy to Sarah."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from super_travel.control.app import create_app
from tests.test_intake import SARAH

NOW = datetime(2026, 10, 19, 9, 30, tzinfo=UTC)
ALICE, BOB = uuid4(), uuid4()
AT_BORDER = "I'm at border control in Barcelona and the officer is asking for proof of travel insurance. I don't have any!"


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr("super_travel.agents.essentials.proposal.fetch_rate", lambda f, t: (1.12, "2026-10-09"))
    app = create_app(path=str(tmp_path / "t.sqlite3"), tokens={"alice": ALICE, "bob": BOB},
                     worker=False, now=lambda: NOW)
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer alice"
        yield client, app


def post(client, route, body):
    return client.post(route, json=body, headers={"Idempotency-Key": str(uuid4())})


def drain(app):
    while app.state.service.work_once():
        pass


@pytest.fixture
def trip(api):
    client, app = api
    intake = post(client, "/v1/intakes", SARAH).json()["data"]
    drain(app)
    return intake["trip_id"]


def test_traveler_message_is_triaged_urgent(api, trip):
    client, _ = api
    msg = post(client, f"/v1/trips/{trip}/messages", {"sender": "traveler", "text": AT_BORDER}).json()["data"]
    assert msg["triage"] == {"topic": "insurance_proof", "urgency": "urgent", "suggested_action": "voice_quotes",
                             "reason": "Traveler needs proof of travel insurance at the border"}
    reply = post(client, f"/v1/trips/{trip}/messages", {"sender": "advisor", "text": "On it, Sarah."}).json()["data"]
    assert reply["triage"] is None
    thread = client.get(f"/v1/trips/{trip}/messages").json()["data"]
    assert [m["sender"] for m in thread] == ["traveler", "advisor"]  # oldest first
    other = {"Authorization": "Bearer bob"}
    assert client.get(f"/v1/trips/{trip}/messages", headers=other).status_code == 404


def test_full_border_flow(api, trip):
    client, app = api
    msg = post(client, f"/v1/trips/{trip}/messages", {"sender": "traveler", "text": AT_BORDER}).json()["data"]
    run = post(client, "/v1/agent-runs", {"agent": "voice_quotes", "trip_id": trip,
                                          "input": {"child_ages": [6], "message_id": msg["id"]}}).json()["data"]
    drain(app)
    proposal = client.get(f"/v1/agent-runs/{run['id']}").json()["data"]["proposal"]
    outcomes = {c["insurer"]: c["outcome"] for c in proposal["calls"]}
    assert list(outcomes.values()).count("quoted") == 3 and "declined" in outcomes.values()
    quotes = {c["quote"]["quote_id"]: c["quote"] for c in proposal["calls"] if c["quote"]}
    cheapest_overall = min(quotes.values(), key=lambda q: q["premium"]["amount_minor"])
    assert not cheapest_overall["meets_requirements"]  # too little medical cover
    best = quotes[proposal["recommended_quote_id"]]
    assert best["meets_requirements"] and best["insurer"] == "Sol & Sea Assurance"
    assert best["premium"] == {"amount_minor": 7 * (320 + 160), "currency": "EUR"}  # 7 days, 1 adult + 1 child

    rejected = post(client, f"/v1/trips/{trip}/insurance-policies",
                    {"run_id": run["id"], "quote_id": cheapest_overall["quote_id"]})
    assert rejected.status_code == 422

    policy = post(client, f"/v1/trips/{trip}/insurance-policies",
                  {"run_id": run["id"], "quote_id": best["quote_id"]}).json()["data"]
    assert policy["status"] == "simulated" and policy["policy_number"].startswith("SIM-")
    assert policy["insured"] == ["Sarah Mitchell", "Child, age 6"]
    assert policy["coverage_start"] == "2026-10-19" and policy["coverage_end"] == "2026-10-25"

    sent = post(client, f"/v1/trips/{trip}/messages", {
        "sender": "advisor", "text": "Here's your insurance certificate.",
        "attachment": {"type": "insurance_policy", "policy_id": policy["id"]}}).json()["data"]
    assert sent["attachment"]["policy_id"] == policy["id"]
    fetched = client.get(f"/v1/trips/{trip}/insurance-policies/{policy['id']}").json()["data"]
    assert fetched["policy_number"] == policy["policy_number"]


def test_policy_requires_this_trips_finished_voice_run(api, trip):
    client, app = api
    plan_run = client.get(f"/v1/agent-runs?trip_id={trip}").json()["data"][0]
    assert post(client, f"/v1/trips/{trip}/insurance-policies",
                {"run_id": plan_run["id"], "quote_id": "solsea-7d"}).status_code == 409
    other_trip = post(client, "/v1/intakes", SARAH).json()["data"]["trip_id"]
    run = post(client, "/v1/agent-runs", {"agent": "voice_quotes", "trip_id": other_trip, "input": {}}).json()["data"]
    drain(app)
    assert post(client, f"/v1/trips/{trip}/insurance-policies",
                {"run_id": run["id"], "quote_id": "solsea-7d"}).status_code == 409


def test_attachment_must_belong_to_trip(api, trip):
    client, app = api
    other_trip = post(client, "/v1/intakes", SARAH).json()["data"]["trip_id"]
    run = post(client, "/v1/agent-runs", {"agent": "voice_quotes", "trip_id": other_trip, "input": {}}).json()["data"]
    drain(app)
    best = client.get(f"/v1/agent-runs/{run['id']}").json()["data"]["proposal"]["recommended_quote_id"]
    policy = post(client, f"/v1/trips/{other_trip}/insurance-policies", {"run_id": run["id"], "quote_id": best}).json()["data"]
    bad = post(client, f"/v1/trips/{trip}/messages", {"sender": "advisor", "text": "x",
                                                     "attachment": {"type": "insurance_policy", "policy_id": policy["id"]}})
    assert bad.status_code == 422
    assert client.get(f"/v1/trips/{trip}/insurance-policies/{policy['id']}").status_code == 404


@pytest.mark.parametrize("text,topic", [
    ("Our flight is delayed 4 hours", "disruption"),
    ("Do I need insurance for the trip?", "insurance_proof"),
    ("What time is check-in?", "general"),
])
def test_triage_topics(api, trip, text, topic):
    client, _ = api
    msg = post(client, f"/v1/trips/{trip}/messages", {"sender": "traveler", "text": text}).json()["data"]
    assert msg["triage"]["topic"] == topic
