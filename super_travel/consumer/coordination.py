"""Deterministic group dates, trip segments and exact expense splits."""

from datetime import date
from uuid import uuid4

from super_travel.consumer.models import Expense, Participant, Segment
from super_travel.control.store import ControlError


class CoordinationService:
    def segment(self, actor, trip_id, payload):
        trip = self.owned(actor, "trip", trip_id)
        if (
            trip["start_date"]
            and payload.start_date < date.fromisoformat(trip["start_date"])
        ) or (
            trip["end_date"] and payload.end_date > date.fromisoformat(trip["end_date"])
        ):
            raise ControlError(
                422, "invalid_dates", "Segment dates must be within the trip"
            )
        trip.update(
            context_version=trip["context_version"] + 1, version=trip["version"] + 1
        )
        self.put(actor, "trip", trip)
        return self.put(
            actor,
            "segment",
            Segment(**payload.model_dump(), id=uuid4(), trip_id=trip_id),
        )

    def participant(self, actor, trip_id, payload, bootstrap=False):
        trip = self.owned(actor, "trip", trip_id)
        for value in (payload.arrive, payload.depart):
            if value and (
                (trip["start_date"] and value < date.fromisoformat(trip["start_date"]))
                or (trip["end_date"] and value > date.fromisoformat(trip["end_date"]))
            ):
                raise ControlError(
                    422, "invalid_dates", "Participant dates must fall within the trip"
                )
        if not bootstrap:
            count=sum(person['kind']==payload.kind for person in self.collection(actor,'participant',trip_id))
            if count >= (10 if payload.kind=='infant' else 30):
                raise ControlError(422,'group_limit','Traveler count limit reached for this category')
        person = self.put(
            actor,
            "participant",
            Participant(**payload.model_dump(), id=uuid4(), trip_id=trip_id),
        )
        if not bootstrap:
            people = self.collection(actor, "participant", trip_id)
            trip["traveler_configuration"] = {
                kind + "_count": sum(person["kind"] == kind for person in people)
                for kind in ("adult", "child", "infant")
            }
            trip.update(
                version=trip["version"] + 1, context_version=trip["context_version"] + 1
            )
            self.put(actor, "trip", trip)
        return person

    def expense(self, actor, trip_id, payload):
        trip = self.owned(actor, "trip", trip_id)
        if payload.money.currency != trip["currency"]:
            raise ControlError(
                422,
                "currency_mismatch",
                "Use the trip currency; no implicit conversion",
            )
        people = {item["id"] for item in self.collection(actor, "participant", trip_id)}
        if (
            str(payload.paid_by) not in people
            or any(str(person) not in people for person in payload.split_between)
            or len(set(payload.split_between)) != len(payload.split_between)
        ):
            raise ControlError(
                422, "invalid_participants", "Use unique participants from this trip"
            )
        identifiers = sorted(str(person) for person in payload.split_between)
        base, remainder = divmod(payload.money.amount_minor, len(identifiers))
        shares = {
            identifier: base + (i < remainder)
            for i, identifier in enumerate(identifiers)
        }
        return self.put(
            actor,
            "expense",
            Expense(
                **payload.model_dump(), id=uuid4(), trip_id=trip_id, shares_minor=shares
            ),
        )
