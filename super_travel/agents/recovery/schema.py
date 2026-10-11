"""Structured output of the Manage & Recover agent (submitted via the submit_recovery tool)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Priority = Literal["must", "should", "nice"]


class ProposedAction(BaseModel):
    kind: Literal["send_claim", "request_refund", "contact_airline", "contact_insurer",
                  "request_settle_up", "cancel_reservation", "other"]
    summary: str = Field(description="One line shown on the confirm card")
    recipient: str = Field(description="Who it goes to, e.g. 'Vueling customer relations'")
    incident_id: str = Field(description="Related incident id, or empty string")
    draft: str = Field(description="Full message or claim text ready to send, or empty string")
    amount: float = Field(description="Amount claimed or requested; 0 if not applicable")
    currency: str = Field(description="ISO code, or empty string")


class ChecklistItem(BaseModel):
    title: str
    due: str = Field(description="YYYY-MM-DD")
    traveler_id: str = Field(description="Traveler id, or empty string for everyone")
    priority: Priority


class HandoffOut(BaseModel):
    to_agent: Literal["planning", "packing", "explore", "essentials"]
    task: str = Field(description="Self-contained instruction for the other agent")


class RecoveryResult(BaseModel):
    reply: str = Field(description="Markdown for the travelers: what happened, what they're owed, what to do now")
    pending_actions: list[ProposedAction] = Field(
        description="Irreversible steps (sending, cancelling, requesting money) for the user to confirm"
    )
    checklist_items: list[ChecklistItem] = Field(
        description="Follow-ups and post-trip tasks, e.g. claim deadlines; skip ones already in the checklist"
    )
    handoffs: list[HandoffOut]
