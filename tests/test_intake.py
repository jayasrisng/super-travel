"""Intake -> trip -> five agent runs, plus the Essentials/Recovery API agents."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from super_travel.control.app import create_app

NOW = datetime(2026, 10, 11, 18, tzinfo=UTC)
ALICE, BOB = uuid4(), uuid4()

SARAH = {
    "client_name": "Sarah Mitchell",
    "purpose": "Family vacation",
    "destination": "Barcelona, Spain",
    "start_date": "2026-10-19",
    "end_date": "2026-10-25",
    "traveler_configuration": {"adult_count": 1, "child_count": 1},
    "child_ages": [6],
    "accommodation_area": "Near the Gothic Quarter",
    "interests": ["Aquarium", "parks", "beaches", "local food"],
    "needs": ["Kid-friendly meals", "easy walks", "pharmacy access", "downtime"],
    "advisor_name": "Dana Ortiz",
}

DELAY = {
    "kind": "delay",
    "passengers": 2,
    "arrival_delay_minutes": 220,
    "reference": "QX7K2M",
    "flight": {"carrier_code": "VY", "number": "VY7821", "from_iata": "LHR", "to_iata": "BCN",
               "scheduled_date": "2026-10-19"},
}


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr("super_travel.agents.essentials.proposal.fetch_rate", lambda f, t: (1.12, "2026-10-09"))
    app = create_app(path=str(tmp_path / "t.sqlite3"), tokens={"alice": ALICE, "bob": BOB},
                     worker=False, now=lambda: NOW)
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer alice"
        yield client, app


def post(client, route, body, key=None):
    return client.post(route, json=body, headers={"Idempotency-Key": str(key or uuid4())})


def drain(app):
    while app.state.service.work_once():
        pass


def test_intake_creates_trip_and_runs_all_five_agents(api):
    client, app = api
    created = post(client, "/v1/intakes", SARAH)
    assert created.status_code == 201
    intake = created.json()["data"]
    assert [r["agent"] for r in intake["runs"]] == [
        "plan_book", "pack_shop", "travel_essentials", "manage_recover", "explore_magic"]
    assert all(r["run_id"] for r in intake["runs"])

    trip = client.get(f"/v1/trips/{intake['trip_id']}").json()["data"]
    assert trip["timezone"] == "Europe/Madrid" and trip["traveler_configuration"]["child_count"] == 1
    assert trip["title"] == "Sarah's Barcelona trip"

    drain(app)
    runs = client.get(f"/v1/agent-runs?trip_id={intake['trip_id']}&limit=100").json()["data"]
    by_agent = {r["agent"]: r for r in runs}
    assert set(by_agent) == {"plan_book", "pack_shop", "travel_essentials", "manage_recover", "explore_magic"}
    assert all(r["status"] == "succeeded" for r in runs)

    essentials = by_agent["travel_essentials"]["proposal"]
    assert essentials["exchange_rate"]["rate"] == 1.12
    assert {c["phone"] for c in essentials["emergency_contacts"]} >= {"112"}
    assert any(i["item_id"] == "health-kids" for s in essentials["sections"] for i in s["items"])
    assert by_agent["manage_recover"]["proposal"]["actions"] == []
    assert by_agent["explore_magic"]["proposal"]["recommendations"]

    assert client.get("/v1/intakes").json()["data"][0]["id"] == intake["id"]
    assert client.get(f"/v1/intakes/{intake['id']}").json()["data"]["client_name"] == "Sarah Mitchell"


def test_intake_is_idempotent_and_actor_scoped(api):
    client, _ = api
    key = uuid4()
    first = post(client, "/v1/intakes", SARAH, key).json()
    assert post(client, "/v1/intakes", SARAH, key).json() == first
    assert post(client, "/v1/intakes", {**SARAH, "client_name": "Someone else"}, key).status_code == 409
    other = {"Authorization": "Bearer bob"}
    assert client.get(f"/v1/intakes/{first['data']['id']}", headers=other).status_code == 404
    assert client.get("/v1/intakes", headers=other).json()["data"] == []
    assert client.get(f"/v1/agent-runs?trip_id={first['data']['trip_id']}", headers=other).json()["data"] == []


def test_intake_validation(api):
    client, _ = api
    assert post(client, "/v1/intakes", {**SARAH, "end_date": "2026-10-01"}).status_code == 422
    assert post(client, "/v1/intakes", {**SARAH, "child_ages": [21]}).status_code == 422
    assert post(client, "/v1/intakes", {**SARAH, "ssn": "x"}).status_code == 422


def test_magic_skipped_outside_barcelona(api):
    client, app = api
    intake = post(client, "/v1/intakes", {**SARAH, "destination": "Lisbon"}).json()["data"]
    magic = next(r for r in intake["runs"] if r["agent"] == "explore_magic")
    assert magic["run_id"] is None and "Barcelona" in magic["skipped_reason"]
    drain(app)
    runs = client.get(f"/v1/agent-runs?trip_id={intake['trip_id']}").json()["data"]
    assert len(runs) == 4 and all(r["status"] == "succeeded" for r in runs)


def test_reported_delay_computes_eu261_claim(api):
    client, app = api
    intake = post(client, "/v1/intakes", SARAH).json()["data"]
    run = post(client, "/v1/agent-runs", {"agent": "manage_recover", "trip_id": intake["trip_id"],
                                          "input": {"disruption": DELAY}}).json()["data"]
    drain(app)
    proposal = client.get(f"/v1/agent-runs/{run['id']}").json()["data"]["proposal"]
    eu = proposal["rights"][0]
    assert eu["regulation"] == "EU261" and eu["total"] == {"amount_minor": 50000, "currency": "EUR"}
    claim = proposal["actions"][0]
    assert claim["kind"] == "send_claim" and claim["high_stakes"] and claim["amount"]["amount_minor"] == 50000
    assert "QX7K2M" in claim["draft"]


def test_disruption_without_trip_and_baggage(api):
    client, app = api
    run = post(client, "/v1/agent-runs", {"agent": "manage_recover",
                                          "input": {"disruption": {"kind": "baggage_delayed", "reference": "BCN1"}}}).json()["data"]
    drain(app)
    proposal = client.get(f"/v1/agent-runs/{run['id']}").json()["data"]["proposal"]
    assert proposal["baggage"]["kind"] == "delayed" and proposal["actions"][0]["kind"] == "send_claim"
    bad = {"agent": "manage_recover", "input": {"disruption": {"kind": "delay"}}}
    assert post(client, "/v1/agent-runs", bad).status_code == 422


def test_unknown_airport_fails_safely(api):
    client, app = api
    flight = {**DELAY["flight"], "from_iata": "ZZZ"}
    run = post(client, "/v1/agent-runs", {"agent": "manage_recover",
                                          "input": {"disruption": {**DELAY, "flight": flight}}}).json()["data"]
    drain(app)
    body = client.get(f"/v1/agent-runs/{run['id']}").json()["data"]
    assert body["status"] == "failed" and body["error"]["code"] == "invalid_constraints"


def test_agents_endpoint_lists_five_specialists_and_voice(api):
    client, _ = api
    agents = [a["agent"] for a in client.get("/v1/agents").json()["data"]]
    assert agents == ["plan_book", "pack_shop", "explore_magic", "travel_essentials", "manage_recover",
                      "voice_quotes"]
