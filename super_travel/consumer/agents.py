"""Reuse existing helpers on isolated snapshots; fixture mode makes no model calls."""

from super_travel.agents.essentials.agent import EssentialsAgent
from super_travel.agents.recovery.agent import RecoveryAgent
from super_travel.control.schemas import PlanProposal
from super_travel.core.trip_context import TripContext


class HelperAdapter:
    def __init__(self, name, mode):
        self.name, self.mode = name, mode

    def propose(self, request, now):
        tasks = (
            [
                "Review connectivity options",
                "Check official entry and emergency information",
            ]
            if self.name == "essentials"
            else [
                "Keep booking receipts and provider contacts",
                "Review disruption options before taking action",
            ]
        )
        if self.mode == "fixture":
            return PlanProposal(
                reply=f"Sample {self.name} preparation note for {request.destination}. No live advice or external action.",
                assumptions=[
                    "Sample preparation guidance; verify current requirements with official sources."
                ],
                sources=[],
                data_mode="fixture",
                itinerary_items=[],
                budget_estimates=[],
                checklist_tasks=[
                    {"item_id": f"{self.name}-{i}", "title": title, "system": self.name}
                    for i, title in enumerate(tasks)
                ],
            )
        country = {"Tokyo": "JP", "Barcelona": "ES", "Lisbon": "PT"}.get(
            request.destination, ""
        )
        snapshot = TripContext(
            trip_id="isolated-proposal",
            name=request.destination or "Trip",
            status="planned",
            home={
                "city": "",
                "country": "",
                "timezone": request.timezone,
                "currency": "EUR",
            },
            travelers=[],
            destinations=[
                {
                    "id": "destination",
                    "city": request.destination,
                    "country": country,
                    "arrive": request.start_date,
                    "depart": request.end_date,
                    "currency": "EUR",
                }
            ],
        )
        agent = EssentialsAgent() if self.name == "essentials" else RecoveryAgent()
        result = agent.run(
            request.instructions or "Suggest preparation tasks",
            snapshot,
            now.date(),
            timeout_seconds=20,
        )
        # Mutations by legacy tools remain in the discarded snapshot; only validated proposals escape.
        titles = [item["title"] for item in result.data.get("checklist_added", [])]
        return PlanProposal(
            reply=result.reply[:2000],
            assumptions=[
                "Model research; no booking, claim, message or purchase has been executed."
            ],
            sources=[],
            data_mode="live",
            itinerary_items=[],
            budget_estimates=[],
            checklist_tasks=[
                {"item_id": f"{self.name}-{i}", "title": title, "system": self.name}
                for i, title in enumerate(titles[:30])
            ],
        )
