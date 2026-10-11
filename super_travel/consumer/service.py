"""Owner-scoped consumer application service over the existing transactional store."""

import json
from datetime import date, datetime
from uuid import NAMESPACE_URL, uuid4, uuid5
from zoneinfo import ZoneInfo

from pydantic import TypeAdapter

from super_travel.consumer.coordination import CoordinationService
from super_travel.consumer.models import (
    Briefing,
    CalendarEvent,
    Home,
    ItineraryItem,
    ParticipantCreate,
    Profile,
    Task,
    TaskCreate,
    TripNotebook,
    WardrobeItem,
)
from super_travel.consumer.seed import seed_items
from super_travel.consumer.wardrobe import WardrobeService
from super_travel.control.schemas import RunRequest, Trip
from super_travel.control.store import ControlError


class Notebook(WardrobeService, CoordinationService):
    def __init__(self, store, agents):
        self.store, self.agents = store, agents

    def collection(self, actor, kind, trip_id=None):
        rows = self.store.db.execute(
            "SELECT body FROM objects WHERE actor=? AND kind=? ORDER BY created,id",
            (str(actor), kind),
        ).fetchall()
        values = [json.loads(row["body"]) for row in rows]
        return [
            item
            for item in values
            if trip_id is None or item.get("trip_id") == str(trip_id)
        ]

    def put(self, actor, kind, model):
        body = model.model_dump(mode="json") if hasattr(model, "model_dump") else model
        if self.store.db.execute(
            "SELECT id FROM objects WHERE id=? AND actor=? AND kind=?",
            (body["id"], str(actor), kind),
        ).fetchone():
            self.store.db.execute(
                "UPDATE objects SET body=? WHERE id=? AND actor=? AND kind=?",
                (json.dumps(body), body["id"], str(actor), kind),
            )
        else:
            self.store.insert(actor, kind, body)
        return body

    def owned(self, actor, kind, identifier, trip_id=None):
        body = self.store.get(actor, kind, identifier)
        if trip_id and body.get("trip_id") != str(trip_id):
            raise ControlError(404, "not_found", "Resource not found in this trip")
        return body

    def version(self, body, etag):
        if etag is None:
            raise ControlError(428, "precondition_required", "If-Match is required")
        if etag != f'"{body["version"]}"':
            raise ControlError(
                412, "version_conflict", "This page changed; refresh before editing"
            )

    def initialize(self, actor):
        profiles = self.collection(actor, "user")
        if not profiles:
            profile = Profile(id=actor)
            self.put(actor, "user", profile)
            for item in seed_items(actor):
                self.put(actor, "wardrobe", WardrobeItem(**item))
        return self.store.get(actor, "user", actor)

    def home(self, actor):
        profile = self.initialize(actor)
        tasks = [self.sync_task(actor, t) for t in self.collection(actor, "task")]
        return Home(
            trips=self.collection(actor, "trip"),
            tasks=tasks,
            profile=profile,
            wardrobe_count=len(self.collection(actor, "wardrobe")),
        )

    def new_task(self, actor, trip_id, payload, creator="user"):
        trip = self.owned(actor, "trip", trip_id)
        if (
            payload.due_date
            and trip["end_date"]
            and payload.due_date > date.fromisoformat(trip["end_date"])
        ):
            raise ControlError(
                422,
                "invalid_due_date",
                "Task deadline must be within or before the trip",
            )
        return self.put(
            actor,
            "task",
            Task(
                **payload.model_dump(),
                id=uuid4(),
                trip_id=trip_id,
                created_by=creator,
                created_at=self.store.now(),
                updated_at=self.store.now(),
            ),
        )

    def create_trip(self, actor, payload):
        self.initialize(actor)
        trip = Trip(**payload.model_dump(), id=uuid4(), owner_user_id=actor)
        self.put(actor, "trip", trip)
        tasks = [
            (
                "Compare travel options",
                "plan_book",
                "Compare transport and accommodation. Show research or samples; never book automatically.",
            ),
            (
                "Shape a gentle itinerary",
                "plan_book",
                "Suggest a flexible itinerary based on our interests.",
            ),
            (
                "Prepare my packing list",
                "pack_shop",
                "Suggest essentials and clothing for our trip; do not buy anything.",
            ),
            (
                "Choose outfits for the trip",
                "pack_shop",
                "Open the wardrobe and choose comfortable outfits.",
            ),
            (
                "Find a local experience",
                "explore_magic",
                "Suggest a short activity that fits our time and budget.",
            ),
            (
                "Check documents and entry rules",
                "essentials",
                "Identify information needed; refer to official entry sources.",
            ),
            (
                "Arrange connectivity",
                "essentials",
                "Review connectivity options and emergency preparation.",
            ),
            (
                "Keep receipts and a backup plan",
                "recovery",
                "Prepare a plan for disruptions. Draft only; no outbound claims.",
            ),
        ]
        if (
            payload.traveler_configuration.child_count
            or payload.traveler_configuration.infant_count
        ):
            tasks.append(
                (
                    "Plan breaks for the family",
                    "plan_book",
                    "Allow downtime and age-appropriate walking distances.",
                )
            )
        if payload.dietary:
            tasks.append(
                (
                    "Find meals everyone will enjoy",
                    "explore_magic",
                    f"Research meal options for these preferences: {payload.dietary}. No reservations.",
                )
            )
        for title, agent, instructions in tasks:
            self.new_task(
                actor,
                trip.id,
                TaskCreate(
                    title=title,
                    description=instructions,
                    agent_instructions=instructions,
                    assigned_agent=agent,
                ),
                "wonder",
            )
        for i in range(payload.traveler_configuration.adult_count):
            self.participant(
                actor,
                trip.id,
                ParticipantCreate(label=f"Adult {i + 1}"),
                bootstrap=True,
            )
        for i in range(payload.traveler_configuration.child_count):
            self.participant(
                actor,
                trip.id,
                ParticipantCreate(label=f"Child {i + 1}", kind="child"),
                bootstrap=True,
            )
        for i in range(payload.traveler_configuration.infant_count):
            self.participant(
                actor,
                trip.id,
                ParticipantCreate(label=f"Infant {i + 1}", kind="infant"),
                bootstrap=True,
            )
        return trip

    def sync_task(self, actor, body):
        if (
            body["status"]
            not in (
                "queued",
                "agent_working",
                "ready_for_review",
                "waiting_for_approval",
            )
            or not body["agent_run_id"]
        ):
            return body
        try:
            run = self.owned(actor, "run", body["agent_run_id"])
        except ControlError:
            body.update(status="failed", result=None)
        else:
            status = {
                "queued": "queued",
                "running": "agent_working",
                "succeeded": "ready_for_review",
                "failed": "failed",
                "cancelled": "cancelled",
                "expired": "failed",
            }[run["status"]]
            if status == body["status"]:
                return body
            body.update(status=status, result=run["proposal"])
            body["history"].append(
                {
                    "status": status,
                    "at": self.store.now().isoformat(),
                    "run_id": run["id"],
                }
            )
            if run["error"]:
                body["history"].append(
                    {
                        "status": status,
                        "message": run["error"]["message"],
                        "at": self.store.now().isoformat(),
                    }
                )
        body.update(
            version=body["version"] + 1, updated_at=self.store.now().isoformat()
        )
        return self.put(actor, "task", body)

    def patch_task(self, actor, trip_id, identifier, payload, etag):
        task = self.sync_task(actor, self.owned(actor, "task", identifier, trip_id))
        self.version(task, etag)
        changes = payload.model_dump(mode="json", exclude_unset=True)
        if any(value is None for name, value in changes.items() if name != "due_date"):
            raise ControlError(
                422, "invalid_request", "Task text and assignment cannot be null"
            )
        if task["agent_run_id"] and any(
            name in changes
            for name in ("agent_instructions", "assigned_agent", "description")
        ):
            run = self.owned(actor, "run", task["agent_run_id"])
            self.store.cancel(actor, run["id"], f'"{run["version"]}"')
            task.update(agent_run_id=None, result=None, status="not_started")
        trip = self.owned(actor, "trip", trip_id)
        if (
            changes.get("due_date")
            and trip["end_date"]
            and changes["due_date"] > trip["end_date"]
        ):
            raise ControlError(
                422, "invalid_due_date", "Task due date must be within the trip"
            )
        task.update(
            **changes,
            version=task["version"] + 1,
            updated_at=self.store.now().isoformat(),
        )
        return self.put(actor, "task", Task.model_validate(task))

    def run_task(self, actor, trip_id, identifier, etag, magic=None):
        task = self.sync_task(actor, self.owned(actor, "task", identifier, trip_id))
        self.version(task, etag)
        trip = self.owned(actor, "trip", trip_id)
        if task["status"] in ("queued", "agent_working"):
            raise ControlError(
                409, "run_in_progress", "Cancel or wait for the current run"
            )
        agent = task["assigned_agent"]
        if (agent == "explore_magic" and magic is None) or (
            agent != "explore_magic"
            and (
                not trip["start_date"]
                or not trip["end_date"]
                or trip["destination"] == "Undecided"
            )
        ):
            task.update(status="needs_more_information", version=task["version"] + 1)
            task["history"].append(
                {
                    "status": "needs_more_information",
                    "message": "Add destination/dates, or provide a Magic location and window.",
                    "at": self.store.now().isoformat(),
                }
            )
            return self.put(actor, "task", task)
        values = (
            magic.model_dump(mode="json")
            if agent == "explore_magic"
            else {"instructions": task["agent_instructions"] or task["description"]}
        )
        if agent == "pack_shop":
            values["activities"] = trip["activities"]
        request = TypeAdapter(RunRequest).validate_python(
            {"agent": agent, "trip_id": trip_id, "input": values}
        )
        run = self.agents.create_run(actor, request)
        task.update(
            status="queued",
            agent_run_id=run["id"],
            result=None,
            version=task["version"] + 1,
            updated_at=self.store.now().isoformat(),
        )
        task["history"].append(
            {
                "run_id": run["id"],
                "status": "queued",
                "input_version": task["version"],
                "context_version": trip["context_version"],
                "at": self.store.now().isoformat(),
            }
        )
        return self.put(actor, "task", task)

    def decide_task(self, actor, trip_id, identifier, action, etag):
        task = self.sync_task(actor, self.owned(actor, "task", identifier, trip_id))
        self.version(task, etag)
        if action == "approve":
            if task["status"] != "ready_for_review" or not task["result"]:
                raise ControlError(
                    409,
                    "proposal_not_ready",
                    "Run this task and review its result first",
                )
            run = self.owned(actor, "run", task["agent_run_id"])
            trip = self.owned(actor, "trip", trip_id)
            if run["context_version"] != trip["context_version"]:
                raise ControlError(
                    409, "stale_context", "Trip changed; rerun before applying"
                )
            # Explicit approval applies draft itinerary items, never external actions.
            added = False
            for item in task["result"].get("itinerary_items", []):
                instant = datetime.fromisoformat(item["starts_at"]).astimezone(
                    ZoneInfo(item["timezone"])
                )
                identity = uuid5(NAMESPACE_URL, f"{run['id']}:{item['item_id']}")
                if not any(
                    old["id"] == str(identity)
                    for old in self.collection(actor, "itinerary", trip_id)
                ):
                    added = True
                    self.put(
                        actor,
                        "itinerary",
                        ItineraryItem(
                            id=identity,
                            trip_id=trip_id,
                            title=item["title"],
                            day=instant.date(),
                            local_time=instant.strftime("%H:%M"),
                        ),
                    )
            if added:
                trip.update(
                    version=trip["version"] + 1,
                    context_version=trip["context_version"] + 1,
                )
                self.put(actor, "trip", trip)
            task.update(requires_approval=False, status="ready_for_review")
        elif action == "reject":
            task.update(status="not_started", result=None, agent_run_id=None)
        elif action == "complete":
            if task["status"] in ("queued", "agent_working"):
                run = self.owned(actor, "run", task["agent_run_id"])
                self.store.cancel(actor, run["id"], f'"{run["version"]}"')
            task["status"] = (
                "completed"  # explicitly reported by user, not inferred from a link/approval
            )
        else:
            task["status"] = "not_started"
        task["history"].append(
            {
                "status": task["status"],
                "action": action,
                "at": self.store.now().isoformat(),
                "message": "Draft accepted; no external action executed"
                if action == "approve"
                else "User updated this task",
            }
        )
        task.update(
            version=task["version"] + 1, updated_at=self.store.now().isoformat()
        )
        return self.put(actor, "task", task)

    def calendar(self, actor, trip_id, day):
        self.owned(actor, "trip", trip_id)
        connections = self.collection(actor, "calendar")
        active = (
            connections[0]
            if connections
            else {"enabled": False, "selected_event_ids": []}
        )
        return [
            CalendarEvent(
                id=key,
                title=title,
                day=day,
                local_time=hour,
                event_type=kind,
                selected=active["enabled"] and key in active["selected_event_ids"],
            )
            for key, title, hour, kind in [
                ("museum", "Sample museum visit", "10:00", "museum"),
                ("dinner", "Sample family dinner", "19:00", "dinner"),
                ("personal", "Sample personal appointment", "15:00", "personal"),
            ]
        ]

    def briefing(self, actor, trip_id, day=None):
        trip = self.owned(actor, "trip", trip_id)
        today = self.store.now().astimezone(ZoneInfo(trip["timezone"])).date()
        start = date.fromisoformat(trip["start_date"]) if trip["start_date"] else None
        end = date.fromisoformat(trip["end_date"]) if trip["end_date"] else None
        if day and ((start and day < start) or (end and day > end)):
            raise ControlError(
                422, "invalid_day", "Briefing day must be within the trip"
            )
        day = day or (
            max(start, min(today, end))
            if start and end
            else max(start, today)
            if start
            else today
        )
        events = [
            event for event in self.calendar(actor, trip_id, day) if event.selected
        ]
        for entry in self.collection(actor, "itinerary", trip_id):
            if entry["day"] == day.isoformat():
                events.append(
                    CalendarEvent(
                        id=entry["id"],
                        title=entry["title"],
                        day=day,
                        local_time=entry["local_time"],
                        event_type="personal",
                        selected=True,
                        data_mode="manual",
                        calendar_id="wonder-itinerary",
                    )
                )
        events.sort(key=lambda event: event.local_time)
        packing = self.packing(actor, trip_id)
        ready = {
            item.wardrobe_item_id
            for item in packing.items
            if item.packed and item.availability == "ready"
        }
        outfit = next(
            (
                outfit
                for outfit in packing.liked_outfits
                if day in outfit.suitable_days
                and all(identifier in ready for identifier in outfit.item_ids)
            ),
            None,
        )
        tasks = [
            task
            for task in self.collection(actor, "task", trip_id)
            if task["status"] != "completed"
        ]
        note = "A little room for a good day. "
        note += (
            (
                "You have "
                + ", ".join(f"{event.title} at {event.local_time}" for event in events)
                + ". "
            )
            if events
            else "No selected schedule items yet. "
        )
        note += (
            f"Your {outfit.title} look is packed and ready."
            if outfit
            else "Choose and pack a ready outfit when you like."
        )
        body = Briefing(
            id=uuid5(NAMESPACE_URL, f"{actor}:{trip_id}:{day}"),
            trip_id=trip_id,
            day=day,
            note=note,
            schedule=events,
            outfit=outfit,
            weather="Sample forecast: 18°C, a cool morning; light rain possible. Not live weather.",
            reminders=[t["title"] for t in tasks[:3]],
            disruptions=[],
        )
        self.put(actor, "briefing", body)
        return body

    def notebook(self, actor, trip_id):
        trip = self.owned(actor, "trip", trip_id)
        return TripNotebook(
            trip=trip,
            tasks=[
                self.sync_task(actor, item)
                for item in self.collection(actor, "task", trip_id)
            ],
            packing=self.packing(actor, trip_id),
            participants=self.collection(actor, "participant", trip_id),
            itinerary=self.collection(actor, "itinerary", trip_id),
            expenses=self.collection(actor, "expense", trip_id),
            segments=self.collection(actor, "segment", trip_id),
        )
