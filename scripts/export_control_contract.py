"""Export schemas and synthetic response fixtures without credentials/network access."""

import json
from datetime import UTC, datetime
from pathlib import Path

from super_travel.agents.explore import ExploreAgent
from super_travel.agents.proposals import PackingAgent, PlanningAgent
from super_travel.consumer.agents import HelperAdapter
from super_travel.control.app import create_app
from super_travel.control.schemas import HelperInput, MagicInput, PackInput, PlanInput

ROOT = Path(__file__).resolve().parents[1]


def artifacts():
    travel = {
        "destination": "Barcelona",
        "start_date": "2026-11-13",
        "end_date": "2026-11-15",
    }
    magic = {
        "location": {"latitude": 41.385, "longitude": 2.174},
        "available_minutes": 120,
        "interests": ["culture"],
        "budget": {"amount_minor": 2000, "currency": "EUR"},
    }
    now = datetime(2026, 10, 11, 12, tzinfo=UTC)
    proposals = {
        "plan_book": PlanningAgent()
        .propose(PlanInput(**travel), now)
        .model_dump(mode="json"),
        "pack_shop": PackingAgent()
        .propose(PackInput(**travel), now)
        .model_dump(mode="json"),
        "explore_magic": ExploreAgent()
        .propose(MagicInput(**magic), now)
        .model_dump(mode="json"),
        "magic_empty": ExploreAgent()
        .propose(MagicInput(**{**magic, "available_minutes": 15}), now)
        .model_dump(mode="json"),
    }
    for agent in ("essentials", "recovery"):
        proposals[agent] = (
            HelperAdapter(agent,"fixture")
            .propose(HelperInput(**travel), now)
            .model_dump(mode="json")
        )
    requests = {
        agent: {"agent": agent, "input": magic if agent == "explore_magic" else travel}
        for agent in (
            "plan_book",
            "pack_shop",
            "explore_magic",
            "essentials",
            "recovery",
        )
    }
    return {
        "packages/contracts/openapi.json": create_app().openapi(),
        "packages/contracts/fixtures/agent_requests.json": requests,
        "packages/contracts/fixtures/agent_proposals.json": proposals,
    }


def render(value):
    return json.dumps(value, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    for relative, value in artifacts().items():
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render(value))
        print(relative)
