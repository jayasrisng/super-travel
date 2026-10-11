"""Consumer journey, privacy, versioning, replay, and exact-money invariants."""

import base64
import io
from collections import Counter
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from super_travel.control.app import create_app


@pytest.fixture
def api(tmp_path):
    clock = [datetime(2026, 10, 11, 1, tzinfo=UTC)]
    app = create_app(
        path=str(tmp_path / "consumer.sqlite3"),
        tokens={"alice": uuid4(), "bob": uuid4()},
        worker=False,
        now=lambda: clock[0],
        demo_auth=True,
    )
    with TestClient(app) as client:
        client.headers["Authorization"] = "Bearer alice"
        yield client, app, clock


def post(client, path, body=None, version=None, key=None):
    headers = {"Idempotency-Key": str(key or uuid4())}
    if version:
        headers["If-Match"] = f'"{version}"'
    return client.post("/v1" + path, json={} if body is None else body, headers=headers)


def data(response):
    assert response.is_success, response.text
    return response.json()["data"]


def trip(client, **changes):
    return data(
        post(
            client,
            "/consumer/trips",
            {
                "title": "Tokyo with family",
                "destination": "Tokyo",
                "timezone": "Asia/Tokyo",
                "currency": "JPY",
                "date_certainty": "confirmed",
                "start_date": "2026-11-13",
                "end_date": "2026-11-19",
                "traveler_configuration": {
                    "adult_count": 2,
                    "child_count": 1,
                    "infant_count": 0,
                },
                "dietary": "Vegetarian",
                "accessibility": "Easy walks",
                "interests": ["museums", "food"],
                "budget": {"amount_minor": 120000, "currency": "JPY"},
                **changes,
            },
        )
    )


def notebook(client, t):
    return data(client.get("/v1/consumer/trips/" + t["id"]))


def primary(client, t):
    return next(
        task
        for task in notebook(client, t)["tasks"]
        if task["assigned_agent"] == "plan_book"
    )


def route(t, task):
    return f"/consumer/trips/{t['id']}/tasks/{task['id']}"


def test_tokyo_checklist_five_real_jobs_and_approval(api):
    client, app, _ = api
    t = trip(client)
    book = notebook(client, t)
    assert len(book["participants"]) == 3
    assert len(book["tasks"]) >= 10
    assert {task["assigned_agent"] for task in book["tasks"]} == {
        "plan_book",
        "pack_shop",
        "explore_magic",
        "essentials",
        "recovery",
    }
    for agent in ("plan_book", "pack_shop", "explore_magic", "essentials", "recovery"):
        task = next(
            task
            for task in notebook(client, t)["tasks"]
            if task["assigned_agent"] == agent
        )
        payload = (
            {
                "magic": {
                    "location": {"latitude": 35.6812, "longitude": 139.7671},
                    "available_minutes": 120,
                    "city": "Tokyo",
                    "timezone": "Asia/Tokyo",
                }
            }
            if agent == "explore_magic"
            else {}
        )
        queued = data(post(client, route(t, task) + "/run", payload, task["version"]))
        assert queued["status"] == "queued"
        assert app.state.service.work_once()
        ready = next(
            item for item in notebook(client, t)["tasks"] if item["id"] == task["id"]
        )
        assert ready["status"] == "ready_for_review"
        assert ready["result"]["data_mode"] == "fixture"
        accepted = data(
            post(
                client,
                route(t, ready) + "/decision",
                {"action": "approve"},
                ready["version"],
            )
        )
        assert accepted["status"] != "completed"
    assert notebook(client, t)["itinerary"]


