import json
from datetime import date

import pytest

from super_travel.agents import REGISTRY
from super_travel.agents.essentials import tools
from super_travel.agents.essentials.agent import _CLIENT_TOOLS, _SUBMIT_SCHEMA, EssentialsAgent
from super_travel.core.trip_context import Task, demo_today, load_trip


def test_country_info_known_and_unknown():
    pt = json.loads(tools.get_country_info("pt"))
    assert pt["emergency"]["general"] == "112"
    assert "F" in pt["plug_types"]
    assert "error" in json.loads(tools.get_country_info("ZZ"))


def test_esim_plans_cover_all_countries_sorted_by_price():
    plans = json.loads(tools.find_esim_plans(["PT", "ES"], 9))["plans"]
    assert plans and all({"PT", "ES"} <= set(p["countries"]) for p in plans)
    assert [p["price_usd"] for p in plans] == sorted(p["price_usd"] for p in plans)
    assert json.loads(tools.find_esim_plans(["PT", "JP"], 9))["plans"] == []


def test_exchange_rate_same_currency_needs_no_network():
    out = json.loads(tools.get_exchange_rate("eur", "EUR", 50))
    assert out["converted"] == 50


@pytest.mark.network
def test_exchange_rate_live():
    out = json.loads(tools.get_exchange_rate("USD", "EUR", 100))
    assert 50 < out["converted"] < 150


def test_tool_definitions_serialize():
    names = [t.to_dict()["name"] for t in _CLIENT_TOOLS]
    assert names == ["get_country_info", "get_exchange_rate", "find_esim_plans"]
    assert "$ref" not in json.dumps(_SUBMIT_SCHEMA)
    assert set(_SUBMIT_SCHEMA["required"]) >= {"reply", "sections", "checklist_items", "handoffs"}


def test_demo_trip_loads_and_prompt_strips_demo_annotations():
    trip = load_trip()
    assert demo_today() == date(2026, 11, 3)
    prompt = trip.to_prompt_json()
    assert "\"_demo\"" not in prompt and "\"_meta\"" not in prompt and "Lisbon" in prompt


def test_checklist_dedupes_by_title():
    trip = load_trip()
    before = len(trip.checklist)
    added = trip.add_checklist_items([
        Task(id="x1", title="Pick travel insurance", owner_agent="essentials"),
        Task(id="x2", title="Download offline maps", owner_agent="essentials"),
    ])
    assert [t.title for t in added] == ["Download offline maps"]
    assert len(trip.checklist) == before + 1


def test_registered():
    assert isinstance(REGISTRY["essentials"], EssentialsAgent)
