"""Agent 5: Manage & Recover. Handle what doesn't go to plan, then close out the trip."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from anthropic import beta_tool

from super_travel.core import llm
from super_travel.core.agent import AgentResult, Handoff, PendingAction
from super_travel.core.specialist import run_specialist, user_message
from super_travel.core.trip_context import TripContext
from super_travel.agents.recovery.schema import RecoveryResult
from super_travel.agents.recovery.tools import RecoveryTools

SYSTEM_PROMPT = (Path(__file__).parent / "prompt.md").read_text()
WEB_SEARCH = {**llm.WEB_SEARCH_TOOL, "max_uses": 4}


class RecoveryAgent:
    name = "recovery"
    description = (
        "Manage & Recover: flight delays and cancellations, missed connections, lost or delayed "
        "baggage, compensation and refund claims, emergency replanning decisions, expense tracking "
        "and settle-up, home preparation, and post-trip tasks."
    )

    def run(self, task: str, trip: TripContext, today: date | None = None) -> AgentResult:
        trip_tools = RecoveryTools(trip)
        result = run_specialist(
            system_prompt=SYSTEM_PROMPT,
            tools=[WEB_SEARCH, *(beta_tool(fn) for fn in trip_tools.as_list())],
            message=user_message(task, trip, today or date.today()),
            result_model=RecoveryResult,
            submit_name="submit_recovery",
            effort="high",
        )
        added = trip.add_tasks(result.checklist_items, owner_agent=self.name)
        data = result.model_dump()
        data["checklist_added"] = [t.model_dump(mode="json") for t in added]
        return AgentResult(
            reply=result.reply,
            pending_actions=[
                PendingAction(kind=a.kind, summary=a.summary, payload=a.model_dump(exclude={"kind", "summary"}))
                for a in result.pending_actions
            ],
            handoffs=[Handoff(to_agent=h.to_agent, task=h.task) for h in result.handoffs],
            data=data,
        )

    def handle_event(self, event: dict[str, Any], trip: TripContext, today: date | None = None) -> AgentResult:
        """App events (flight feed, receipt upload, trip end). Applies the event to trip state, then runs."""
        if event["type"] == "flight_status_update":
            for seg in trip.segments:
                if seg["id"] == event["segment_id"]:
                    seg["live_status"] = event["data"]
        payload = {k: v for k, v in event.items() if k != "expected"}
        return self.run(f"EVENT: {json.dumps(payload, ensure_ascii=False)}", trip, today)