def test_task_edit_cancels_old_run_preserves_user_text_and_stale_version(api):
    client, app, _ = api
    t = trip(client)
    task = primary(client, t)
    queued = data(post(client, route(t, task) + "/run", {}, task["version"]))
    custom = {
        "title": "Birthday dinner for mom",
        "description": "Vegetarian with easy access",
        "agent_instructions": "Research only; no booking",
        "assigned_agent": "plan_book",
    }
    edit = client.patch(
        "/v1" + route(t, task),
        json=custom,
        headers={"If-Match": f'"{queued["version"]}"'},
    )
    updated = data(edit)
    assert updated["status"] == "not_started" and updated["agent_run_id"] is None
    assert (
        data(client.get("/v1/agent-runs/" + queued["agent_run_id"]))["status"]
        == "cancelled"
    )
    assert (
        client.patch(
            "/v1" + route(t, task),
            json={"title": "Stale edit"},
            headers={"If-Match": f'"{queued["version"]}"'},
        ).status_code
        == 412
    )
    assert primary(client, t)["title"] == custom["title"]
    assert not app.state.service.work_once()


def test_missing_dates_and_stale_trip_context(api):
    client, app, _ = api
    flexible = trip(
        client,
        start_date=None,
        end_date=None,
        date_certainty="flexible",
        destination="Undecided",
    )
    task = primary(client, flexible)
    assert (
        data(post(client, route(flexible, task) + "/run", {}, task["version"]))[
            "status"
        ]
        == "needs_more_information"
    )
    t = trip(client)
    task = primary(client, t)
    post(client, route(t, task) + "/run", {}, task["version"])
    app.state.service.work_once()
    ready = primary(client, t)
    payload = {
        k: v
        for k, v in t.items()
        if k not in ("id", "version", "context_version", "owner_user_id")
    }
    payload["dietary"] = "Vegan"
    data(
        client.put(
            "/v1/consumer/trips/" + t["id"], json=payload, headers={"If-Match": '"1"'}
        )
    )
    assert (
        post(
            client,
            route(t, ready) + "/decision",
            {"action": "approve"},
            ready["version"],
        ).status_code
        == 409
    )


def test_actor_trip_isolation_and_replay(api):
    client, _, _ = api
    t = trip(client)
    other = trip(client, title="Another trip")
    task = primary(client, t)
    assert (
        client.patch(
            "/v1" + route(other, task),
            json={"title": "Cross trip"},
            headers={"If-Match": '"1"'},
        ).status_code
        == 404
    )
    key = uuid4()
    payload = {"title": "My own note"}
    first = post(client, f"/consumer/trips/{t['id']}/tasks", payload, key=key)
    assert (
        post(client, f"/consumer/trips/{t['id']}/tasks", payload, key=key).json()
        == first.json()
    )
    assert (
        post(
            client, f"/consumer/trips/{t['id']}/tasks", {"title": "Changed"}, key=key
        ).status_code
        == 409
    )
    client.headers["Authorization"] = "Bearer bob"
    assert client.get("/v1/consumer/trips/" + t["id"]).status_code == 404
    assert data(client.get("/v1/consumer/home"))["trips"] == []


def test_wardrobe_seed_photo_sanitization_edit_delete_and_isolation(api):
    client, _, _ = api
    items = data(client.get("/v1/consumer/wardrobe"))
    assert Counter(i["category"] for i in items) == {
        "tops": 10,
        "bottoms": 10,
        "shoes": 4,
        "accessories": 10,
    }
    item = items[0]
    output = io.BytesIO()
    image = Image.new("RGB", (1200, 800), "red")
    exif = Image.Exif()
    exif[270] = "private metadata"
    image.save(output, "JPEG", exif=exif)
    uploaded = data(
        post(
            client,
            f"/consumer/wardrobe/{item['id']}/photo",
            {
                "content_base64": base64.b64encode(output.getvalue()).decode(),
                "mime": "image/jpeg",
            },
            item["version"],
        )
    )
    response = client.get(uploaded["image"])
    assert response.status_code == 200
    with Image.open(io.BytesIO(response.content)) as clean:
        assert clean.width <= 1000 and not clean.getexif()
    client.headers["Authorization"] = "Bearer bob"
    assert client.get(uploaded["image"]).status_code == 404
    client.headers["Authorization"] = "Bearer alice"
    assert (
        post(
            client,
            f"/consumer/wardrobe/{item['id']}/photo",
            {"content_base64": "not an image", "mime": "image/png"},
            uploaded["version"],
        ).status_code
        == 422
    )
    assert (
        client.delete(
            "/v1/consumer/wardrobe/" + item["id"],
            headers={"If-Match": f'"{uploaded["version"]}"'},
        ).status_code
        == 204
    )
    assert len(data(client.get("/v1/consumer/wardrobe"))) == 33
    assert client.get(uploaded["image"]).status_code == 404


