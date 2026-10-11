"""Wonder local control API: uv run uvicorn super_travel.control.app:app."""

import hashlib
import hmac
import logging
import os
import sqlite3
import threading
from contextlib import asynccontextmanager
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from fastapi import Depends, FastAPI, Header, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.exceptions import HTTPException

# FastAPI evaluates dependency defaults as declarations.
# ruff: noqa: B008
from super_travel.control.schemas import (
    AdvisorLink,
    AdvisorLinkCreate,
    AgentInfo,
    AgentRun,
    Envelope,
    ErrorEnvelope,
    ExploreRequest,
    InsurancePolicy,
    Intake,
    IntakeCreate,
    MagicRequest,
    Message,
    MessageCreate,
    PolicyCreate,
    RunRequest,
    SavedExperience,
    SaveRequest,
    TravelerMessageCreate,
    Trip,
    TripCreate,
)
from super_travel.control.service import Service
from super_travel.control.store import ControlError, Store


def create_app(
    *,
    path=None,
    tokens=None,
    mode=None,
    worker=True,
    now=None,
    agents=None,
    demo_auth=None,
):
    mode = mode or os.getenv("WONDER_AGENT_MODE", "fixture")
    if mode not in ("fixture", "llm"):
        raise ValueError("WONDER_AGENT_MODE must be fixture or llm")

    demo_auth = (
        demo_auth
        if demo_auth is not None
        else os.getenv("WONDER_DEMO_AUTH", "false") == "true"
    )
    if demo_auth and os.getenv("APP_ENV", "local") != "local":
        raise RuntimeError("Demo authentication is forbidden outside APP_ENV=local")

    @asynccontextmanager
    async def lifespan(app):
        configured = tokens
        if configured is None:
            token = os.getenv("WONDER_API_TOKEN", "")
            if len(token) < 32:
                raise RuntimeError(
                    "Set WONDER_API_TOKEN to a random token of at least 32 characters"
                )
            configured = {
                token: uuid5(NAMESPACE_URL, hashlib.sha256(token.encode()).hexdigest())
            }
        app.state.tokens = configured
        app.state.demo_auth = demo_auth
        app.state.demo_secret = next(iter(configured))

        app.state.store = Store(
            path or os.getenv("WONDER_DB_PATH", "wonder-control.sqlite3"),
            **({"now": now} if now else {}),
        )
        app.state.service = Service(app.state.store, mode, agents)
        from super_travel.consumer.service import Notebook

        app.state.notebook = Notebook(app.state.store, app.state.service)
        stop = threading.Event()

        def consume():
            while not stop.is_set():
                try:
                    app.state.service.work_once()
                except sqlite3.DatabaseError:
                    logging.getLogger(__name__).warning(
                        "Control store operation failed; retrying"
                    )
                stop.wait(0.1)

        thread = threading.Thread(target=consume, daemon=True) if worker else None
        if thread:
            thread.start()
        try:
            yield
        finally:
            stop.set()
            if thread:
                thread.join(timeout=1)
            # An in-flight model call may finish late. Keep its store open until process exit;
            # cancellation/lease checks prevent resurrection. Production needs a managed worker.
            if not thread or not thread.is_alive():
                app.state.store.close()

    app = FastAPI(
        title="Wonder Consumer & Agent API",
        version="0.1.0",
        lifespan=lifespan,
        # Fixed descriptions keep the exported OpenAPI identical across Python versions
        # (3.13 renamed the 413 reason phrase).
        responses={
            status: {"model": ErrorEnvelope, "description": description}
            for status, description in {
                400: "Bad Request", 401: "Unauthorized", 403: "Forbidden", 404: "Not Found",
                409: "Conflict", 412: "Precondition Failed", 413: "Content Too Large",
                422: "Unprocessable Content", 428: "Precondition Required",
                429: "Too Many Requests", 503: "Service Unavailable",
            }.items()
        },
        description="Local consumer notebook and agent control. Explicit draft apply; fixture defaults; no external purchases.",
    )
    origins = [
        value.strip()
        for value in os.getenv("WONDER_CORS_ORIGINS", "http://localhost:3000").split(
            ","
        )
        if value.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_methods=["GET", "POST", "DELETE", "PUT", "PATCH"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "If-Match"],
        expose_headers=["ETag", "X-Request-ID"],
    )

    def error(request, status, code, message, details=None):
        return JSONResponse(
            status_code=status,
            content={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or [],
                    "retryable": status in (429, 503),
                },
                "meta": {"request_id": request.state.request_id},
            },
            headers={"X-Request-ID": request.state.request_id},
        )

    @app.middleware("http")
    async def boundaries(request, call_next):
        request.state.request_id = str(uuid4())
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            limit = (
                2_800_200
                if request.url.path.startswith("/v1/consumer/wardrobe/")
                and request.url.path.endswith("/photo")
                else 32768
            )
            if len(raw) > limit:
                return error(
                    request,
                    413,
                    "body_too_large",
                    "Request exceeds the size limit (32 KiB; photo uploads 2 MB)",
                )
        request._body = bytes(raw)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ControlError)
    async def control_error(request, exc):
        return error(request, exc.status, exc.code, exc.message)

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request, exc):
        details = [
            {
                "field": ".".join(str(part) for part in issue["loc"]),
                "reason": issue["type"],
            }
            for issue in exc.errors()
        ]
        return error(
            request,
            422,
            "invalid_request",
            "Request does not match the contract",
            details,
        )

    @app.exception_handler(HTTPException)
    async def http_error(request, exc):
        return error(
            request, exc.status_code, "http_error", "Request could not be handled"
        )

    @app.exception_handler(sqlite3.DatabaseError)
    async def storage_unavailable(request, exc):
        return error(
            request,
            503,
            "store_unavailable",
            "Control store is temporarily unavailable",
        )

    bearer = HTTPBearer(auto_error=False, scheme_name="LocalBearer")

    def actor(
        request: Request,
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
    ):
        value = credentials.credentials if credentials else ""
        for token, identity in request.app.state.tokens.items():
            if hmac.compare_digest(value.encode(), token.encode()):
                return identity
        if request.app.state.demo_auth and credentials is None:
            from super_travel.consumer.auth import verify

            return verify(request, request.app.state.demo_secret)
        raise ControlError(
            401,
            "unauthorized",
            "A valid local API bearer token or enabled demo session is required",
        )

    def key(idempotency_key: UUID = Header(alias="Idempotency-Key")):
        return idempotency_key

    def envelope(request, data, cursor=None):
        return {
            "data": data,
            "meta": {"request_id": request.state.request_id, "next_cursor": cursor},
        }

    def set_etag(response, body):
        response.headers["ETag"] = f'"{body["version"]}"'

    @app.get("/v1/agents", response_model=Envelope[list[AgentInfo]])
    def agents_status(request: Request, identity=Depends(actor)):
        return envelope(
            request,
            [
                {
                    "agent": wire,
                    "prototype_name": name,
                    "title": title,
                    "mode": mode,
                    "ready": mode == "fixture"
                    or (
                        wire != "explore_magic" and bool(os.getenv("ANTHROPIC_API_KEY"))
                    ),
                    "limitation": (
                        "Synthetic examples; no provider verification"
                        if mode == "fixture"
                        else "Model drafts only; no verified booking or shopping data"
                        if wire != "explore_magic"
                        else "Live discovery and route providers are not configured"
                    ),
                }
                for wire, name, title in [
                    ("plan_book", "planning", "Plan & Book"),
                    ("pack_shop", "packing", "Pack & Shop"),
                    ("explore_magic", "explore", "Explore / Magic"),
                    ("essentials", "essentials", "Travel Essentials"),
                    ("recovery", "recovery", "Manage & Recover"),
                ]
            ]
            + [
                {
                    "agent": wire,
                    "prototype_name": name,
                    "title": title,
                    "mode": mode,
                    "ready": True,
                    "limitation": limitation,
                }
                for wire, name, title, limitation in [
                    ("travel_essentials", "essentials", "Travel Essentials",
                     "Deterministic: curated country data, ECB rates, mock eSIM plans; no advisories"),
                    ("manage_recover", "recovery", "Manage & Recover",
                     "Deterministic rules on reported disruptions; no flight monitoring; claims are drafts"),
                    ("voice_quotes", "voice", "Voice agent: insurance quotes",
                     request.app.state.service.agents["voice_quotes"].describe()),
                ]
            ],
        )

    def enqueue(request, response, payload, identity, replay_key, route):
        result = request.app.state.store.create(
            identity,
            route,
            replay_key,
            payload.model_dump(mode="json", exclude_unset=True),
            lambda: envelope(
                request, request.app.state.service.create_run(identity, payload)
            ),
        )
        set_etag(response, result["data"])
        return result

    @app.post("/v1/agent-runs", status_code=202, response_model=Envelope[AgentRun])
    def create_run(
        payload: RunRequest,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        return enqueue(
            request, response, payload, identity, replay_key, "/v1/agent-runs"
        )

    @app.post("/v1/magic/runs", status_code=202, response_model=Envelope[AgentRun])
    def create_magic(
        payload: MagicRequest,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        adapted = ExploreRequest(
            agent="explore_magic",
            trip_id=payload.trip_id,
            input=payload.model_dump(exclude={"trip_id"}),
        )
        return enqueue(
            request, response, adapted, identity, replay_key, "/v1/magic/runs"
        )

    @app.get("/v1/agent-runs", response_model=Envelope[list[AgentRun]])
    def list_runs(
        request: Request,
        identity=Depends(actor),
        cursor: UUID | None = None,
        limit: int = Query(default=20, ge=1, le=100),
        trip_id: UUID | None = None,
    ):
        values, next_cursor = request.app.state.store.transaction(
            lambda: request.app.state.store.list(identity, "run", cursor, limit, trip_id)
        )
        return envelope(request, values, next_cursor)

    @app.get("/v1/agent-runs/{run_id}", response_model=Envelope[AgentRun])
    def get_run(
        run_id: UUID, request: Request, response: Response, identity=Depends(actor)
    ):
        body = request.app.state.store.transaction(
            lambda: request.app.state.store.get(identity, "run", run_id)
        )
        set_etag(response, body)
        return envelope(request, body)

    @app.post("/v1/agent-runs/{run_id}/cancel", response_model=Envelope[AgentRun])
    def cancel_run(
        run_id: UUID,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
        if_match: str | None = Header(default=None),
    ):
        store = request.app.state.store
        result = store.create(
            identity,
            f"/v1/agent-runs/{run_id}/cancel",
            replay_key,
            {"if_match": if_match},
            lambda: envelope(request, store.cancel(identity, run_id, if_match)),
        )
        set_etag(response, result["data"])
        return result

    @app.post("/v1/trips", status_code=201, response_model=Envelope[Trip])
    def create_trip(
        payload: TripCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        store = request.app.state.store

        def persist():
            body = Trip(
                **payload.model_dump(), id=uuid4(), owner_user_id=identity
            ).model_dump(mode="json")
            store.insert(identity, "trip", body)
            return envelope(request, body)

        result = store.create(
            identity, "/v1/trips", replay_key, payload.model_dump(mode="json"), persist
        )
        set_etag(response, result["data"])
        return result

    @app.get("/v1/trips/{trip_id}", response_model=Envelope[Trip])
    def get_trip(
        trip_id: UUID, request: Request, response: Response, identity=Depends(actor)
    ):
        body = request.app.state.store.transaction(
            lambda: request.app.state.store.get(identity, "trip", trip_id)
        )
        set_etag(response, body)
        return envelope(request, body)

    @app.post("/v1/intakes", status_code=201, response_model=Envelope[Intake])
    def create_intake(
        payload: IntakeCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        result = request.app.state.store.create(
            identity,
            "/v1/intakes",
            replay_key,
            payload.model_dump(mode="json"),
            lambda: envelope(
                request, request.app.state.service.create_intake(identity, payload)
            ),
        )
        set_etag(response, result["data"])
        return result

    @app.get("/v1/intakes", response_model=Envelope[list[Intake]])
    def list_intakes(
        request: Request,
        identity=Depends(actor),
        cursor: UUID | None = None,
        limit: int = Query(default=20, ge=1, le=100),
    ):
        values, next_cursor = request.app.state.store.transaction(
            lambda: request.app.state.store.list(identity, "intake", cursor, limit)
        )
        return envelope(request, values, next_cursor)

    @app.get("/v1/intakes/{intake_id}", response_model=Envelope[Intake])
    def get_intake(
        intake_id: UUID, request: Request, response: Response, identity=Depends(actor)
    ):
        body = request.app.state.store.transaction(
            lambda: request.app.state.store.get(identity, "intake", intake_id)
        )
        set_etag(response, body)
        return envelope(request, body)

    # ---- traveler side (consumer app): linked to the agency trip by client code ----

    @app.post("/v1/consumer/advisor-link", status_code=201, response_model=Envelope[AdvisorLink])
    def link_advisor(
        payload: AdvisorLinkCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        service = request.app.state.service
        result = service.store.create(
            identity, "/v1/consumer/advisor-link", replay_key, payload.model_dump(mode="json"),
            lambda: envelope(request, service.link_advisor(identity, payload.client_code)),
        )
        set_etag(response, result["data"])
        return result

    @app.get("/v1/consumer/advisor", response_model=Envelope[AdvisorLink])
    def get_advisor(request: Request, identity=Depends(actor)):
        service = request.app.state.service
        return envelope(request, service.store.transaction(lambda: service.advisor_link(identity)[0]))

    @app.get("/v1/consumer/advisor/messages", response_model=Envelope[list[Message]])
    def traveler_messages(request: Request, identity=Depends(actor)):
        service = request.app.state.service
        return envelope(request, service.store.transaction(lambda: service.traveler_messages(identity)))

    @app.post("/v1/consumer/advisor/messages", status_code=201, response_model=Envelope[Message])
    def traveler_send(
        payload: TravelerMessageCreate,
        request: Request,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        service = request.app.state.service
        return service.store.create(
            identity, "/v1/consumer/advisor/messages", replay_key, payload.model_dump(mode="json"),
            lambda: envelope(request, service.traveler_send(identity, payload.text)),
        )

    @app.get("/v1/consumer/advisor/policies/{policy_id}", response_model=Envelope[InsurancePolicy])
    def traveler_policy(policy_id: UUID, request: Request, identity=Depends(actor)):
        service = request.app.state.service
        return envelope(request, service.store.transaction(lambda: service.traveler_policy(identity, policy_id)))

    @app.post("/v1/trips/{trip_id}/messages", status_code=201, response_model=Envelope[Message])
    def create_message(
        trip_id: UUID,
        payload: MessageCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        result = request.app.state.store.create(
            identity,
            f"/v1/trips/{trip_id}/messages",
            replay_key,
            payload.model_dump(mode="json"),
            lambda: envelope(
                request, request.app.state.service.create_message(identity, trip_id, payload)
            ),
        )
        set_etag(response, result["data"])
        return result

    @app.get("/v1/trips/{trip_id}/messages", response_model=Envelope[list[Message]])
    def list_messages(trip_id: UUID, request: Request, identity=Depends(actor)):
        store = request.app.state.store

        def read():
            store.get(identity, "trip", trip_id)
            return store.thread(identity, "message", trip_id)  # oldest first, like a chat

        return envelope(request, store.transaction(read))

    @app.post(
        "/v1/trips/{trip_id}/insurance-policies",
        status_code=201,
        response_model=Envelope[InsurancePolicy],
    )
    def create_policy(
        trip_id: UUID,
        payload: PolicyCreate,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        result = request.app.state.store.create(
            identity,
            f"/v1/trips/{trip_id}/insurance-policies",
            replay_key,
            payload.model_dump(mode="json"),
            lambda: envelope(
                request, request.app.state.service.create_policy(identity, trip_id, payload)
            ),
        )
        set_etag(response, result["data"])
        return result

    @app.get(
        "/v1/trips/{trip_id}/insurance-policies/{policy_id}",
        response_model=Envelope[InsurancePolicy],
    )
    def get_policy(
        trip_id: UUID, policy_id: UUID, request: Request, response: Response, identity=Depends(actor)
    ):
        body = request.app.state.store.transaction(
            lambda: request.app.state.store.get(identity, "policy", policy_id)
        )
        if body["trip_id"] != str(trip_id):
            raise ControlError(404, "not_found", "Resource not found")
        set_etag(response, body)
        return envelope(request, body)

    @app.post(
        "/v1/me/saved-experiences",
        status_code=201,
        response_model=Envelope[SavedExperience],
    )
    def save(
        payload: SaveRequest,
        request: Request,
        response: Response,
        identity=Depends(actor),
        replay_key=Depends(key),
    ):
        store = request.app.state.store

        def persist():
            run = store.get(identity, "run", payload.run_id)
            if run["status"] != "succeeded" or run["agent"] != "explore_magic":
                raise ControlError(
                    409, "run_not_ready", "Save requires a succeeded Magic run"
                )
            candidates = (
                run["proposal"]["recommendations"]
                + run["proposal"]["uncertain_recommendations"]
            )
            candidate = next(
                (
                    item
                    for item in candidates
                    if item["id"] == str(payload.recommendation_id)
                ),
                None,
            )
            if candidate is None:
                raise ControlError(404, "not_found", "Recommendation not found")
            from datetime import datetime

            if datetime.fromisoformat(candidate["valid_until"]) <= store.now():
                raise ControlError(
                    409, "recommendation_expired", "Refresh Magic before saving"
                )
            body = SavedExperience(
                id=uuid4(),
                run_id=payload.run_id,
                recommendation_id=payload.recommendation_id,
                title=candidate["title"],
                trip_id=run["trip_id"],
                data_mode=run["proposal"]["data_mode"],
            ).model_dump(mode="json")
            store.insert(identity, "saved", body)
            return envelope(request, body)

        result = store.create(
            identity,
            "/v1/me/saved-experiences",
            replay_key,
            payload.model_dump(mode="json"),
            persist,
        )
        set_etag(response, result["data"])
        return result

    @app.get("/v1/me/saved-experiences", response_model=Envelope[list[SavedExperience]])
    def list_saved(
        request: Request,
        identity=Depends(actor),
        cursor: UUID | None = None,
        limit: int = Query(default=20, ge=1, le=100),
    ):
        values, next_cursor = request.app.state.store.transaction(
            lambda: request.app.state.store.list(identity, "saved", cursor, limit)
        )
        return envelope(request, values, next_cursor)

    @app.delete("/v1/me/saved-experiences/{saved_id}", status_code=204)
    def delete_saved(
        saved_id: UUID,
        request: Request,
        identity=Depends(actor),
        if_match: str | None = Header(default=None),
    ):
        store = request.app.state.store

        def remove():
            body = store.get(identity, "saved", saved_id)
            if if_match is None:
                raise ControlError(428, "precondition_required", "If-Match is required")
            if if_match != f'"{body["version"]}"':
                raise ControlError(
                    412,
                    "version_conflict",
                    "Read the latest saved item before deleting",
                )
            store.db.execute(
                "DELETE FROM objects WHERE id=? AND actor=?",
                (str(saved_id), str(identity)),
            )

        store.transaction(remove)
        return Response(status_code=204)

    from super_travel.consumer.api import register

    register(app, actor, key, envelope, set_etag)
    return app


app = create_app()
