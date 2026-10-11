"""Agent registry. The orchestrator builds its delegate tool from this.

To plug in a new agent: implement the Agent protocol (core/agent.py), add it to REGISTRY,
and remove its entry from PLANNED.
"""

from super_travel.agents.essentials.agent import EssentialsAgent
from super_travel.agents.recovery.agent import RecoveryAgent

REGISTRY = {agent.name: agent for agent in [EssentialsAgent(), RecoveryAgent()]}

# Agents defined in docs/architecture.md but not built yet. The orchestrator knows they exist
# and tells the user instead of improvising their work.
PLANNED = {
    "planning": "Plan & Book: destination discovery, dates, budget, flights, accommodation, travel documents, visas, itinerary.",
    "packing": "Pack & Shop: packing lists, weather-based suggestions, luggage restrictions, essentials shopping and last-minute purchases.",
    "explore": "Explore & Experience: attractions, local transport, dining, events, experiences, reservations, Magic discovery.",
}

# App events are routed deterministically, never by the model.
EVENT_ROUTES = {
    "flight_status_update": "recovery",
    "baggage_delayed": "recovery",
    "receipt_uploaded": "recovery",
    "trip_ended": "recovery",
}
