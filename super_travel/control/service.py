"""Bounded worker and actor-scoped application operations."""

import json
from datetime import date, timedelta
from uuid import uuid4

from pydantic import TypeAdapter, ValidationError

from super_travel.agents.essentials.proposal import EssentialsProposalAgent
from super_travel.agents.explore import ExploreAgent, ProviderUnavailable
from super_travel.agents.proposals import PackingAgent, PlanningAgent
from super_travel.agents.recovery.proposal import RecoveryProposalAgent
from super_travel.agents.voice import VoiceQuoteAgent
from super_travel.consumer.agents import HelperAdapter
from super_travel.control.schemas import (
    AgentRun,
    InsurancePolicy,
    Intake,
    Location,
    Message,
    RunRequest,
    Trip,
)
from super_travel.control.store import ControlError
from super_travel.core.geo import destination

# Deterministic message triage: (topic, words that all-of-any-group must match).
INSURANCE_WORDS = ("insurance", "insured", "policy", "coverage", "cover")
BORDER_WORDS = (
    "border",
    "officer",
    "immigration",
    "passport control",
    "customs",
    "entry",
    "airport",
)
DISRUPTION_WORDS = ("delay", "delayed", "cancel", "missed", "bag", "luggage", "lost")


def triage(text):
    lower = text.lower()
    if any(w in lower for w in INSURANCE_WORDS):
        at_border = any(w in lower for w in BORDER_WORDS)
        return {
            "topic": "insurance_proof",
            "urgency": "urgent" if at_border else "normal",
            "suggested_action": "voice_quotes",
            "reason": "Traveler needs proof of travel insurance"
            + (" at the border" if at_border else ""),
        }
    if any(w in lower for w in DISRUPTION_WORDS):
        return {
            "topic": "disruption",
            "urgency": "urgent",
            "suggested_action": "manage_recover",
            "reason": "Traveler reports a disruption",
        }
    return {
        "topic": "general",
        "urgency": "normal",
        "suggested_action": "reply",
        "reason": "General question",
    }


# Intake interests (free text) -> Magic candidate categories.
MAGIC_CATEGORIES = {
    "food": ("food", "eat", "restaurant", "tapas", "market", "cafe", "coffee"),
    "nature": ("park", "beach", "garden", "nature", "outdoor", "hike"),
    "culture": (
        "museum",
        "aquarium",
        "art",
        "history",
        "architecture",
        "culture",
        "gothic",
    ),
}


