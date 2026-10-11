"""Offline boundary, persistence and race tests for dashboard integration."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from super_travel.agents.explore import Candidate, ExploreAgent
from super_travel.agents.proposals import PackingAgent, PlanningAgent
from super_travel.control.app import create_app
from super_travel.control.schemas import MagicInput, Money, PackInput, PlanInput, Source
from tests.fake_api import fake_messages_api, text, tool_use

NOW = datetime(2026, 10, 25, 0, 30, tzinfo=UTC)
ALICE, BOB = uuid4(), uuid4()


@pytest.fixture
def api(tmp_path):
    clock = [NOW]
    app = create_app(
        path=str(tmp_path / "test.sqlite3"),
        tokens={"alice": ALICE, "bob": BOB},
        worker=False,
        now=lambda: clock[0],
    )
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer alice"
        yield client, app, clock


def post(client, route, body, key=None, **headers):
    return client.post(
        route, json=body, headers={"Idempotency-Key": str(key or uuid4()), **headers}
    )


def plan():
    return {
        "agent": "plan_book",
        "input": {
            "destination": "Barcelona",
            "start_date": "2026-11-13",
            "end_date": "2026-11-15",
        },
    }


def magic():
    return {
        "location": {"latitude": 41.385, "longitude": 2.174},
        "available_minutes": 120,
    }


def test_auth_strict_input_money_and_body_limit(api):
    client, _, _ = api
    assert (
        client.get("/v1/agents", headers={"Authorization": "Bearer wrong"}).status_code
        == 401
    )
    assert (
        post(client, "/v1/agent-runs", {**plan(), "unexpected": "value"}).status_code
        == 422
    )
    invalid = plan()
    invalid["input"]["budget"] = {"amount_minor": 2.5, "currency": "EUR"}
    assert post(client, "/v1/agent-runs", invalid).status_code == 422
    assert client.post("/v1/agent-runs", json=plan()).status_code == 422
    result = client.post("/v1/agent-runs", content="x" * 32769)
    assert result.status_code == 413
    assert "error" in result.json()


def test_replay_conflict_actor_isolation_and_cancel_late_result(api):
    client, app, _ = api
    key = uuid4()
    created = post(client, "/v1/agent-runs", plan(), key)
    run = created.json()["data"]
    assert created.status_code == 202
    assert post(client, "/v1/agent-runs", plan(), key).json() == created.json()
    assert (
        post(
            client, "/v1/agent-runs", {"agent": "pack_shop", "input": {}}, key
        ).status_code
        == 409
    )
    claim = app.state.store.claim()
    running = client.get("/v1/agent-runs/" + run["id"])
    assert running.json()["data"]["status"] == "running"
    client.headers["Authorization"] = "Bearer bob"
    assert client.get("/v1/agent-runs/" + run["id"]).status_code == 404
    assert client.get("/v1/agent-runs").json()["data"] == []
    client.headers["Authorization"] = "Bearer alice"
    route = "/v1/agent-runs/" + run["id"] + "/cancel"
    assert post(client, route, {}).status_code == 428
    assert (
        post(client, route, {}, **{"If-Match": created.headers["etag"]}).status_code
        == 412
    )
    cancelled = post(client, route, {}, **{"If-Match": running.headers["etag"]})
    assert cancelled.json()["data"]["status"] == "cancelled"
    app.state.store.finish(
        run["id"],
        claim[2],
        proposal=PlanningAgent().propose(PlanInput(), NOW).model_dump(mode="json"),
    )
    assert (
        client.get("/v1/agent-runs/" + run["id"]).json()["data"]["status"]
        == "cancelled"
    )


@pytest.mark.parametrize("agent", ["plan_book", "pack_shop", "explore_magic"])
def test_all_three_agents_reach_typed_success(api, agent):
    client, app, _ = api
    body = {
        "agent": agent,
        "input": magic() if agent == "explore_magic" else plan()["input"],
    }
    created = post(client, "/v1/agent-runs", body).json()["data"]
    assert app.state.service.work_once()
    result = client.get("/v1/agent-runs/" + created["id"])
    assert result.status_code == 200
    assert result.json()["data"]["status"] == "succeeded"
    assert result.json()["data"]["proposal"]["data_mode"] == "fixture"


def test_trip_context_allowlist_and_isolation(api):
    client, app, _ = api
    trip_body = {
        "title": "Barcelona",
        "destination": "Barcelona",
        "start_date": "2026-11-13",
        "end_date": "2026-11-15",
    }
    trip = post(client, "/v1/trips", trip_body).json()["data"]
    run = post(
        client,
        "/v1/agent-runs",
        {"agent": "plan_book", "trip_id": trip["id"], "input": {}},
    ).json()["data"]
    assert run["context_version"] == 1
    app.state.service.work_once()
    result = client.get("/v1/agent-runs/" + run["id"]).json()["data"]
    assert result["proposal"]["itinerary_items"][0]["starts_at"].startswith(
        "2026-11-13"
    )
    assert client.get("/v1/trips/" + trip["id"]).json()["data"] == trip
    client.headers["Authorization"] = "Bearer bob"
    assert (
        post(
            client,
            "/v1/agent-runs",
            {"agent": "plan_book", "trip_id": trip["id"], "input": {}},
        ).status_code
        == 404
    )


def test_saved_expiry_deletion_and_run_redaction(api):
    client, app, clock = api
    run = post(client, "/v1/magic/runs", magic()).json()["data"]
    app.state.service.work_once()
    proposal = client.get("/v1/agent-runs/" + run["id"]).json()["data"]["proposal"]
    rec = proposal["recommendations"][0]
    body = {"run_id": run["id"], "recommendation_id": rec["id"]}
    saved = post(client, "/v1/me/saved-experiences", body)
    assert saved.status_code == 201
    identifier = saved.json()["data"]["id"]
    assert len(client.get("/v1/me/saved-experiences").json()["data"]) == 1
    assert client.delete("/v1/me/saved-experiences/" + identifier).status_code == 428
    assert (
        client.delete(
            "/v1/me/saved-experiences/" + identifier,
            headers={"If-Match": saved.headers["etag"]},
        ).status_code
        == 204
    )
    clock[0] += timedelta(minutes=16)
    assert post(client, "/v1/me/saved-experiences", body).status_code == 409
    clock[0] += timedelta(hours=24)
    expired = client.get("/v1/agent-runs/" + run["id"]).json()["data"]
    assert expired["status"] == "expired" and expired["proposal"] is None
    row = app.state.store.db.execute(
        "SELECT input FROM objects WHERE id=?", (run["id"],)
    ).fetchone()
    assert row["input"] is None


def test_queue_pagination_and_recovery_after_restart(tmp_path):
    clock = [NOW]
    path = str(tmp_path / "persist.sqlite3")
    settings = {
        "path": path,
        "tokens": {"alice": ALICE},
        "worker": False,
        "now": lambda: clock[0],
    }
    with TestClient(create_app(**settings)) as client:
        client.headers["Authorization"] = "Bearer alice"
        for _ in range(10):
            assert post(client, "/v1/agent-runs", plan()).status_code == 202
        assert post(client, "/v1/agent-runs", plan()).status_code == 429
        page = client.get("/v1/agent-runs?limit=3").json()
        second = client.get(
            "/v1/agent-runs", params={"cursor": page["meta"]["next_cursor"], "limit": 3}
        ).json()
        assert not ({x["id"] for x in page["data"]} & {x["id"] for x in second["data"]})
        claimed = client.app.state.store.claim()
    clock[0] += timedelta(seconds=121)
    with TestClient(create_app(**settings)) as client:
        client.headers["Authorization"] = "Bearer alice"
        assert client.app.state.service.work_once()
        assert (
            client.get("/v1/agent-runs/" + claimed[0]["id"]).json()["data"]["status"]
            == "succeeded"
        )


def test_live_magic_fails_honestly(api):
    client, app, _ = api
    app.state.service.agents["explore_magic"] = ExploreAgent("llm")
    run = post(client, "/v1/magic/runs", magic()).json()["data"]
    app.state.service.work_once()
    result = client.get("/v1/agent-runs/" + run["id"]).json()["data"]
    assert result["status"] == "failed"
    assert result["error"]["code"] == "provider_unavailable"


@pytest.mark.parametrize(
    "agent,agent_input",
    [(PlanningAgent("llm"), PlanInput()), (PackingAgent("llm"), PackInput())],
)
def test_model_agents_validate_and_strip_unverified_provenance(
    monkeypatch, agent, agent_input
):
    fixture = agent.fixture(agent_input, NOW).model_dump(mode="json")
    fixture.update(
        data_mode="live",
        sources=[
            {
                "provider": "made-up",
                "source_url": "https://example.com/",
                "observed_at": NOW.isoformat(),
                "data_mode": "live",
                "availability": "verified",
            }
        ],
    )
    with fake_messages_api(
        [tool_use("submit_" + agent.name, fixture, "submit1"), text("Done.")],
        monkeypatch,
    ) as seen:
        result = agent.propose(agent_input, NOW)
    assert result.data_mode == "live" and result.sources == []
    assert seen


def test_magic_unknown_budget_onward_and_dst():
    class Provider:
        data_mode = "live"

        def discover(self, request, now):
            source = Source(
                provider="test",
                source_url="https://example.com/",
                observed_at=now,
                expires_at=now + timedelta(minutes=10),
                data_mode="live",
                availability="verified",
                cost_status="verified",
            )
            return [
                Candidate(
                    "a",
                    "Test option",
                    "culture",
                    request.location,
                    20,
                    10,
                    20,
                    Money(amount_minor=500, currency="EUR"),
                    now,
                    now + timedelta(hours=2),
                    source,
                )
            ]

    agent = ExploreAgent(provider=Provider())
    request = MagicInput(
        **magic(),
        next_commitment={
            "starts_at": "2026-10-25T02:20:00+01:00",
            "location": magic()["location"],
        },
    )
    assert not agent.propose(
        request, NOW
    ).recommendations  # only 50 real minutes; needs 65
    request = MagicInput(**magic(), budget={"amount_minor": 499, "currency": "EUR"})
    assert not agent.propose(request, NOW).recommendations
    request = MagicInput(**magic(), budget={"amount_minor": 500, "currency": "EUR"})
    assert agent.propose(request, NOW).recommendations
    provider = Provider()
    original = provider.discover
    from dataclasses import replace

    provider.discover = lambda req, now: [
        replace(original(req, now)[0], outbound_minutes=None)
    ]
    agent = ExploreAgent(provider=provider)
    assert not agent.propose(request, NOW).recommendations
    unknown = agent.propose(
        request.model_copy(update={"allow_unknown_feasibility": True}), NOW
    )
    assert unknown.uncertain_recommendations[0].slack_minutes is None
    assert unknown.uncertain_recommendations[0].valid_until <= NOW + timedelta(
        minutes=10
    )


def test_checked_contract_does_not_drift():
    from scripts.export_control_contract import ROOT, artifacts, render

    for path, value in artifacts().items():
        assert (ROOT / path).read_text() == render(value), f"Regenerate {path}"


def test_no_missing_standalone_constraints_or_outside_area(api):
    client, _, _ = api
    assert (
        post(client, "/v1/agent-runs", {"agent": "plan_book", "input": {}}).status_code
        == 422
    )
    assert (
        post(
            client,
            "/v1/magic/runs",
            {**magic(), "location": {"latitude": 91, "longitude": 0}},
        ).json()["error"]["code"]
        == "invalid_request"
    )


def test_live_runner_never_receives_private_trip_data(monkeypatch):
    from super_travel.core.trip_context import load_trip

    captured = []

    def runner(**kwargs):
        captured.append(kwargs["message"])
        return PlanningAgent().fixture(PlanInput(), NOW)

    monkeypatch.setattr("super_travel.agents.proposals.run_specialist", runner)
    trip = load_trip()
    before = trip.model_dump(mode="json")
    PlanningAgent("llm").run("Suggest a walk", trip)
    assert trip.model_dump(mode="json") == before
    assert all(
        field not in captured[0]
        for field in (
            "documents",
            "reservations",
            "expenses",
            "travelers",
            "passport",
            "pnr",
        )
    )


def test_trip_omission_and_explicit_default_have_distinct_replay_digest(api):
    client, _, _ = api
    trip = post(
        client,
        "/v1/trips",
        {
            "title": "Barcelona",
            "destination": "Barcelona",
            "start_date": "2026-11-13",
            "end_date": "2026-11-15",
            "timezone": "UTC",
        },
    ).json()["data"]
    key = uuid4()
    body = {"agent": "plan_book", "trip_id": trip["id"], "input": {}}
    assert post(client, "/v1/agent-runs", body, key).status_code == 202
    assert (
        post(
            client,
            "/v1/agent-runs",
            {**body, "input": {"timezone": "Europe/Madrid"}},
            key,
        ).status_code
        == 409
    )


def test_default_worker_processes_fixture_without_manual_tick(tmp_path):
    import time

    app = create_app(path=str(tmp_path / "worker.sqlite3"), tokens={"alice": ALICE})
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer alice"
        run = post(client, "/v1/agent-runs", plan()).json()["data"]
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            result = client.get("/v1/agent-runs/" + run["id"]).json()["data"]
            if result["status"] == "succeeded":
                break
            time.sleep(0.02)
        assert result["status"] == "succeeded"
