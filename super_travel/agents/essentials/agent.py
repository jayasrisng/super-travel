"""Agent 4: Travel Essentials. Prepare travelers before they go."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from anthropic import beta_tool
from pydantic import ValidationError

from super_travel.core import llm
from super_travel.core.agent import AgentResult, Handoff
from super_travel.core.trip_context import Task, TripContext
from super_travel.agents.essentials import tools
from super_travel.agents.essentials.schema import EssentialsResult

SYSTEM_PROMPT = (Path(__file__).parent / "prompt.md").read_text()
MAX_ITERATIONS = 15
EFFORT = "medium"

# Built once at import so the tool list is byte-identical across requests (prompt caching).
_CLIENT_TOOLS = [
    beta_tool(tools.get_country_info),
    beta_tool(tools.get_exchange_rate),
    beta_tool(tools.find_esim_plans),
]
_SUBMIT_SCHEMA = llm.inline_refs(EssentialsResult.model_json_schema())
_SUBMIT_DESCRIPTION = "Submit your final result. Call exactly once, when you are done."


class EssentialsAgentError(RuntimeError):
    pass


class EssentialsAgent:
    name = "essentials"
    description = (
        "Travel Essentials: payments and currency, eSIM and connectivity, health, travel "
        "insurance, safety and advisories, local customs and etiquette, key phrases, and "
        "emergency contacts. Use for 'what do I need to know before I go' and pre-departure prep. "
        "Not for visas or passports (planning) or buying items (packing)."
    )

    def run(self, task: str, trip: TripContext, today: date | None = None) -> AgentResult:
        result = self.research(task, trip, today or date.today())
        added = trip.add_checklist_items([
            Task(
                id=f"{trip.next_checklist_id()}_{i}",
                title=item.title,
                owner_agent=self.name,
                traveler_id=item.traveler_id or None,
                due=date.fromisoformat(item.due) if item.due else None,
                priority=item.priority,
            )
            for i, item in enumerate(result.checklist_items)
        ])
        data = result.model_dump()
        data["checklist_added"] = [t.model_dump(mode="json") for t in added]
        return AgentResult(
            reply=result.reply,
            handoffs=[Handoff(to_agent=h.to_agent, task=h.task) for h in result.handoffs],
            data=data,
        )

    def research(self, task: str, trip: TripContext, today: date) -> EssentialsResult:
        submitted: list[EssentialsResult] = []

        def submit_essentials(**kwargs: Any) -> str:
            try:
                submitted.append(EssentialsResult.model_validate(kwargs))
            except ValidationError as exc:
                raise ValueError(f"Result did not match the schema, fix and resubmit: {exc}") from exc
            return "Received."

        submit_tool = beta_tool(
            submit_essentials,
            name="submit_essentials",
            description=_SUBMIT_DESCRIPTION,
            input_schema=_SUBMIT_SCHEMA,
        )

        runner = llm.client().beta.messages.tool_runner(
            model=llm.MODEL,
            max_tokens=16000,
            system=[{"type": "text", "text": SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}}],
            tools=[llm.WEB_SEARCH_TOOL, *_CLIENT_TOOLS, submit_tool],
            messages=[{"role": "user", "content": self._user_message(task, trip, today)}],
            output_config={"effort": EFFORT},
            max_iterations=MAX_ITERATIONS,
            **llm.FALLBACK_KWARGS,
        )
        final = runner.until_done()

        if final.stop_reason == "refusal":
            raise EssentialsAgentError(f"Request declined: {final.stop_details}")
        if not submitted:
            raise EssentialsAgentError(
                f"Agent finished without submitting a result (stop_reason={final.stop_reason})."
            )
        return submitted[-1]

    @staticmethod
    def _user_message(task: str, trip: TripContext, today: date) -> str:
        return (
            f"Today is {today.isoformat()}.\n\n"
            f"<trip>\n{trip.to_prompt_json()}\n</trip>\n\n"
            f"<request>\n{task}\n</request>"
        )
