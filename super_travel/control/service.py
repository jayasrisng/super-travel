"""Bounded worker and actor-scoped application operations."""

import json
from datetime import timedelta
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from super_travel.agents.explore import ExploreAgent, ProviderUnavailable
from super_travel.agents.proposals import PackingAgent, PlanningAgent
from super_travel.control.schemas import AgentRun, RunRequest
from super_travel.control.store import ControlError


class Service:
    def __init__(self, store, mode="fixture", agents=None):
        self.store = store
        self.agents = agents or {
            "plan_book": PlanningAgent(mode),
            "pack_shop": PackingAgent(mode),
            "explore_magic": ExploreAgent(mode),
        }

    def create_run(self, actor, request):
        if request.agent == "explore_magic" and not ExploreAgent.supports(
            request.input.location
        ):
            raise ControlError(
                422,
                "unsupported_area",
                "Magic currently covers the Barcelona demo rectangle only",
            )
        now = self.store.now()
        trip = (
            self.store.get(actor, "trip", request.trip_id) if request.trip_id else None
        )
        active = self.store.db.execute(
            "SELECT body FROM objects WHERE actor=? AND kind='run'", (str(actor),)
        ).fetchall()
        if (
            sum(
                json.loads(row["body"])["status"] in ("queued", "running")
                for row in active
            )
            >= 10
        ):
            raise ControlError(429, "queue_full", "At most ten active runs per actor")
        all_runs = self.store.db.execute(
            "SELECT body FROM objects WHERE kind='run'"
        ).fetchall()
        if (
            sum(
                json.loads(row["body"])["status"] in ("queued", "running")
                for row in all_runs
            )
            >= 100
        ):
            raise ControlError(429, "queue_full", "Global queue capacity reached")
        values = request.input.model_dump(mode="json")
        if trip and request.agent != "explore_magic":
            # Only fill omitted fields; explicit null remains explicit null.
            defaults = {
                field: trip[field]
                for field in (
                    "destination",
                    "start_date",
                    "end_date",
                    "timezone",
                    "interests",
                )
            }
            defaults.update(trip["traveler_configuration"])
            for field, value in defaults.items():
                if field not in request.input.model_fields_set:
                    values[field] = value
        try:
            resolved = TypeAdapter(RunRequest).validate_python(
                {"agent": request.agent, "trip_id": request.trip_id, "input": values}
            )
        except ValidationError as exc:
            raise ControlError(
                422,
                "invalid_constraints",
                "Trip overrides produce invalid dates or constraints",
            ) from exc
        if request.agent != "explore_magic" and any(
            getattr(resolved.input, field) is None
            for field in ("destination", "start_date", "end_date")
        ):
            raise ControlError(
                422,
                "missing_constraints",
                "Destination and both dates are required, directly or from a trip",
            )
        body = {
            "id": str(uuid4()),
            "actor_user_id": str(actor),
            "trip_id": str(request.trip_id) if trip else None,
            "agent": request.agent,
            "status": "queued",
            "context_version": trip["context_version"] if trip else None,
            "version": 1,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=24)).isoformat(),
            "proposal": None,
            "error": None,
        }
        self.store.insert(actor, "run", body, resolved.model_dump(mode="json"))
        return body

    def work_once(self):
        claimed = self.store.claim()
        if not claimed:
            return False
        body, payload, lease = claimed
        try:
            request = TypeAdapter(RunRequest).validate_python(payload)
            proposal = self.agents[request.agent].propose(
                request.input, self.store.now()
            )
            validated = AgentRun.model_validate(
                {
                    **body,
                    "status": "succeeded",
                    "proposal": proposal.model_dump(mode="json"),
                }
            )
            self.store.finish(
                body["id"], lease, proposal=validated.proposal.model_dump(mode="json")
            )
        except ProviderUnavailable:
            self.store.finish(
                body["id"],
                lease,
                error={
                    "code": "provider_unavailable",
                    "message": "Live discovery and route providers are not configured",
                    "retryable": False,
                },
            )
        except ValueError:
            self.store.finish(
                body["id"],
                lease,
                error={
                    "code": "invalid_constraints",
                    "message": "The input or proposal did not satisfy supported constraints",
                    "retryable": False,
                },
            )
        except Exception:  # noqa: BLE001 - SDK boundary; redact all provider errors
            # Never put SDK/provider responses or request contents into public errors/logs.
            self.store.finish(
                body["id"],
                lease,
                error={
                    "code": "agent_failed",
                    "message": "Agent could not produce a valid proposal",
                    "retryable": True,
                },
            )
        return True
