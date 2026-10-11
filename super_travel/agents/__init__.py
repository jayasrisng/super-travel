"""Agent registry. The orchestrator builds its delegate tool from this."""

from super_travel.agents.essentials.agent import EssentialsAgent

REGISTRY = {agent.name: agent for agent in [EssentialsAgent()]}