def test_votes_undo_packing_dedup_status_and_refresh(api):
    client, app, _ = api
    t = trip(client)
    looks = data(post(client, "/consumer/outfits/generate", {"trip_id": t["id"]}))
    assert len(looks) > 3
    for outfit in looks[:3]:
        data(
            post(client, f"/consumer/outfits/{outfit['id']}/vote", {"decision": "like"})
        )
    rejected = looks[3]
    data(
        post(
            client, f"/consumer/outfits/{rejected['id']}/vote", {"decision": "dislike"}
        )
    )
    assert rejected["id"] not in [
        o["id"]
        for o in data(post(client, "/consumer/outfits/generate", {"trip_id": t["id"]}))
    ]
    assert (
        client.delete(f"/v1/consumer/outfits/{rejected['id']}/vote").status_code == 204
    )
    packing = data(post(client, f"/consumer/trips/{t['id']}/packing"))
    expected = {identifier for outfit in looks[:3] for identifier in outfit["item_ids"]}
    assert packing["unique_items"] == len(expected) < 12
    assert len({i["wardrobe_item_id"] for i in packing["items"]}) == len(
        packing["items"]
    )
    first = packing["items"][0]
    edited = data(
        client.patch(
            f"/v1/consumer/trips/{t['id']}/packing/" + first["id"],
            json={"packed": True, "availability": "dirty"},
            headers={"If-Match": '"1"'},
        )
    )
    rebuilt = data(post(client, f"/consumer/trips/{t['id']}/packing"))
    assert (
        next(i for i in rebuilt["items"] if i["id"] == first["id"])["availability"]
        == "dirty"
    )
    assert notebook(client, t)["packing"]["items"]
    regenerated = data(post(client, "/consumer/outfits/generate", {"trip_id": t["id"]}))
    assert all(first["wardrobe_item_id"] not in o["item_ids"] for o in regenerated)
    assert edited["packed"]
    assert app.state.store.db.execute(
        "SELECT count(*) FROM objects WHERE kind='packing'"
    ).fetchone()[0] == len(expected)


def test_calendar_selection_disconnect_and_briefing_ready_only(api):
    client, _, _ = api
    t = trip(client)
    look = data(post(client, "/consumer/outfits/generate", {"trip_id": t["id"]}))[0]
    data(post(client, f"/consumer/outfits/{look['id']}/vote", {"decision": "like"}))
    packing = data(post(client, f"/consumer/trips/{t['id']}/packing"))
    assert data(client.get(f"/v1/consumer/trips/{t['id']}/briefing"))["outfit"] is None
    for item in packing["items"]:
        data(
            client.patch(
                f"/v1/consumer/trips/{t['id']}/packing/" + item["id"],
                json={"packed": True},
                headers={"If-Match": '"1"'},
            )
        )
    brief = data(client.get(f"/v1/consumer/trips/{t['id']}/briefing"))
    assert brief["outfit"]["id"] == look["id"]
    assert brief["weather_mode"] == "fixture" and brief["delivery"] == "in_app_only"
    connection = data(
        client.put(
            "/v1/consumer/calendar",
            json={"enabled": True, "selected_event_ids": ["museum"]},
        )
    )
    selected = data(client.get(f"/v1/consumer/trips/{t['id']}/briefing"))["schedule"]
    assert len(selected) == 1 and selected[0]["event_type"] == "museum"
    data(
        client.put(
            "/v1/consumer/calendar",
            json={"enabled": False, "selected_event_ids": []},
            headers={"If-Match": f'"{connection["version"]}"'},
        )
    )
    assert data(client.get(f"/v1/consumer/trips/{t['id']}/briefing"))["schedule"] == []


