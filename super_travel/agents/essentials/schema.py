"""Structured output of the Travel Essentials agent (submitted via the submit_essentials tool)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Topic = Literal[
    "payments_currency", "connectivity", "health", "insurance",
    "safety", "customs_etiquette", "language", "emergency",
]
Priority = Literal["must", "should", "nice"]


class Source(BaseModel):
    title: str
    url: str


class BriefingItem(BaseModel):
    title: str = Field(description="Short headline, e.g. 'Carry some cash for small cafés'")
    detail: str = Field(description="1-3 sentences, specific to this trip")
    priority: Priority
    traveler_ids: list[str] = Field(description="Travelers this applies to; empty list means everyone")
    destination_ids: list[str] = Field(description="Destinations this applies to; empty list means all")


class BriefingSection(BaseModel):
    topic: Topic
    items: list[BriefingItem]


class EmergencyContact(BaseModel):
    destination_id: str
    label: str = Field(description="e.g. 'General emergency', 'US Embassy Lisbon'")
    phone: str = Field(description="Number as dialed locally; empty string if not verified")
    notes: str = Field(description="Address, hours or 'verify before travel'; may be empty")


class Phrase(BaseModel):
    destination_id: str
    english: str
    local: str
    pronunciation: str


class ChecklistItem(BaseModel):
    title: str
    due: str = Field(description="YYYY-MM-DD, before departure")
    traveler_id: str = Field(description="Traveler id, or empty string for everyone")
    priority: Priority


class HandoffOut(BaseModel):
    to_agent: Literal["planning", "packing", "explore", "recovery"]
    task: str = Field(description="Self-contained instruction for the other agent")


class EssentialsResult(BaseModel):
    reply: str = Field(description="Markdown answer to the user's request, written for the traveler")
    sections: list[BriefingSection] = Field(
        description="Full briefing sections. Empty when the request is a narrow question."
    )
    emergency_contacts: list[EmergencyContact]
    phrases: list[Phrase]
    checklist_items: list[ChecklistItem] = Field(
        description="New prep tasks only; do not repeat tasks already in the trip checklist"
    )
    handoffs: list[HandoffOut]
    sources: list[Source] = Field(description="Web pages relied on for time-sensitive facts")
