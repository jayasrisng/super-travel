"""Explicit permitted-provider interfaces; credentials do not imply API permission."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal, Protocol

from super_travel.agents.explore import Candidate, ProviderUnavailable
from super_travel.consumer.models import CalendarEvent
from super_travel.control.schemas import MagicInput


class EventProvider(Protocol):
    name: str

    def discover(self, request: MagicInput, now: datetime) -> list[Candidate]: ...


class CalendarProvider(Protocol):
    def events(
        self, connection_id: str, day: date, selected_ids: list[str]
    ) -> list[CalendarEvent]: ...
    def disconnect(self, connection_id: str) -> None: ...


@dataclass(frozen=True)
class WeatherReading:
    temperature_c: int
    summary: str
    data_mode: Literal["fixture", "live"]
    observed_at: datetime


class WeatherProvider(Protocol):
    def forecast(
        self, latitude: float, longitude: float, day: date
    ) -> WeatherReading: ...


@dataclass(frozen=True)
class UnconfiguredEventProvider:
    """Fail explicitly until a legitimate provider adapter is installed and tested."""

    name: str

    def discover(self, request: MagicInput, now: datetime) -> list[Candidate]:
        raise ProviderUnavailable(f"{self.name} has no permitted adapter configured")


EVENT_PROVIDERS = tuple(
    UnconfiguredEventProvider(name)
    for name in ("Luma", "Partiful", "Eventbrite", "Meetup")
)