def test_partial_participant_and_exact_expense_split(api):
    client, _, _ = api
    t = trip(client)
    participants = notebook(client, t)["participants"]
    partial = data(
        post(
            client,
            f"/consumer/trips/{t['id']}/participants",
            {"label": "Joining later", "arrive": "2026-11-15", "depart": "2026-11-17"},
        )
    )
    assert partial["arrive"] == "2026-11-15"
    assert (
        post(
            client,
            f"/consumer/trips/{t['id']}/participants",
            {"label": "Outside dates", "arrive": "2026-11-10"},
        ).status_code
        == 422
    )
    split = [p["id"] for p in participants]
    expense = data(
        post(
            client,
            f"/consumer/trips/{t['id']}/expenses",
            {
                "title": "Lunch",
                "money": {"amount_minor": 100, "currency": "JPY"},
                "paid_by": split[0],
                "split_between": split,
            },
        )
    )
    assert sorted(expense["shares_minor"].values()) == [33, 33, 34]
    foreign = notebook(client, trip(client, title="Other"))["participants"][0]["id"]
    assert (
        post(
            client,
            f"/consumer/trips/{t['id']}/expenses",
            {
                "title": "Invalid",
                "money": {"amount_minor": 100, "currency": "JPY"},
                "paid_by": split[0],
                "split_between": [foreign],
            },
        ).status_code
        == 422
    )


def test_share_redaction_hash_only_replay_revocation_and_expiry(api):
    client, app, clock = api
    t = trip(client)
    key = uuid4()
    shared = data(post(client, f"/consumer/trips/{t['id']}/shares", key=key))
    assert data(post(client, f"/consumer/trips/{t['id']}/shares", key=key)) == shared
    public = data(client.get("/v1/consumer/share/" + shared["token"]))
    assert not {"tasks", "packing", "expenses", "dietary"} & public.keys()
    for table in ("objects", "replays"):
        rows = app.state.store.db.execute(f"SELECT body FROM {table}").fetchall()
        assert all(shared["token"] not in row[0] for row in rows)
    assert (
        client.delete(
            f"/v1/consumer/trips/{t['id']}/shares/{shared['id']}",
            headers={"If-Match": '"1"'},
        ).status_code
        == 204
    )
    assert client.get("/v1/consumer/share/" + shared["token"]).status_code == 404
    second = data(post(client, f"/consumer/trips/{t['id']}/shares"))
    clock[0] += timedelta(days=2)
    assert client.get("/v1/consumer/share/" + second["token"]).status_code == 404


