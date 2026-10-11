"""Shared five-specialist registry and deterministic event routing."""

from super_travel.agents.essentials.agent import EssentialsAgent
from super_travel.agents.explore import ExploreAgent
from super_travel.agents.proposals import PackingAgent, PlanningAgent
from super_travel.agents.recovery.agent import RecoveryAgent

REGISTRY = {agent.name: agent for agent in [
    EssentialsAgent(), RecoveryAgent(), PlanningAgent(), PackingAgent(), ExploreAgent(),
]}
# Keep future entries separate from registered specialists. Fixture availability
# does not imply live provider availability; control /v1/agents carries those limits.
PLANNED: dict[str, str] = {}
EVENT_ROUTES = {
    "flight_status_update": "recovery",
    "baggage_delayed": "recovery",
    "receipt_uploaded": "recovery",
    "trip_ended": "recovery",
}
