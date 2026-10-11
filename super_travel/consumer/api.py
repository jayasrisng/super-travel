"""Consumer endpoints share the control API's identity, transactions and replay semantics."""

# ruff: noqa: B008
import base64
import hashlib
import hmac
import json
from datetime import date, timedelta
from uuid import UUID, uuid4

from fastapi import Depends, Header, Request, Response

from super_travel.consumer import auth
from super_travel.consumer.models import (
    Briefing,
    CalendarConnection,
    CalendarEvent,
    CalendarSelection,
    Expense,
    ExpenseCreate,
    Home,
    ItineraryCreate,
    ItineraryItem,
    Outfit,
    OutfitRequest,
    OutfitVote,
    PackingAdd,
    PackingItem,
    PackingPatch,
    PackingSummary,
    Participant,
    ParticipantCreate,
    PhotoInput,
    Preferences,
    Profile,
    RunTaskInput,
    Segment,
    SegmentCreate,
    SessionInfo,
    Share,
    ShareCreated,
    SharedItinerary,
    SharedNotebook,
    Task,
    TaskCreate,
    TaskDecision,
    TaskPatch,
    TripNotebook,
    VoteRequest,
    WardrobeCreate,
    WardrobeItem,
)
from super_travel.consumer.providers import EVENT_PROVIDERS
from super_travel.control.schemas import Envelope, Trip, TripCreate
from super_travel.control.store import ControlError


