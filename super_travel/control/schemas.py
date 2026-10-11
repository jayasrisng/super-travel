"""Strict shared wire schemas for the three proposal-only agents."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Annotated, Literal, TypeVar
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)

AgentKey = Literal["plan_book", "pack_shop", "explore_magic", "essentials", "recovery"]
Mode = Literal["fixture", "llm"]
Status = Literal["queued", "running", "succeeded", "failed", "cancelled", "expired"]
Minor = Annotated[int, Field(ge=0, le=9_007_199_254_740_991, strict=True)]
Text = Annotated[str, Field(min_length=1, max_length=2000)]


class Model(BaseModel):
    @field_validator("*")
    @classmethod
    def utc_instants(cls, value):
        if isinstance(value, datetime) and value.tzinfo is not None:
            return value.astimezone(UTC)
        return value

    model_config = ConfigDict(extra="forbid")


class Money(Model):
    amount_minor: Minor
    currency: str = Field(pattern=r"^[A-Z]{3}$")


class Location(Model):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class Source(Model):
    provider: str
    source_url: HttpUrl
    observed_at: AwareDatetime
    expires_at: AwareDatetime | None = None
    data_mode: Literal["fixture", "manual", "live"]
    availability: Literal["verified", "unverified", "unavailable", "not_applicable"] = (
        "unverified"
    )
    cost_status: Literal["verified", "estimated", "unknown"] = "unknown"

    @field_validator("source_url")
    @classmethod
    def https_only(cls, value):
        if value.scheme != "https":
            raise ValueError("Sources must use HTTPS")
        return value


class TravelInput(Model):
    destination: str | None = Field(default=None, min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    timezone: str = "Europe/Madrid"
    adult_count: int = Field(default=1, ge=1, le=30, strict=True)
    child_count: int = Field(default=0, ge=0, le=30, strict=True)
    infant_count: int = Field(default=0, ge=0, le=10, strict=True)
    interests: list[Text] = Field(default_factory=list, max_length=20)
    instructions: str = Field(default="", max_length=2000)
    dietary: str = Field(default="", max_length=500)
    accessibility: str = Field(default="", max_length=500)
    travel_style: str = Field(default="unhurried", max_length=100)
    child_ages: list[int] = Field(default_factory=list, max_length=30)

    @field_validator("timezone")
    @classmethod
    def timezone_exists(cls, value):
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Use an IANA timezone") from exc
        return value

    @model_validator(mode="after")
    def valid_dates(self):
        if self.start_date and self.end_date:
            if self.start_date > self.end_date:
                raise ValueError("start_date must precede end_date")
            if (self.end_date - self.start_date).days > 60:
                raise ValueError("A proposal may span at most 61 civil days")
        return self


class PlanInput(TravelInput):
    budget: Money | None = None


class PackInput(TravelInput):
    activities: list[Text] = Field(default_factory=list, max_length=20)
    baggage_mode: Literal["carry_on", "checked", "personal_item"] = "carry_on"


class Commitment(Model):
    starts_at: AwareDatetime
    location: Location


class MagicInput(Model):
    location: Location
    available_minutes: int = Field(ge=15, le=480, strict=True)
    interests: list[Text] = Field(default_factory=list, max_length=20)
    budget: Money | None = None
    next_commitment: Commitment | None = None
    travel_mode: Literal["walk", "transit"] = "walk"
    buffer_minutes: int = Field(default=15, ge=0, le=60, strict=True)
    timezone: str = "Europe/Madrid"
    city: str = Field(default="Barcelona", min_length=1, max_length=120)
    allow_unknown_feasibility: bool = False

    @model_validator(mode="after")
    def valid_timezone(self):
        TravelInput(timezone=self.timezone)
        return self


class RunBase(Model):
    trip_id: UUID | None = None


class PlanRequest(RunBase):
    agent: Literal["plan_book"]
    input: PlanInput


class PackRequest(RunBase):
    agent: Literal["pack_shop"]
    input: PackInput


class ExploreRequest(RunBase):
    agent: Literal["explore_magic"]
    input: MagicInput


class HelperInput(TravelInput):
    pass


class EssentialsRequest(RunBase):
    agent: Literal["essentials"]
    input: HelperInput


class RecoveryRequest(RunBase):
    agent: Literal["recovery"]
    input: HelperInput


RunRequest = Annotated[
    PlanRequest | PackRequest | ExploreRequest | EssentialsRequest | RecoveryRequest,
    Field(discriminator="agent"),
]


class MagicRequest(MagicInput):
    trip_id: UUID | None = None


class TaskProposal(Model):
    item_id: Text
    title: Text
    system: AgentKey


class ItineraryProposal(Model):
    item_id: Text
    title: Text
    starts_at: AwareDatetime
    ends_at: AwareDatetime
    timezone: str
    kind: Literal["activity", "transport", "stay", "commitment"] = "activity"

    @model_validator(mode="after")
    def valid_duration(self):
        if self.starts_at >= self.ends_at:
            raise ValueError("Itinerary duration must be positive")
        try:
            ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError("Use an IANA timezone") from exc
        return self


class ProposalBase(Model):
    reply: Text
    assumptions: list[Text]
    sources: list[Source]
    data_mode: Literal["fixture", "live"]


class PlanProposal(ProposalBase):
    itinerary_items: list[ItineraryProposal] = Field(max_length=100)
    checklist_tasks: list[TaskProposal] = Field(max_length=100)
    budget_estimates: list[Money] = Field(max_length=30)


class PackingItem(Model):
    item_id: Text
    title: Text
    quantity: int = Field(ge=1, le=1000, strict=True)
    category: Text
    purchase_status: Literal["not_needed", "missing"] = "not_needed"


class PackingListProposal(Model):
    item_id: Text
    title: Text
    items: list[PackingItem] = Field(max_length=100)


class PackProposal(ProposalBase):
    packing_lists: list[PackingListProposal] = Field(max_length=30)
    checklist_tasks: list[TaskProposal] = Field(max_length=100)


class Action(Model):
    type: Literal["save"] = "save"


class Recommendation(Model):
    id: UUID
    title: Text
    category: Text
    location: Location
    rank: int = Field(ge=1)
    reason: Text
    duration_minutes: int = Field(ge=1)
    outbound_minutes: int | None = Field(default=None, ge=0)
    onward_minutes: int | None = Field(default=None, ge=0)
    buffer_minutes: int = Field(ge=0)
    slack_minutes: int | None
    cost: Money | None
    cost_status: Literal["verified", "estimated", "unknown"]
    feasibility: Literal["feasible", "unknown"]
    evaluated_at: AwareDatetime
    valid_until: AwareDatetime
    provenance: list[Source] = Field(min_length=1)
    assumptions: list[Text]
    allowed_actions: list[Action] = Field(default_factory=lambda: [Action()])


class Coverage(Model):
    area: str = "barcelona"
    data_mode: Literal["fixture", "live"]
    providers: list[str]
    partial: bool


class ExploreProposal(ProposalBase):
    recommendations: list[Recommendation] = Field(max_length=5)
    uncertain_recommendations: list[Recommendation] = Field(max_length=5)
    warnings: list[Text]
    coverage: Coverage


Proposal = PlanProposal | PackProposal | ExploreProposal


class RunError(Model):
    code: str
    message: str
    retryable: bool = False


class AgentRun(Model):
    id: UUID
    actor_user_id: UUID
    trip_id: UUID | None
    agent: AgentKey
    status: Status
    context_version: int | None
    version: int
    created_at: AwareDatetime
    expires_at: AwareDatetime
    proposal: Proposal | None = None
    error: RunError | None = None

    @model_validator(mode="after")
    def proposal_matches_agent(self):
        expected = {
            "plan_book": PlanProposal,
            "pack_shop": PackProposal,
            "explore_magic": ExploreProposal,
            "essentials": PlanProposal,
            "recovery": PlanProposal,
        }[self.agent]
        if self.proposal is not None and not isinstance(self.proposal, expected):
            raise ValueError("Proposal type must match the run agent")
        if self.status == "succeeded" and self.proposal is None:
            raise ValueError("Succeeded runs require a proposal")
        if self.status != "succeeded" and self.proposal is not None:
            raise ValueError("Only succeeded runs expose a proposal")
        return self


class Meta(Model):
    request_id: str
    next_cursor: str | None = None


T = TypeVar("T")


class Envelope[T](Model):
    data: T
    meta: Meta


class TravelerConfiguration(Model):
    adult_count: int = Field(default=1, ge=1, le=30, strict=True)
    child_count: int = Field(default=0, ge=0, le=30, strict=True)
    infant_count: int = Field(default=0, ge=0, le=10, strict=True)


class TripCreate(Model):
    title: str = Field(min_length=1, max_length=120)
    destination: str = Field(default="Undecided", min_length=1, max_length=120)
    start_date: date | None = None
    end_date: date | None = None
    date_certainty: Literal["confirmed", "tentative", "flexible"] = "confirmed"
    dietary: str = Field(default="", max_length=500)
    accessibility: str = Field(default="", max_length=500)
    travel_style: str = Field(default="unhurried", max_length=100)
    activities: list[Text] = Field(default_factory=list, max_length=20)
    child_ages: list[int] = Field(default_factory=list, max_length=30)
    budget: Money | None = None
    existing_bookings: str = Field(default="", max_length=1000)
    status: Literal["planned", "ongoing", "completed", "archived"] = "planned"
    timezone: str = "Europe/Madrid"
    currency: Literal["EUR", "USD", "JPY"] = "EUR"
    traveler_configuration: TravelerConfiguration = Field(
        default_factory=TravelerConfiguration
    )
    interests: list[Text] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_trip(self):
        if self.date_certainty == "confirmed" and (
            not self.start_date or not self.end_date
        ):
            raise ValueError("Confirmed dates require both start and end")
        if any(age < 0 or age > 17 for age in self.child_ages):
            raise ValueError("Child ages must be 0 to 17; no child names requested")
        if self.budget and self.budget.currency != self.currency:
            raise ValueError("Budget must use the trip currency")
        if len(self.child_ages) > self.traveler_configuration.child_count:
            raise ValueError("Child ages must correspond to the child traveler count")
        TravelInput(
            destination=self.destination,
            start_date=self.start_date,
            end_date=self.end_date,
            timezone=self.timezone,
        )
        return self


class Trip(TripCreate):
    id: UUID
    owner_user_id: UUID
    context_version: int = 1
    version: int = 1


class SaveRequest(Model):
    run_id: UUID
    recommendation_id: UUID


class SavedExperience(Model):
    id: UUID
    run_id: UUID
    recommendation_id: UUID
    title: str
    trip_id: UUID | None
    data_mode: Literal["fixture", "live"]
    version: int = 1


class AgentInfo(Model):
    agent: AgentKey
    prototype_name: str
    title: str
    mode: Mode
    ready: bool
    limitation: str


class ErrorDetail(Model):
    field: str
    reason: str


class APIError(Model):
    code: str
    message: str
    details: list[ErrorDetail]
    retryable: bool


class ErrorEnvelope(Model):
    error: APIError
    meta: Meta
