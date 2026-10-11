"""Agent 4: Travel Essentials. Prepare travelers before they go."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from anthropic import beta_tool

from super_travel.core import llm
from super_travel.core.agent import AgentResult, Handoff
from super_travel.core.specialist import run_specialist, user_message
from super_travel.core.trip_context import TripContext
from super_travel.agents.essentials import tools
from super_travel.agents.essentials.schema import EssentialsResult

SYSTEM_PROMPT = (Path(__file__).parent / "prompt.md").read_text()

# Built once at import so the tool list is byte-identical across requests (prompt caching).
_CLIENT_TOOLS = [
    beta_tool(tools.get_country_info),
    beta_tool(tools.get_exchange_rate),
    beta_tool(tools.find_esim_plans),
]


class EssentialsAgent:
    name = "essentials"
    description = (
        "Travel Essentials: payments and currency, eSIM and connectivity, health, travel "
        "insurance, safety and advisories, local customs and etiquette, key phrases, and "
        "emergency contacts. Use for 'what do I need to know before I go' and pre-departure prep. "
        "Not for visas or passports (planning) or buying items (packing)."
    )

    def run(self, task: str, trip: TripContext, today: date | None = None) -> AgentResult:
        result = run_specialist(
            system_prompt=SYSTEM_PROMPT,
            tools=[llm.WEB_SEARCH_TOOL, *_CLIENT_TOOLS],
            message=user_message(task, trip, today or date.today()),
            result_model=EssentialsResult,
            submit_name="submit_essentials",
            effort="medium",
        )
        added = trip.add_tasks(result.checklist_items, owner_agent=self.name)
        data = result.model_dump()
        data["checklist_added"] = [t.model_dump(mode="json") for t in added]
        return AgentResult(
            reply=result.reply,
            handoffs=[Handoff(to_agent=h.to_agent, task=h.task) for h in result.handoffs],
            data=data,
        )