def test_local_cookie_sessions_never_shared_bearer_and_origin_rejected(api):
    client, _, _ = api
    client.headers.pop("Authorization")
    session = data(post(client, "/demo/session"))
    assert session["mode"] == "local_demo"
    assert "HttpOnly" in client.cookies.__repr__() or client.cookies.get("wonder_demo")
    assert data(client.get("/v1/consumer/home"))["wardrobe_count"] == 34
    assert (
        client.get(
            "/v1/consumer/home", headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/v1/demo/session", json={}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert client.delete("/v1/demo/session").status_code == 204
    assert client.get("/v1/consumer/home").status_code == 401


def test_manual_essentials_survive_rebuild_and_shared_itinerary_is_redacted(api):
    client, _, _ = api
    t = trip(client)
    essential = data(
        post(
            client,
            "/consumer/wardrobe",
            {"name": "Travel adapter", "category": "essentials"},
        )
    )
    manual = data(
        post(
            client,
            f"/consumer/trips/{t['id']}/packing/items",
            {"wardrobe_item_id": essential["id"]},
        )
    )
    assert manual["manual"] and manual["outfit_ids"] == []
    data(
        post(
            client,
            f"/consumer/trips/{t['id']}/packing/items",
            {"wardrobe_item_id": essential["id"]},
        )
    )
    assert data(post(client, f"/consumer/trips/{t['id']}/packing"))["unique_items"] == 1
    partial = data(
        post(
            client,
            f"/consumer/trips/{t['id']}/participants",
            {"label": "Joining late", "arrive": "2026-11-15"},
        )
    )
    assert (
        post(
            client,
            f"/consumer/trips/{t['id']}/itinerary",
            {
                "title": "Too early",
                "day": "2026-11-14",
                "local_time": "10:00",
                "participant_ids": [partial["id"]],
            },
        ).status_code
        == 422
    )
    saved = data(
        post(
            client,
            f"/consumer/trips/{t['id']}/itinerary",
            {
                "title": "Museum together",
                "day": "2026-11-15",
                "local_time": "10:00",
                "participant_ids": [partial["id"]],
            },
        )
    )
    segment = data(
        post(
            client,
            f"/consumer/trips/{t['id']}/segments",
            {
                "title": "A Kyoto chapter",
                "destination": "Kyoto",
                "start_date": "2026-11-16",
                "end_date": "2026-11-18",
            },
        )
    )
    assert segment["destination"] == "Kyoto" and notebook(client, t)["segments"]
    share = data(post(client, f"/consumer/trips/{t['id']}/shares"))
    public = data(client.get("/v1/consumer/share/" + share["token"]))
    assert public["itinerary"][0]["title"] == saved["title"]
    assert (
        "participant_ids" not in public["itinerary"][0]
        and "trip_id" not in public["itinerary"][0]
    )
    other = trip(client, title="Other")
    assert (
        post(
            client,
            f"/consumer/trips/{other['id']}/packing/items",
            {"wardrobe_item_id": uuid4().__str__()},
        ).status_code
        == 404
    )


def test_unconfigured_event_providers_fail_instead_of_fabricating(api):
    from super_travel.agents.explore import ProviderUnavailable
    from super_travel.consumer.providers import EVENT_PROVIDERS
    from super_travel.control.schemas import MagicInput

    request = MagicInput(
        location={"latitude": 35.6812, "longitude": 139.7671}, available_minutes=120
    )
    for provider in EVENT_PROVIDERS:
        with pytest.raises(ProviderUnavailable):
            provider.discover(request, datetime.now(UTC))


def test_expired_agent_draft_cannot_be_applied(api):
    client, app, clock = api
    t = trip(client)
    task = primary(client, t)
    post(client, route(t, task) + "/run", {}, task["version"])
    app.state.service.work_once()
    ready = primary(client, t)
    clock[0] += timedelta(hours=25)
    response = post(
        client, route(t, ready) + "/decision", {"action": "approve"}, ready["version"]
    )
    assert response.status_code in (409, 412)
    latest = primary(client, t)
    assert latest["status"] == "failed" and latest["result"] is None
    assert not notebook(client, t)["itinerary"]


def test_daily_brief_uses_trip_local_today_and_current_clothing_state(api):
    client, _, clock = api
    t = trip(client)
    looks = data(post(client, "/consumer/outfits/generate", {"trip_id": t["id"]}))
    look = looks[0]
    data(post(client, f"/consumer/outfits/{look['id']}/vote", {"decision": "like"}))
    items = data(post(client, f"/consumer/trips/{t['id']}/packing"))["items"]
    for item in items:
        data(
            client.patch(
                f"/v1/consumer/trips/{t['id']}/packing/{item['id']}",
                json={"packed": True},
                headers={"If-Match": '"1"'},
            )
        )
    clock[0] = datetime(2026, 11, 14, 23, tzinfo=UTC)
    brief = data(client.get(f"/v1/consumer/trips/{t['id']}/briefing"))
    assert brief["day"] == "2026-11-15" and brief["outfit"]
    clothing = next(
        i
        for i in data(client.get("/v1/consumer/wardrobe"))
        if i["id"] == look["item_ids"][0]
    )
    payload = {
        name: value
        for name, value in clothing.items()
        if name not in ("id", "version", "image_mode")
    }
    payload.update(availability="dirty", name="Updated shirt")
    data(
        client.put(
            "/v1/consumer/wardrobe/" + clothing["id"],
            json=payload,
            headers={"If-Match": '"1"'},
        )
    )
    assert data(client.get(f"/v1/consumer/trips/{t['id']}/briefing"))["outfit"] is None
    assert "Updated shirt" in [
        i["name"] for i in notebook(client, t)["packing"]["items"]
    ]
