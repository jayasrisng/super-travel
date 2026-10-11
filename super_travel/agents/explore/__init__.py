"""Deterministic Barcelona feasibility over normalized provider candidates."""

from datetime import UTC, datetime, timedelta
from typing import Annotated, Protocol
from uuid import NAMESPACE_URL, uuid5

from pydantic import AwareDatetime, ConfigDict, Field
from pydantic.dataclasses import dataclass

from super_travel.control.schemas import (
    ExploreProposal,
    Location,
    MagicInput,
    Money,
    Source,
)
from super_travel.core.agent import AgentResult


class ProviderUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class Candidate:
    key: str
    title: str
    category: str
    location: Location
    duration_minutes: Annotated[int, Field(ge=1, le=480, strict=True)]
    outbound_minutes: Annotated[int, Field(ge=0, strict=True)] | None
    onward_minutes: Annotated[int, Field(ge=0, strict=True)] | None
    cost: Money | None
    opens_at: AwareDatetime | None
    closes_at: AwareDatetime | None
    source: Source


class DiscoveryProvider(Protocol):
    data_mode: str

    def discover(self, request: MagicInput, now: datetime) -> list[Candidate]: ...


class FixtureProvider:
    data_mode = "fixture"

    def discover(self, request, now):
        # Routes/hours below are simulated scenarios, never geographic/live assertions.
        currency = (
            request.budget.currency
            if request.budget
            else ("JPY" if request.city == "Tokyo" else "EUR")
        )
        source = Source(
            provider="wonder-fixture",
            source_url="https://example.com/wonder-fixtures",
            observed_at=now,
            expires_at=now + timedelta(minutes=15),
            data_mode="fixture",
            availability="unverified",
            cost_status="estimated",
        )
        return [
            Candidate(
                key,
                title,
                category,
                Location(
                    latitude=max(-89.9, min(89.9, request.location.latitude + (lat - 41.385))),
                    longitude=max(
                        -179.9, min(179.9, request.location.longitude + (lon - 2.174))
                    ),
                ),
                duration,
                outbound,
                onward,
                Money(amount_minor=cost, currency=currency),
                now - timedelta(hours=1),
                now + timedelta(hours=8),
                source,
            )
            for key, title, category, lat, lon, duration, outbound, onward, cost in [
                (
                    "walk",
                    f"Example {request.city} neighbourhood walk",
                    "culture",
                    41.383,
                    2.176,
                    30,
                    10,
                    15,
                    0,
                ),
                (
                    "coffee",
                    "Example coffee break",
                    "food",
                    41.386,
                    2.174,
                    20,
                    8,
                    12,
                    500,
                ),
                ("park", "Example park visit", "nature", 41.388, 2.187, 45, 15, 20, 0),
            ]
        ]


class ExploreAgent:
    name = "explore"
    description = "Barcelona Magic feasibility specialist"

    def __init__(self, mode="fixture", provider=None):
        self.mode = mode
        self.provider = provider or (FixtureProvider() if mode == "fixture" else None)

    @staticmethod
    def supports(location):
        # Global synthetic origins only; this does not assert live place coverage.
        return -90 <= location.latitude <= 90 and -180 <= location.longitude <= 180

    def run(self, task, trip, today=None):
        request = MagicInput.model_validate_json(task)
        proposal = self.propose(request, datetime.now(UTC))
        return AgentResult(reply=proposal.reply, data=proposal.model_dump(mode="json"))

    def propose(self, request, now):
        if self.provider is None:
            raise ProviderUnavailable(
                "Live discovery and route providers are not configured"
            )
        if not self.supports(request.location):
            raise ValueError("Magic currently covers Barcelona only")
        now = now.astimezone(UTC)
        deadline = now + timedelta(minutes=request.available_minutes)
        if request.next_commitment:
            deadline = min(deadline, request.next_commitment.starts_at.astimezone(UTC))
        available = int((deadline - now).total_seconds() // 60)
        feasible, uncertain = [], []
        warnings = (
            ["Fixture routes, hours and costs are simulated; verify before travelling."]
            if self.provider.data_mode == "fixture"
            else []
        )
        for candidate in self.provider.discover(request, now):
            source = candidate.source
            if source.data_mode != self.provider.data_mode or source.observed_at > now:
                continue
            if not self.supports(candidate.location):
                continue
            if source.expires_at and source.expires_at <= now:
                continue
            if source.availability == "unavailable" or candidate.duration_minutes <= 0:
                continue
            if any(
                value is not None and value < 0
                for value in (candidate.outbound_minutes, candidate.onward_minutes)
            ):
                continue
            onward = candidate.onward_minutes if request.next_commitment else 0
            unknown = (
                candidate.outbound_minutes is None
                or onward is None
                or candidate.opens_at is None
                or candidate.closes_at is None
                or source.expires_at is None
            )
            if self.provider.data_mode == "live" and source.availability != "verified":
                unknown = True
            if request.budget:
                if candidate.cost is None or source.cost_status == "unknown":
                    unknown = True
                elif (
                    candidate.cost.currency != request.budget.currency
                    or candidate.cost.amount_minor > request.budget.amount_minor
                ):
                    continue
            minimum = (
                (candidate.outbound_minutes or 0)
                + candidate.duration_minutes
                + (onward or 0)
                + request.buffer_minutes
            )
            if minimum > available:
                continue
            arrival = now + timedelta(minutes=candidate.outbound_minutes or 0)
            finish = arrival + timedelta(minutes=candidate.duration_minutes)
            if candidate.opens_at and arrival < candidate.opens_at:
                continue
            if candidate.closes_at and finish > candidate.closes_at:
                continue
            if unknown and not request.allow_unknown_feasibility:
                continue
            validity = min(
                now + timedelta(minutes=15), deadline, source.expires_at or deadline
            )
            if candidate.closes_at:
                validity = min(validity, candidate.closes_at)
            if validity <= now:
                continue
            item = {
                "id": uuid5(NAMESPACE_URL, candidate.key),
                "title": candidate.title,
                "category": candidate.category,
                "location": candidate.location,
                "rank": 1,
                "reason": "Fits the supplied constraints"
                if not unknown
                else "Feasibility needs verification",
                "duration_minutes": candidate.duration_minutes,
                "outbound_minutes": candidate.outbound_minutes,
                "onward_minutes": onward,
                "buffer_minutes": request.buffer_minutes,
                "slack_minutes": None if unknown else available - minimum,
                "cost": candidate.cost,
                "cost_status": source.cost_status if candidate.cost else "unknown",
                "feasibility": "unknown" if unknown else "feasible",
                "evaluated_at": now,
                "valid_until": validity,
                "provenance": [source],
                "assumptions": ["No booking or attendance is implied."],
            }
            (uncertain if unknown else feasible).append(item)
        for group in (feasible, uncertain):
            group.sort(
                key=lambda item: (
                    item["category"] not in request.interests,
                    -(item["slack_minutes"] or 0),
                    str(item["id"]),
                )
            )
            for rank, item in enumerate(group, 1):
                item["rank"] = rank
        if not feasible:
            warnings.append(
                "No verified feasible options for this window; try a longer window or review uncertain options."
            )
        return ExploreProposal(
            reply=f"Review your {request.city} sample options before saving.",
            assumptions=[],
            sources=[],
            data_mode=self.provider.data_mode,
            recommendations=feasible[:5],
            uncertain_recommendations=uncertain[:5],
            warnings=warnings,
            coverage={
                "area": request.city.lower(),
                "data_mode": self.provider.data_mode,
                "providers": [type(self.provider).__name__],
                "partial": bool(uncertain),
            },
        )