class Service:
    def __init__(self, store, mode="fixture", agents=None):
        self.store = store
        self.agents = agents or {
            "plan_book": PlanningAgent(mode),
            "pack_shop": PackingAgent(mode),
            "explore_magic": ExploreAgent(mode),
            "travel_essentials": EssentialsProposalAgent(mode),
            "manage_recover": RecoveryProposalAgent(mode),
            "voice_quotes": VoiceQuoteAgent(mode),
            "essentials": HelperAdapter("essentials", mode),
            "recovery": HelperAdapter("recovery", mode),
        }

    def create_run(self, actor, request):
        if request.agent == "explore_magic" and not ExploreAgent.supports(
            request.input.location
        ):
            raise ControlError(
                422,
                "unsupported_area",
                "Invalid geographic origin",
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
                    "dietary",
                    "accessibility",
                    "travel_style",
                    "child_ages",
                )
            }
            if request.agent == "plan_book" and trip.get("budget") is not None:
                defaults["budget"] = trip["budget"]
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
        disruption_only = (
            request.agent == "manage_recover" and resolved.input.disruption is not None
        )
        if (
            request.agent != "explore_magic"
            and not disruption_only
            and any(
                getattr(resolved.input, field) is None
                for field in ("destination", "start_date", "end_date")
            )
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

    def create_intake(self, actor, intake):
        """Create the trip, record the intake and queue every agent that can run for it.

        Runs inside the caller's store transaction, so all of it commits or none does.
        """
        now = self.store.now()
        place = destination(intake.destination)
        timezone = place["timezone"] if place else "Europe/Madrid"
        trip = Trip(
            id=uuid4(),
            owner_user_id=actor,
            title=f"{intake.client_name.split()[0]}'s {intake.destination.split(',')[0]} trip",
            destination=intake.destination,
            start_date=intake.start_date,
            end_date=intake.end_date,
            timezone=timezone,
            currency=place["currency"]
            if place and place["currency"] in ("EUR", "USD", "JPY")
            else "EUR",
            traveler_configuration=intake.traveler_configuration,
            interests=intake.interests,
        ).model_dump(mode="json")
        self.store.insert(actor, "trip", trip)

        trip_id = trip["id"]
        runs = []
        requests = {
            "plan_book": {},
            "pack_shop": {},
            "travel_essentials": {"home_currency": intake.home_currency},
            "manage_recover": {},
        }
        for agent, values in requests.items():
            request = TypeAdapter(RunRequest).validate_python(
                {"agent": agent, "trip_id": trip_id, "input": values}
            )
            runs.append(
                {"agent": agent, "run_id": self.create_run(actor, request)["id"]}
            )

        center = place and Location(latitude=place["lat"], longitude=place["lon"])
        # Preserve the advisor demo's declared Barcelona coverage; the consumer
        # fixture adapter separately accepts entered origins in other cities.
        if (
            center
            and 41.32 <= center.latitude <= 41.47
            and 2.05 <= center.longitude <= 2.23
        ):
            text = " ".join(intake.interests).lower()
            categories = [
                c
                for c, words in MAGIC_CATEGORIES.items()
                if any(w in text for w in words)
            ]
            request = TypeAdapter(RunRequest).validate_python(
                {
                    "agent": "explore_magic",
                    "trip_id": trip_id,
                    "input": {
                        "location": center.model_dump(),
                        "available_minutes": 120,
                        "interests": categories,
                    },
                }
            )
            runs.append(
                {
                    "agent": "explore_magic",
                    "run_id": self.create_run(actor, request)["id"],
                }
            )
        else:
            runs.append(
                {
                    "agent": "explore_magic",
                    "run_id": None,
                    "skipped_reason": "Magic covers the Barcelona demo area only",
                }
            )

        body = Intake(
            **intake.model_dump(),
            id=uuid4(),
            trip_id=trip_id,
            created_at=now,
            runs=runs,
        ).model_dump(mode="json")
        self.store.insert(actor, "intake", body)
        return body

    def intake_for_trip(self, actor, trip_id):
        intakes, _ = self.store.list(actor, "intake", limit=1000)
        return next((i for i in intakes if i["trip_id"] == str(trip_id)), None)

    def create_message(self, actor, trip_id, payload):
        self.store.get(actor, "trip", trip_id)  # 404 unless the actor owns the trip
        if payload.attachment:
            policy = self.store.get(actor, "policy", payload.attachment.policy_id)
            if policy["trip_id"] != str(trip_id):
                raise ControlError(
                    422, "invalid_attachment", "Attachment belongs to another trip"
                )
        body = Message(
            **payload.model_dump(),
            id=uuid4(),
            trip_id=trip_id,
            created_at=self.store.now(),
            triage=triage(payload.text) if payload.sender == "traveler" else None,
        ).model_dump(mode="json")
        self.store.insert(actor, "message", body)
        return body

    def create_policy(self, actor, trip_id, payload):
        """Advisor approval of a voice-agent quote. Issues a SIMULATED policy record."""
        trip = self.store.get(actor, "trip", trip_id)
        run = self.store.get(actor, "run", payload.run_id)
        if (
            run["agent"] != "voice_quotes"
            or run["trip_id"] != str(trip_id)
            or run["status"] != "succeeded"
        ):
            raise ControlError(
                409,
                "run_not_ready",
                "Approve a quote from this trip's finished voice-agent run",
            )
        quote = next(
            (
                c["quote"]
                for c in run["proposal"]["calls"]
                if c["quote"] and c["quote"]["quote_id"] == payload.quote_id
            ),
            None,
        )
        if quote is None:
            raise ControlError(404, "not_found", "Quote not found")
        if not quote["meets_requirements"]:
            raise ControlError(
                422,
                "quote_not_eligible",
                "This quote does not meet the coverage requirements",
            )
        intake = self.intake_for_trip(actor, trip_id)
        configuration = trip["traveler_configuration"]
        insured = [intake["client_name"]] if intake else ["Lead traveler"]
        insured += ["Adult traveler"] * (configuration["adult_count"] - 1)
        ages = (intake or {}).get("child_ages", [])
        insured += [
            f"Child, age {ages[i]}" if i < len(ages) else "Child"
            for i in range(configuration["child_count"])
        ]
        insured += ["Infant"] * configuration["infant_count"]
        now = self.store.now()
        start = max(now.date(), date.fromisoformat(trip["start_date"]))
        body = InsurancePolicy(
            id=uuid4(),
            trip_id=trip_id,
            run_id=payload.run_id,
            quote_id=quote["quote_id"],
            policy_number=f"SIM-{uuid4().hex[:8].upper()}",
            insurer=quote["insurer"],
            insured=insured,
            coverage_start=start,
            coverage_end=max(start, date.fromisoformat(trip["end_date"])),
            premium=quote["premium"],
            medical_cover=quote["medical_cover"],
            deductible=quote["deductible"],
            repatriation=quote["repatriation"],
            schengen_compliant=quote["schengen_compliant"],
            issued_at=now,
        ).model_dump(mode="json")
        self.store.insert(actor, "policy", body)
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
