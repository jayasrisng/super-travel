"""Agent registry. The orchestrator builds its delegate tool from this."""

from super_travel.agents.essentials.agent import EssentialsAgent
from super_travel.agents.recovery.agent import RecoveryAgent

REGISTRY = {agent.name: agent for agent in [EssentialsAgent(), RecoveryAgent()]}
