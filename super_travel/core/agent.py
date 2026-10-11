"""The contract every specialist agent implements. See docs/architecture.md section 2."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from super_travel.core.trip_context import TripContext


@dataclass
class PendingAction:
    """An irreversible action (booking, purchase, sending) waiting for the user's yes."""

    kind: str
    summary: str
    payload: dict[str, Any]


@dataclass
class Handoff:
    to_agent: str  # "planning" | "packing" | "explore" | "essentials" | "recovery"
    task: str


@dataclass
class AgentResult:
    reply: str  # markdown for the orchestrator to relay or merge
    pending_actions: list[PendingAction] = field(default_factory=list)
    handoffs: list[Handoff] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)  # structured payload for UI cards


class Agent(Protocol):
    name: str
    description: str

    def run(self, task: str, trip: TripContext) -> AgentResult: ...
