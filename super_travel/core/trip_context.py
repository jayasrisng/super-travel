"""Shared trip state. Canonical example: fixtures/demo_trip.json.

Models are deliberately permissive (extra="allow") so each agent can add fields while
the team converges. Type only what more than one agent relies on.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

REPO_ROOT = Path(__file__).resolve().parents[2]
DEMO_TRIP_PATH = REPO_ROOT / "fixtures" / "demo_trip.json"


class _Model(BaseModel):
    model_config = ConfigDict(extra="allow")


class Location(_Model):
    city: str
    country: str
    timezone: str
    currency: str


class Traveler(_Model):
    id: str
    name: str
    citizenship: str
    residence: str | None = None


class Destination(_Model):
    id: str
    city: str
    country: str
    arrive: date
    depart: date
    currency: str


class Task(_Model):
    id: str
    title: str
    owner_agent: str
    traveler_id: str | None = None
    due: date | None = None
    status: str = "todo"


class TripContext(_Model):
    trip_id: str
    name: str
    status: str
    home: Location
    travelers: list[Traveler]
    destinations: list[Destination]
    budget: dict[str, Any] = Field(default_factory=dict)
    preferences: dict[str, Any] = Field(default_factory=dict)
    segments: list[dict[str, Any]] = Field(default_factory=list)
    stays: list[dict[str, Any]] = Field(default_factory=list)
    reservations: list[dict[str, Any]] = Field(default_factory=list)
    documents: list[dict[str, Any]] = Field(default_factory=list)
    expenses: list[dict[str, Any]] = Field(default_factory=list)
    checklist: list[Task] = Field(default_factory=list)
    packing: dict[str, Any] = Field(default_factory=dict)
    incidents: list[dict[str, Any]] = Field(default_factory=list)

    def to_prompt_json(self) -> str:
        """Stable JSON for prompts: no demo annotations, sorted keys (keeps prompt caching effective)."""
        data = _strip_private(self.model_dump(mode="json"))
        return json.dumps(data, sort_keys=True, ensure_ascii=False, indent=1)

    def add_checklist_items(self, items: list[Task]) -> list[Task]:
        """Append items, skipping titles that already exist. Returns the ones added."""
        existing = {t.title.strip().lower() for t in self.checklist}
        added = [t for t in items if t.title.strip().lower() not in existing]
        self.checklist.extend(added)
        return added

    def next_checklist_id(self) -> str:
        return f"c{len(self.checklist) + 1}"


def _strip_private(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: _strip_private(v) for k, v in value.items() if not k.startswith("_")}
    if isinstance(value, list):
        return [_strip_private(v) for v in value]
    return value


def load_trip(path: Path = DEMO_TRIP_PATH) -> TripContext:
    return TripContext.model_validate_json(path.read_text())


def demo_today(path: Path = DEMO_TRIP_PATH) -> date:
    """The fixture's frozen 'today', so demo runs are reproducible."""
    return date.fromisoformat(json.loads(path.read_text())["_meta"]["today"])


def save_trip(trip: TripContext, path: Path) -> None:
    path.write_text(trip.model_dump_json(indent=2) + "\n")