def register(app, actor, key, envelope, etag):
    def domain(request):
        return request.app.state.notebook

    def mutate(request, response, identity, replay_key, route, payload, operation):
        service = domain(request)
        result = service.store.create(
            identity,
            route,
            replay_key,
            payload,
            lambda: envelope(request, operation(service)),
        )
        if isinstance(result["data"], dict) and "version" in result["data"]:
            etag(response, result["data"])
        return result

    def read(request, operation):
        service = domain(request)
        result = service.store.transaction(lambda: operation(service))
        if hasattr(result, "model_dump"):
            result = result.model_dump(mode="json")
        elif isinstance(result, list):
            result = [
                value.model_dump(mode="json") if hasattr(value, "model_dump") else value
                for value in result
            ]
        return envelope(request, result)

    @app.post("/v1/demo/session", response_model=Envelope[SessionInfo])
    def session(request: Request, response: Response):
        if not request.app.state.demo_auth:
            raise ControlError(404, "not_found", "Demo authentication is disabled")
        auth.local_request(request)
        secret = request.app.state.demo_secret
        try:
            identity = auth.verify(request, secret)
        except ControlError:
            cookie = auth.issue(secret)
            response.set_cookie(
                "wonder_demo",
                cookie,
                httponly=True,
                samesite="strict",
                max_age=604800,
                path="/v1",
            )
            identity = UUID(cookie.split(".")[0])
        domain(request).store.transaction(lambda: domain(request).initialize(identity))
        return envelope(request, SessionInfo(user_id=identity).model_dump(mode="json"))

    @app.delete("/v1/demo/session", status_code=204)
    def logout(request: Request, response: Response):
        auth.local_request(request)
        response.delete_cookie("wonder_demo", path="/v1")
        response.status_code = 204
        return response

    @app.get("/v1/consumer/home", response_model=Envelope[Home])
    def home(request: Request, identity=Depends(actor)):
        return read(request, lambda service: service.home(identity))

    @app.put("/v1/consumer/preferences", response_model=Envelope[Profile])
    def preferences(
        payload: Preferences,
        request: Request,
        response: Response,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)

        def update():
            profile = service.initialize(identity)
            service.version(profile, if_match)
            return service.put(
                identity,
                "user",
                Profile(
                    **{
                        **profile,
                        **payload.model_dump(
                            exclude={"fashion"}
                            if "fashion" not in payload.model_fields_set
                            else set()
                        ),
                        "version": profile["version"] + 1,
                    }
                ),
            )

        body = service.store.transaction(update)
        etag(response, body)
        return envelope(request, body)

    @app.post("/v1/consumer/trips", status_code=201, response_model=Envelope[Trip])
    def create_trip(
        payload: TripCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            "consumer/trips",
            payload.model_dump(mode="json"),
            lambda service: service.create_trip(identity, payload).model_dump(
                mode="json"
            ),
        )

    @app.put("/v1/consumer/trips/{trip_id}", response_model=Envelope[Trip])
    def update_trip(
        trip_id: UUID,
        payload: TripCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)

        def update():
            old = service.owned(identity, "trip", trip_id)
            service.version(old, if_match)
            for segment in service.collection(identity, "segment", trip_id):
                if (
                    payload.start_date
                    and date.fromisoformat(segment["start_date"]) < payload.start_date
                ) or (
                    payload.end_date
                    and date.fromisoformat(segment["end_date"]) > payload.end_date
                ):
                    raise ControlError(
                        409,
                        "segment_dates",
                        "Existing segments fall outside these dates",
                    )
            for participant in service.collection(identity, "participant", trip_id):
                if (
                    payload.start_date
                    and participant["arrive"]
                    and date.fromisoformat(participant["arrive"]) < payload.start_date
                    or payload.end_date
                    and participant["depart"]
                    and date.fromisoformat(participant["depart"]) > payload.end_date
                ):
                    raise ControlError(
                        409,
                        "participant_dates",
                        "Update partial participant dates before narrowing the trip",
                    )
            counts = payload.traveler_configuration.model_dump()
            for kind in ("adult", "child", "infant"):
                old_count = old["traveler_configuration"][kind + "_count"]
                if counts[kind + "_count"] < old_count:
                    raise ControlError(
                        409,
                        "participant_removal",
                        "Reducing traveler counts needs participant removal; this adapter currently supports additions only",
                    )
                for index in range(old_count, counts[kind + "_count"]):
                    service.participant(
                        identity,
                        trip_id,
                        ParticipantCreate(
                            label=f"{kind.title()} {index + 1}", kind=kind
                        ),
                        bootstrap=True,
                    )
            trip = Trip(
                **{
                    **old,
                    **payload.model_dump(),
                    "version": old["version"] + 1,
                    "context_version": old["context_version"] + 1,
                }
            )
            return service.put(identity, "trip", trip)

        body = service.store.transaction(update)
        etag(response, body)
        return envelope(request, body)

    @app.get("/v1/consumer/trips/{trip_id}", response_model=Envelope[TripNotebook])
    def notebook(trip_id: UUID, request: Request, identity=Depends(actor)):
        return read(request, lambda service: service.notebook(identity, trip_id))

    @app.post(
        "/v1/consumer/trips/{trip_id}/tasks",
        status_code=201,
        response_model=Envelope[Task],
    )
    def create_task(
        trip_id: UUID,
        payload: TaskCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"trips/{trip_id}/tasks",
            payload.model_dump(mode="json"),
            lambda service: service.new_task(identity, trip_id, payload),
        )

    @app.patch(
        "/v1/consumer/trips/{trip_id}/tasks/{task_id}", response_model=Envelope[Task]
    )
    def patch_task(
        trip_id: UUID,
        task_id: UUID,
        payload: TaskPatch,
        request: Request,
        response: Response,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)
        body = service.store.transaction(
            lambda: service.patch_task(identity, trip_id, task_id, payload, if_match)
        )
        etag(response, body)
        return envelope(request, body)

    @app.post(
        "/v1/consumer/trips/{trip_id}/tasks/{task_id}/run",
        response_model=Envelope[Task],
    )
    def run_task(
        trip_id: UUID,
        task_id: UUID,
        payload: RunTaskInput,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
        if_match: str | None = Header(default=None),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"tasks/{task_id}/run",
            {"input": payload.model_dump(mode="json"), "etag": if_match},
            lambda service: service.run_task(
                identity, trip_id, task_id, if_match, payload.magic
            ),
        )

    @app.post(
        "/v1/consumer/trips/{trip_id}/tasks/{task_id}/decision",
        response_model=Envelope[Task],
    )
    def decision(
        trip_id: UUID,
        task_id: UUID,
        payload: TaskDecision,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
        if_match: str | None = Header(default=None),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"tasks/{task_id}/decision",
            {"action": payload.action, "etag": if_match},
            lambda service: service.decide_task(
                identity, trip_id, task_id, payload.action, if_match
            ),
        )

    @app.delete("/v1/consumer/trips/{trip_id}/tasks/{task_id}", status_code=204)
    def delete_task(
        trip_id: UUID,
        task_id: UUID,
        request: Request,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)

        def remove():
            task = service.owned(identity, "task", task_id, trip_id)
            service.version(task, if_match)
            if task["agent_run_id"]:
                run = service.owned(identity, "run", task["agent_run_id"])
                service.store.cancel(identity, run["id"], f'"{run["version"]}"')
            service.store.db.execute(
                "DELETE FROM objects WHERE id=? AND actor=?",
                (str(task_id), str(identity)),
            )

        service.store.transaction(remove)
        return Response(status_code=204)

    @app.get("/v1/consumer/wardrobe", response_model=Envelope[list[WardrobeItem]])
    def wardrobe(request: Request, identity=Depends(actor)):
        return read(request, lambda service: service.wardrobe(identity))

    @app.post(
        "/v1/consumer/wardrobe", status_code=201, response_model=Envelope[WardrobeItem]
    )
    def clothing(
        payload: WardrobeCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            "wardrobe",
            payload.model_dump(mode="json"),
            lambda service: service.add_clothing(identity, payload),
        )

    @app.put("/v1/consumer/wardrobe/{item_id}", response_model=Envelope[WardrobeItem])
    def edit_clothing(
        item_id: UUID,
        payload: WardrobeCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)
        body = service.store.transaction(
            lambda: service.update_clothing(identity, item_id, payload, if_match)
        )
        etag(response, body)
        return envelope(request, body)

    @app.delete("/v1/consumer/wardrobe/{item_id}", status_code=204)
    def remove_clothing(
        item_id: UUID,
        request: Request,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)

        def remove():
            item = service.owned(identity, "wardrobe", item_id)
            service.version(item, if_match)
            service.store.db.execute(
                "DELETE FROM objects WHERE id=? AND actor=?",
                (str(item_id), str(identity)),
            )
            if item["image_mode"] == "uploaded":
                service.store.db.execute(
                    "DELETE FROM objects WHERE id=? AND actor=? AND kind='media'",
                    (item["image"].split("/")[-1], str(identity)),
                )

        service.store.transaction(remove)
        return Response(status_code=204)

    @app.post(
        "/v1/consumer/wardrobe/{item_id}/photo", response_model=Envelope[WardrobeItem]
    )
    def photo(
        item_id: UUID,
        payload: PhotoInput,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
        if_match: str | None = Header(default=None),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"wardrobe/{item_id}/photo",
            {
                "digest": hashlib.sha256(payload.content_base64.encode()).hexdigest(),
                "etag": if_match,
                "mime": payload.mime,
            },
            lambda service: service.photo(
                identity, item_id, payload.content_base64, payload.mime, if_match
            ),
        )

    @app.get("/v1/consumer/media/{media_id}")
    def media(media_id: UUID, request: Request, identity=Depends(actor)):
        service = domain(request)
        body = service.store.transaction(
            lambda: service.owned(identity, "media", media_id)
        )
        return Response(
            content=base64.b64decode(body["content"]),
            media_type="image/jpeg",
            headers={
                "Cache-Control": "private, no-store",
                "X-Content-Type-Options": "nosniff",
            },
        )

    @app.post("/v1/consumer/outfits/generate", response_model=Envelope[list[Outfit]])
    def generate(
        payload: OutfitRequest,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            "outfits/generate",
            payload.model_dump(mode="json"),
            lambda service: [
                item.model_dump(mode="json")
                for item in service.outfits(identity, payload)
            ],
        )

    @app.post(
        "/v1/consumer/outfits/{outfit_id}/vote", response_model=Envelope[OutfitVote]
    )
    def vote(
        outfit_id: UUID,
        payload: VoteRequest,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"outfits/{outfit_id}/vote",
            payload.model_dump(mode="json"),
            lambda service: service.vote(identity, outfit_id, payload.decision),
        )

    @app.delete("/v1/consumer/outfits/{outfit_id}/vote", status_code=204)
    def undo(outfit_id: UUID, request: Request, identity=Depends(actor)):
        service = domain(request)
        service.store.transaction(lambda: service.undo_vote(identity, outfit_id))
        return Response(status_code=204)

    @app.get("/v1/consumer/outfits/votes", response_model=Envelope[list[OutfitVote]])
    def votes(request: Request, identity=Depends(actor)):
        return read(request, lambda service: service.collection(identity, "vote"))

    @app.get("/v1/consumer/outfits", response_model=Envelope[list[Outfit]])
    def outfits(request: Request, trip_id: UUID | None = None, identity=Depends(actor)):
        return read(
            request, lambda service: service.collection(identity, "outfit", trip_id)
        )

    @app.post(
        "/v1/consumer/trips/{trip_id}/packing", response_model=Envelope[PackingSummary]
    )
    def build_packing(
        trip_id: UUID,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"trips/{trip_id}/packing",
            {},
            lambda service: service.packing(identity, trip_id, True).model_dump(
                mode="json"
            ),
        )

    @app.patch(
        "/v1/consumer/trips/{trip_id}/packing/{item_id}",
        response_model=Envelope[PackingItem],
    )
    def packing_state(
        trip_id: UUID,
        item_id: UUID,
        payload: PackingPatch,
        request: Request,
        response: Response,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)

        def update():
            item = service.owned(identity, "packing", item_id, trip_id)
            service.version(item, if_match)
            changes = payload.model_dump(exclude_unset=True)
            if any(value is None for value in changes.values()):
                raise ControlError(
                    422, "invalid_request", "Packing fields cannot be null"
                )
            item.update(**changes, version=item["version"] + 1)
            return service.put(identity, "packing", PackingItem(**item))

        body = service.store.transaction(update)
        etag(response, body)
        return envelope(request, body)

    @app.post(
        "/v1/consumer/trips/{trip_id}/packing/items",
        response_model=Envelope[PackingItem],
    )
    def packing_add(
        trip_id: UUID,
        payload: PackingAdd,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"trips/{trip_id}/packing/items",
            payload.model_dump(mode="json"),
            lambda service: service.add_packing(
                identity, trip_id, payload.wardrobe_item_id
            ),
        )

    @app.post(
        "/v1/consumer/trips/{trip_id}/segments",
        response_model=Envelope[Segment],
        status_code=201,
    )
    def segment(
        trip_id: UUID,
        payload: SegmentCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"trips/{trip_id}/segments",
            payload.model_dump(mode="json"),
            lambda service: service.segment(identity, trip_id, payload),
        )

    @app.put("/v1/consumer/calendar", response_model=Envelope[CalendarConnection])
    def calendar(
        payload: CalendarSelection,
        request: Request,
        response: Response,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)

        def update():
            values = service.collection(identity, "calendar")
            if values:
                service.version(values[0], if_match)
            body = CalendarConnection(
                **payload.model_dump(),
                id=values[0]["id"] if values else uuid4(),
                state="connected" if payload.enabled else "disconnected",
                version=values[0]["version"] + 1 if values else 1,
            )
            return service.put(identity, "calendar", body)

        body = service.store.transaction(update)
        etag(response, body)
        return envelope(request, body)

    @app.get("/v1/consumer/calendar", response_model=Envelope[list[CalendarConnection]])
    def calendar_connection(request: Request, identity=Depends(actor)):
        return read(request, lambda service: service.collection(identity, "calendar"))

    @app.get(
        "/v1/consumer/trips/{trip_id}/calendar",
        response_model=Envelope[list[CalendarEvent]],
    )
    def calendar_events(
        trip_id: UUID,
        request: Request,
        day: date | None = None,
        identity=Depends(actor),
    ):
        def events(service):
            trip = service.owned(identity, "trip", trip_id)
            return service.calendar(
                identity,
                trip_id,
                day
                or (
                    date.fromisoformat(trip["start_date"])
                    if trip["start_date"]
                    else service.store.now().date()
                ),
            )

        return read(request, events)

    @app.get("/v1/consumer/trips/{trip_id}/briefing", response_model=Envelope[Briefing])
    def briefing(
        trip_id: UUID,
        request: Request,
        day: date | None = None,
        identity=Depends(actor),
    ):
        return read(request, lambda service: service.briefing(identity, trip_id, day))

    @app.post(
        "/v1/consumer/trips/{trip_id}/participants",
        status_code=201,
        response_model=Envelope[Participant],
    )
    def participant(
        trip_id: UUID,
        payload: ParticipantCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"trips/{trip_id}/participants",
            payload.model_dump(mode="json"),
            lambda service: service.participant(identity, trip_id, payload),
        )

    @app.post(
        "/v1/consumer/trips/{trip_id}/itinerary",
        status_code=201,
        response_model=Envelope[ItineraryItem],
    )
    def itinerary(
        trip_id: UUID,
        payload: ItineraryCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        def create(service):
            trip = service.owned(identity, "trip", trip_id)
            if (
                trip["start_date"]
                and payload.day < date.fromisoformat(trip["start_date"])
                or trip["end_date"]
                and payload.day > date.fromisoformat(trip["end_date"])
            ):
                raise ControlError(
                    422, "invalid_day", "Itinerary day must be within the trip"
                )
            for identifier in payload.participant_ids:
                person = service.owned(identity, "participant", identifier, trip_id)
                if (
                    person["arrive"]
                    and payload.day < date.fromisoformat(person["arrive"])
                ) or (
                    person["depart"]
                    and payload.day > date.fromisoformat(person["depart"])
                ):
                    raise ControlError(
                        422,
                        "absent_participant",
                        "This traveler is not present on that day",
                    )
            trip.update(
                version=trip["version"] + 1, context_version=trip["context_version"] + 1
            )
            service.put(identity, "trip", trip)
            return service.put(
                identity,
                "itinerary",
                ItineraryItem(**payload.model_dump(), id=uuid4(), trip_id=trip_id),
            )

        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"trips/{trip_id}/itinerary",
            payload.model_dump(mode="json"),
            create,
        )

    @app.post(
        "/v1/consumer/trips/{trip_id}/expenses",
        status_code=201,
        response_model=Envelope[Expense],
    )
    def expense(
        trip_id: UUID,
        payload: ExpenseCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return mutate(
            request,
            response,
            identity,
            replay_key,
            f"trips/{trip_id}/expenses",
            payload.model_dump(mode="json"),
            lambda service: service.expense(identity, trip_id, payload),
        )

    @app.post(
        "/v1/consumer/trips/{trip_id}/shares",
        status_code=201,
        response_model=Envelope[ShareCreated],
    )
    def share(
        trip_id: UUID,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        # Reconstruct a capability for replay; persist only its hash, never the token.
        message = f"share:{identity}:{trip_id}:{replay_key}".encode()
        token = hmac.new(
            request.app.state.demo_secret.encode(), message, hashlib.sha256
        ).hexdigest()

        def create(service):
            service.owned(identity, "trip", trip_id)
            body = Share(
                id=uuid4(),
                trip_id=trip_id,
                expires_at=service.store.now() + timedelta(days=1),
            ).model_dump(mode="json")
            service.put(
                identity,
                "share",
                {**body, "digest": hashlib.sha256(token.encode()).hexdigest()},
            )
            return body

        result = mutate(
            request,
            response,
            identity,
            replay_key,
            f"trips/{trip_id}/shares",
            {},
            create,
        )
        return {**result, "data": {**result["data"], "token": token}}

    @app.delete("/v1/consumer/trips/{trip_id}/shares/{share_id}", status_code=204)
    def revoke_share(
        trip_id: UUID,
        share_id: UUID,
        request: Request,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        service = domain(request)

        def revoke():
            body = service.owned(identity, "share", share_id, trip_id)
            service.version(body, if_match)
            body.update(revoked=True, version=body["version"] + 1)
            service.put(identity, "share", body)

        service.store.transaction(revoke)
        return Response(status_code=204)

    @app.get("/v1/consumer/share/{token}", response_model=Envelope[SharedNotebook])
    def shared(token: str, request: Request):
        service = domain(request)

        def lookup():
            row = service.store.db.execute(
                "SELECT actor,body FROM objects WHERE kind='share' AND json_extract(body,'$.digest')=?",
                (hashlib.sha256(token.encode()).hexdigest(),),
            ).fetchone()
            if row is None:
                raise ControlError(404, "not_found", "Share unavailable")
            body = json.loads(row["body"])
            from datetime import datetime

            if (
                body["revoked"]
                or datetime.fromisoformat(body["expires_at"]) <= service.store.now()
            ):
                raise ControlError(404, "not_found", "Share unavailable")
            trip = service.owned(row["actor"], "trip", body["trip_id"])
            return SharedNotebook(
                title=trip["title"],
                destination=trip["destination"],
                start_date=trip["start_date"],
                end_date=trip["end_date"],
                itinerary=[
                    SharedItinerary(
                        **{name: item[name] for name in SharedItinerary.model_fields}
                    )
                    for item in service.collection(
                        row["actor"], "itinerary", trip["id"]
                    )
                ],
            )

        return read(request, lambda _: lookup())

    @app.get("/v1/consumer/providers")
    def providers(request: Request, identity=Depends(actor)):
        return envelope(
            request,
            {
                "mode": "fixture",
                "places": "sample",
                "events": [
                    {
                        "provider": name,
                        "state": "not_configured",
                        "access": "Official API or explicit permitted data only",
                    }
                    for name in (provider.name for provider in EVENT_PROVIDERS)
                ],
                "google_calendar": "demo_only",
                "weather": "sample",
                "garment_recognition": "manual_tagging",
            },
        )
