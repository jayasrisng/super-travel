"""Consumer contracts. Strict UUID ownership, civil dates and integer money."""

from datetime import date
from typing import Literal
from uuid import UUID

from pydantic import AwareDatetime, Field, model_validator

from super_travel.control.schemas import (
    MagicInput,
    Model,
    Money,
    Proposal,
    Text,
    Trip,
)

ConsumerAgentKey = Literal[
    "plan_book", "pack_shop", "explore_magic", "essentials", "recovery"
]

TaskStatus = Literal[
    "not_started",
    "queued",
    "agent_working",
    "needs_more_information",
    "ready_for_review",
    "waiting_for_approval",
    "completed",
    "failed",
    "cancelled",
]


class TaskCreate(Model):
    title: Text
    description: str = Field(default="", max_length=2000)
    agent_instructions: str = Field(default="", max_length=2000)
    assigned_agent: ConsumerAgentKey = "plan_book"
    priority: Literal["must", "should", "could"] = "should"
    due_date: date | None = None
    requires_approval: bool = True


class TaskPatch(Model):
    title: Text | None = None
    description: str | None = Field(default=None, max_length=2000)
    agent_instructions: str | None = Field(default=None, max_length=2000)
    assigned_agent: ConsumerAgentKey | None = None
    priority: Literal["must", "should", "could"] | None = None
    due_date: date | None = None
    requires_approval: bool | None = None


class Task(TaskCreate):
    id: UUID
    trip_id: UUID
    status: TaskStatus = "not_started"
    created_by: Literal["wonder", "user"]
    agent_run_id: UUID | None = None
    result: Proposal | None = None
    history: list[dict] = Field(default_factory=list)
    created_at: AwareDatetime
    updated_at: AwareDatetime
    version: int = 1


class TaskDecision(Model):
    action: Literal["complete", "reopen", "approve", "reject"]


class Preferences(Model):
    dietary: str = Field(default="", max_length=500)
    accessibility: str = Field(default="", max_length=500)
    travel_style: str = Field(default="unhurried", max_length=100)
    interests: list[Text] = Field(default_factory=list, max_length=20)
    notification_preference: bool = False


class Profile(Preferences):
    id: UUID
    label: str = "Local notebook"
    version: int = 1


class WardrobeCreate(Model):
    name: str = Field(min_length=1, max_length=120)
    category: Literal["tops", "bottoms", "shoes", "accessories", "essentials"]
    color: str = Field(default="cream", max_length=30)
    image: str = Field(default="", max_length=120)
    style: str = Field(default="everyday", max_length=100)
    season: list[str] = Field(
        default_factory=lambda: ["spring", "autumn"], max_length=4
    )
    warmth: int = Field(default=2, ge=0, le=5, strict=True)
    occasions: list[str] = Field(
        default_factory=lambda: ["casual", "walking"], max_length=10
    )
    material: str | None = Field(default=None, max_length=100)
    weight_grams: int | None = Field(default=None, ge=0, le=10000, strict=True)
    ownership_status: Literal["owned", "needed"] = "owned"
    favorite: bool = False
    availability: Literal["ready", "worn", "dirty", "unavailable"] = "ready"


class WardrobeItem(WardrobeCreate):
    id: UUID
    version: int = 1
    image_mode: Literal["illustration", "uploaded"] = "illustration"


class OutfitRequest(Model):
    trip_id: UUID | None = None
    occasion: Literal["walking", "dinner", "business", "outdoors"] = "walking"
    temperature_c: int = Field(default=18, ge=-30, le=50, strict=True)
    weather_mode: Literal["manual", "demo"] = "demo"


class Outfit(Model):
    id: UUID
    trip_id: UUID | None = None
    item_ids: list[UUID]
    title: str
    occasion: str
    suitable_days: list[date]
    explanation: str
    score: int
    weather_mode: Literal["manual", "demo"]
    temperature_c: int
    renderer: Literal["lookbook"] = "lookbook"
    version: int = 1


class VoteRequest(Model):
    decision: Literal["like", "dislike"]


class OutfitVote(Model):
    id: UUID
    outfit_id: UUID
    trip_id: UUID | None
    decision: Literal["like", "dislike"]
    created_at: AwareDatetime
    version: int = 1
    previous_decision: Literal["like", "dislike"] | None = None


