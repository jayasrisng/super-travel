"""Consumer app (traveler) <-> advisor dashboard (agency) through a client code."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from super_travel.control.app import create_app
from tests.test_border_scenario import AT_BORDER
from tests.test_intake import SARAH

NOW = datetime(2026, 10, 19, 9, 30, tzinfo=UTC)
AGENCY, TRAVELER, STRANGER = uuid4(), uuid4(), uuid4()


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr("super_travel.agents.essentials.proposal.fetch_rate", lambda f, t: (1.12, "2026-10-09"))
    monkeypatch.setenv("DIAL_ENABLED", "false")
    app = create_app(path=str(tmp_path / "t.sqlite3"),
                     tokens={"agency": AGENCY, "traveler": TRAVELER, "stranger": STRANGER},
                     worker=False, now=lambda: NOW)
    with TestClient(app) as client:
        yield client, app


def as_(who):
    return {"Authorization": f"Bearer {who}"}


def post(client, route, body, who):
    return client.post(route, json=body, headers={**as_(who), "Idempotency-Key": str(uuid4())})


def drain(app):
    while app.state.service.work_once():
        pass


def test_traveler_links_messages_and_receives_policy(api):
    client, app = api
    intake = post(client, "/v1/intakes", SARAH, "agency").json()["data"]
    code = intake["client_code"]
    assert len(code) == 6 and code.isalnum()
    drain(app)

    assert client.get("/v1/consumer/advisor", headers=as_("traveler")).status_code == 404
    assert post(client, "/v1/consumer/advisor-link", {"client_code": "ZZZZZZ"}, "traveler").status_code == 404
    link = post(client, "/v1/consumer/advisor-link", {"client_code": code.lower()}, "traveler").json()["data"]
    assert link["trip_id"] == intake["trip_id"] and link["client_name"] == "Sarah Mitchell"
    assert "agency_actor" not in link

    sent = post(client, "/v1/consumer/advisor/messages", {"text": AT_BORDER}, "traveler").json()["data"]
    assert sent["sender"] == "traveler" and sent["triage"]["urgency"] == "urgent"
    assert post(client, "/v1/consumer/advisor/messages", {"text": "x", "sender": "advisor"}, "traveler").status_code == 422

    # The advisor sees it on the agency trip, deploys the voice agent and sends a policy.
    thread = client.get(f"/v1/trips/{intake['trip_id']}/messages", headers=as_("agency")).json()["data"]
    assert thread[-1]["id"] == sent["id"]
    run = post(client, "/v1/agent-runs", {"agent": "voice_quotes", "trip_id": intake["trip_id"], "input": {}},
               "agency").json()["data"]
    drain(app)
    best = client.get(f"/v1/agent-runs/{run['id']}", headers=as_("agency")).json()["data"]["proposal"]["recommended_quote_id"]
    policy = post(client, f"/v1/trips/{intake['trip_id']}/insurance-policies",
                  {"run_id": run["id"], "quote_id": best}, "agency").json()["data"]
    post(client, f"/v1/trips/{intake['trip_id']}/messages",
         {"sender": "advisor", "text": "You're covered.", "attachment": {"type": "insurance_policy", "policy_id": policy["id"]}},
         "agency")

    feed = client.get("/v1/consumer/advisor/messages", headers=as_("traveler")).json()["data"]
    assert [m["sender"] for m in feed] == ["traveler", "advisor"]
    attached = feed[-1]["attachment"]["policy_id"]
    got = client.get(f"/v1/consumer/advisor/policies/{attached}", headers=as_("traveler")).json()["data"]
    assert got["policy_number"] == policy["policy_number"] and got["insured"][0] == "Sarah Mitchell"


def test_unlinked_users_see_nothing(api):
    client, _ = api
    intake = post(client, "/v1/intakes", SARAH, "agency").json()["data"]
    assert client.get("/v1/consumer/advisor/messages", headers=as_("stranger")).status_code == 404
    assert post(client, "/v1/consumer/advisor/messages", {"text": "hi"}, "stranger").status_code == 404
    assert client.get(f"/v1/trips/{intake['trip_id']}/messages", headers=as_("stranger")).status_code == 404


def test_policy_from_another_trip_is_hidden(api):
    client, app = api
    mine = post(client, "/v1/intakes", SARAH, "agency").json()["data"]
    other = post(client, "/v1/intakes", SARAH, "agency").json()["data"]
    drain(app)
    run = post(client, "/v1/agent-runs", {"agent": "voice_quotes", "trip_id": other["trip_id"], "input": {}},
               "agency").json()["data"]
    drain(app)
    best = client.get(f"/v1/agent-runs/{run['id']}", headers=as_("agency")).json()["data"]["proposal"]["recommended_quote_id"]
    policy = post(client, f"/v1/trips/{other['trip_id']}/insurance-policies", {"run_id": run["id"], "quote_id": best},
                  "agency").json()["data"]
    post(client, "/v1/consumer/advisor-link", {"client_code": mine["client_code"]}, "traveler")
    assert client.get(f"/v1/consumer/advisor/policies/{policy['id']}", headers=as_("traveler")).status_code == 404


def test_demo_cookie_session_can_link(tmp_path, monkeypatch):
    """The consumer web app authenticates with the localhost demo cookie, not a token."""
    monkeypatch.setattr("super_travel.agents.essentials.proposal.fetch_rate", lambda f, t: (1.12, "2026-10-09"))
    app = create_app(path=str(tmp_path / "t.sqlite3"), tokens={"agency-token-" + "x" * 32: AGENCY},
                     worker=False, now=lambda: NOW, demo_auth=True)
    with TestClient(app) as client:
        agency = {"Authorization": "Bearer agency-token-" + "x" * 32}
        intake = client.post("/v1/intakes", json=SARAH, headers={**agency, "Idempotency-Key": str(uuid4())}).json()["data"]
        assert client.post("/v1/demo/session", json={}).status_code == 200
        link = client.post("/v1/consumer/advisor-link", json={"client_code": intake["client_code"]},
                           headers={"Idempotency-Key": str(uuid4())})
        assert link.status_code == 201
        sent = client.post("/v1/consumer/advisor/messages", json={"text": "Hello from the app"},
                           headers={"Idempotency-Key": str(uuid4())}).json()["data"]
        thread = client.get(f"/v1/trips/{intake['trip_id']}/messages", headers=agency).json()["data"]
        assert thread[0]["id"] == sent["id"]
