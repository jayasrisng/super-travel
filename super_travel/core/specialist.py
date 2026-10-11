"""Shared loop for specialist agents: tool runner + a submit tool that carries the structured result."""

from __future__ import annotations

from datetime import date
from typing import Any, TypeVar

from anthropic import beta_tool
from pydantic import BaseModel, ValidationError

from super_travel.core import llm
from super_travel.core.trip_context import TripContext

ResultT = TypeVar("ResultT", bound=BaseModel)


class SpecialistError(RuntimeError):
    pass


def user_message(task: str, trip: TripContext, today: date) -> str:
    return (
        f"Today is {today.isoformat()}.\n\n"
        f"<trip>\n{trip.to_prompt_json()}\n</trip>\n\n"
        f"<request>\n{task}\n</request>"
    )


def run_specialist(
    *,
    system_prompt: str,
    tools: list[Any],
    message: str,
    result_model: type[ResultT],
    submit_name: str,
    effort: str,
    max_iterations: int = 15,
) -> ResultT:
    """Run the agent loop until the model calls `submit_name` with a valid `result_model`."""
    submitted: list[ResultT] = []

    def submit(**kwargs: Any) -> str:
        try:
            submitted.append(result_model.model_validate(kwargs))
        except ValidationError as exc:
            raise ValueError(f"Result did not match the schema, fix and resubmit: {exc}") from exc
        return "Received."

    submit_tool = beta_tool(
        submit,
        name=submit_name,
        description="Submit your final result. Call exactly once, when you are done.",
        input_schema=llm.inline_refs(result_model.model_json_schema()),
    )
    runner = llm.client().beta.messages.tool_runner(
        model=llm.MODEL,
        max_tokens=16000,
        system=[{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}],
        tools=[*tools, submit_tool],
        messages=[{"role": "user", "content": message}],
        output_config={"effort": effort},
        max_iterations=max_iterations,
        **llm.FALLBACK_KWARGS,
    )
    final = runner.until_done()

    if final.stop_reason == "refusal":
        raise SpecialistError(f"Request declined: {final.stop_details}")
    if not submitted:
        raise SpecialistError(f"Agent finished without submitting a result (stop_reason={final.stop_reason}).")
    return submitted[-1]