class PackingItem(Model):
    id: UUID
    trip_id: UUID
    wardrobe_item_id: UUID
    name: str
    image: str
    category: str
    packed: bool = False
    manual: bool = False
    outfit_ids: list[UUID]
    relevant_days: list[date]
    availability: Literal["ready", "worn", "dirty", "unavailable"] = "ready"
    version: int = 1


class PackingAdd(Model):
    wardrobe_item_id: UUID


class PackingPatch(Model):
    packed: bool | None = None
    availability: Literal["ready", "worn", "dirty", "unavailable"] | None = None


class PackingSummary(Model):
    items: list[PackingItem]
    unique_items: int
    liked_outfits: list[Outfit]
    needed_items: list[str]
    substitutions: list[str]


class CalendarSelection(Model):
    enabled: bool = True
    selected_event_ids: list[str] = Field(
        default_factory=lambda: ["museum", "dinner"], max_length=20
    )


class CalendarEvent(Model):
    id: str
    title: str
    day: date
    local_time: str
    calendar_id: str = "demo-travel"
    event_type: Literal["museum", "dinner", "personal"]
    selected: bool
    data_mode: Literal["fixture", "manual"] = "fixture"


class CalendarConnection(CalendarSelection):
    id: UUID
    provider: Literal["demo_google_calendar"] = "demo_google_calendar"
    state: Literal["connected", "disconnected"]
    version: int = 1


class Briefing(Model):
    id: UUID
    trip_id: UUID
    day: date
    note: str
    schedule: list[CalendarEvent]
    outfit: Outfit | None
    weather: str
    weather_mode: Literal["fixture"] = "fixture"
    reminders: list[str]
    disruptions: list[str]
    delivery: Literal["in_app_only"] = "in_app_only"
    version: int = 1


class ParticipantCreate(Model):
    label: str = Field(min_length=1, max_length=120)
    kind: Literal["adult", "child", "infant"] = "adult"
    arrive: date | None = None
    depart: date | None = None

    @model_validator(mode="after")
    def valid_dates(self):
        if self.arrive and self.depart and self.arrive > self.depart:
            raise ValueError("Arrival must precede departure")
        return self


class Participant(ParticipantCreate):
    id: UUID
    trip_id: UUID
    version: int = 1


class ItineraryCreate(Model):
    title: Text
    day: date
    local_time: str = Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    duration_minutes: int = Field(default=60, ge=1, le=1440, strict=True)
    category: str = Field(default="activity", max_length=100)
    participant_ids: list[UUID] = Field(default_factory=list, max_length=70)


class ItineraryItem(ItineraryCreate):
    id: UUID
    trip_id: UUID
    version: int = 1


class ExpenseCreate(Model):
    title: Text
    money: Money
    paid_by: UUID
    split_between: list[UUID] = Field(min_length=1, max_length=70)


class Expense(ExpenseCreate):
    id: UUID
    trip_id: UUID
    shares_minor: dict[str, int]
    version: int = 1


class SegmentCreate(Model):
    title: Text
    destination: Text
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def ordered(self):
        if self.start_date > self.end_date:
            raise ValueError("Segment dates must be ordered")
        return self


class Segment(SegmentCreate):
    id: UUID
    trip_id: UUID
    version: int = 1


class SharedItinerary(Model):
    id: UUID
    title: Text
    day: date
    local_time: str
    duration_minutes: int
    category: str


class TripNotebook(Model):
    trip: Trip
    tasks: list[Task]
    packing: PackingSummary
    participants: list[Participant]
    itinerary: list[ItineraryItem]
    expenses: list[Expense]
    segments: list[Segment]


class Home(Model):
    trips: list[Trip]
    tasks: list[Task]
    profile: Profile
    wardrobe_count: int


class RunTaskInput(Model):
    magic: MagicInput | None = None


class PhotoInput(Model):
    content_base64: str = Field(max_length=2_800_000)
    mime: Literal["image/jpeg", "image/png", "image/webp"]


class Share(Model):
    id: UUID
    trip_id: UUID
    expires_at: AwareDatetime
    revoked: bool = False
    version: int = 1


class ShareCreated(Share):
    token: str


class SharedNotebook(Model):
    title: str
    destination: str
    start_date: date | None
    end_date: date | None
    itinerary: list[SharedItinerary]
    permission: Literal["read_only"] = "read_only"


class SessionInfo(Model):
    mode: Literal["local_demo"] = "local_demo"
    user_id: UUID
