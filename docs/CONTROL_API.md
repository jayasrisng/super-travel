# Wonder agent control API — implementation handoff

> Current consumer supplement: [CONSUMER_APP.md](CONSUMER_APP.md). Checked OpenAPI defines implemented local routes. Latest consumer scope supersedes older Magic-first/website ownership; production beta gates below remain separate.


This change implements the three requested agent backends and their local control API. The website belongs to D4; no frontend is included. Python remains in the existing `super_travel/` package to avoid moving teammates' Essentials/Recovery code.

## Run locally

Python 3.12+ and uv are required. The lockfile pins the installed dependencies.

```sh
uv sync --frozen
cp .env.example .env
# Generate a token directly into the ignored local file; never put it in a browser bundle.
uv run python -c 'import secrets; from pathlib import Path; p=Path(".env"); p.write_text(p.read_text()+"\nWONDER_API_TOKEN="+secrets.token_urlsafe(32)+"\n")'
uv run uvicorn super_travel.control.app:app --host 127.0.0.1 --port 8000 --env-file .env
```

Interactive API documentation is at `http://127.0.0.1:8000/docs`. Authorize with the token from your ignored `.env`. Fixture mode needs no provider key. All data-bearing routes require authentication. Missing/short configured tokens fail startup; there is no public fallback.

| Setting | Current use |
|---|---|
| `WONDER_API_TOKEN` | Random secret, at least 32 characters; one local actor identity derived from its hash |
| `WONDER_AGENT_MODE=fixture` | Default: three runnable synthetic proposal engines |
| `WONDER_AGENT_MODE=llm` | Planning/packing use the existing Anthropic specialist runner; Magic reports `provider_unavailable` until a live adapter is supplied |
| `ANTHROPIC_API_KEY` | Required only for model calls; backend only, never a frontend key |
| `WONDER_DB_PATH=wonder-control.sqlite3` | SQLite local integration persistence, chmod 0600; ignored by Git |
| `WONDER_CORS_ORIGINS=http://localhost:3000` | Exact allowed development origins, comma-separated; CORS is not authorization |

Do not enable paid providers until the owner supplies a budget and the team adds enforced cost caps. No paid provider was called while developing or testing this change. The existing model name/fallback configuration is inherited from `core/llm.py`; live account/model access has not been verified. New agent calls use at most four runner iterations with a 20-second timeout per request and no SDK retries.

The shared token is for local trusted integration only. A website teammate can keep it in their server-side development proxy; native developers use an ignored local development configuration. It cannot be shipped as user authentication. Two distinct token-to-actor mappings can be injected via `create_app(tokens=...)` in synthetic tests; the standard launcher provides one actor. Production replaces this seam with verified Supabase JWT identity and current database membership checks.

## Implemented operations

All paths include `/v1`. GET entity responses carry `ETag: "version"`. JSON is snake_case; money uses strict integer minor units; IDs are UUIDs; instants normalize to UTC. Error details identify validation fields without echoing inputs.

| Method and path | Behavior |
|---|---|
| GET `/agents` | Three agent keys, prototype-name mapping, configured mode, readiness and limitations |
| POST `/agent-runs` | Discriminated agent request; returns 202 and queued run |
| POST `/magic/runs` | Convenient Magic input shape; returns the same run contract |
| GET `/agent-runs` | Actor-owned runs, cursor/limit pagination |
| GET `/agent-runs/{run_id}` | Current state, typed result or redacted failure |
| POST `/agent-runs/{run_id}/cancel` | Cancel queued/running work; requires current `If-Match` |
| POST `/trips` | Minimal owner-only integration context; destination/dates/timezone/traveler counts/interests |
| GET `/trips/{trip_id}` | Same actor only; versioned minimal context |
| POST `/me/saved-experiences` | Save an unexpired recommendation from the actor's succeeded Magic run |
| GET `/me/saved-experiences` | Actor-owned minimal saved records, cursor/limit pagination |
| DELETE `/me/saved-experiences/{saved_id}` | Actor-owned deletion; requires `If-Match` |

Every POST requires a UUID `Idempotency-Key`. The same actor/route/key/input replays the original response envelope for 24 hours; changed input returns 409. Replaying create returns the original queued snapshot even if the run has since finished: GET the run for current state. Omitted trip-context fields and explicit defaults are distinguished in the replay digest. Cancel replays also include the original `If-Match` value in the digest. DELETE uses ETag without a replay key.

Responses use `{data,meta:{request_id,next_cursor}}`; errors use `{error:{code,message,details,retryable},meta:{request_id}}`. `X-Request-ID` identifies the current transport attempt; a replayed envelope retains its original request ID. Common errors: 401 unauthorized; 404 hidden/missing resource; 409 replay conflict/not-ready/expired recommendation; 412 stale ETag; 422 invalid or missing constraints/unsupported area; 428 missing ETag; 429 full queue; 503 storage unavailable. Unknown routes return an error envelope. A missing replay header is a 422 schema error.

Create → poll after one second → increase interval up to ten seconds → stop on `succeeded`, `failed`, `cancelled` or `expired`. Retry failed work with a new key. No progress percentages are fabricated. For cancellation, read the latest ETag first; a state change between read/cancel yields 412.

## Agent contracts and boundaries

| Wire key | Existing protocol name | Behavior |
|---|---|---|
| `plan_book` | `planning` | Itinerary items, checklist tasks and budget estimates; no booking tools or verified inventory |
| `pack_shop` | `packing` | Categorized item quantities and preparation tasks; no purchases or packing-state mutation |
| `explore_magic` | `explore` | Normalized provider candidates filtered/ranked by deterministic feasibility; saving creates only a private saved record |

Standalone Plan/Pack require destination, start_date and end_date. Trip mode can omit those fields: the service reads only an actor-owned snapshot. Explicit null remains explicit and fails if a required constraint becomes absent. Unknown fields fail rather than silently accepting private documents. Traveler counts default to one adult; trip counts fill omitted fields. The model sees only the resolved input, never full TripContext, documents, passenger names, PNRs or ledger rows. The existing prototype `.run(task, trip)` adapter uses a destination/date allowlist and returns `AgentResult` without mutating the trip. Explore's prototype `.run` expects a JSON-encoded MagicInput, since free text cannot safely supply location/time.

Model-generated planning/packing drafts have `data_mode=live` meaning a real model execution, **not verified travel data**. Sources are cleared by the service because no research tools were called. Always show “model-generated, unverified” and the agent limitation; never infer booking, weather, price or source verification from this field. Synthetic fixtures have `data_mode=fixture` throughout. Budget estimates are proposals, not authoritative arithmetic or quotes.

Magic's primary list fits outbound + activity + onward + buffer against the earlier of the requested window and next commitment, using UTC arithmetic across Barcelona DST. Known costs must fit any supplied EUR budget. Unknown route/hours/required cost or unverified live availability excludes primary results; separately listed uncertain results require `allow_unknown_feasibility=true`. No return leg is inferred when no next commitment was supplied. Candidates and origins must be within a temporary Barcelona demo rectangle (latitude 41.32–41.47, longitude 2.05–2.23); this is explicitly **not** the reviewed private-beta polygon. Dates/hours/routes/costs in the fixture adapter are simulated, irrespective of wall-clock time or origin.

Recommendation validity is capped at 15 minutes and shortened by provider expiry, closing time and the time window. Save checks validity again. Saved records retain title, scope and fixture/live label, not precise origin or route history; they are bookmarks, not reservations. Agent-run retention does not extend recommendation validity.

## Durability and limitations

SQLite transactions serialize enqueue/replay/cancel/save. One worker claims a lease, computes outside the transaction and writes only if the same lease is still current and the run remains running. Lease expiry after 120 seconds permits recovery after a restart; an older completion cannot overwrite a reclaimed or cancelled run. Cancel stops publication of late results; it cannot undo an already-issued model request or its billing. External actions are never issued.

The worker queue is bounded at ten active runs per actor and 100 globally. Requests are capped at 32 KiB. Runs expire after 24 hours: cleanup clears request/proposal/error contents; tombstones disappear a day later. Cleanup happens on worker ticks and transactional API access, so an idle stopped process performs cleanup on restart. SQLite is not encrypted; backup copies and filesystem journals are not a production erasure guarantee. Trips and bookmarks persist until manually deleting the local database or deleting a bookmark; production retention/erasure needs its own implementation.

This is an integration/demo adapter, not a private-beta release. Missing beta capabilities include verified JWTs/membership revocation/RLS, PostgreSQL migrations and runtime-role isolation, managed worker shutdown/lease heartbeats, enforced billing quotas, licensed live POI/route/hours adapters, tested boundary polygon, reviewed apply-to-itinerary/packing domain services, navigation link allowlisting and web/iOS parity. The teammate CLI orchestrator is implemented, but no HTTP `/chat`, domain apply, purchase, external message or sponsor execution endpoint is implemented. Calling a planned route returns 404; do not render a success state.

## Contract ownership and checks

[Checked OpenAPI](../packages/contracts/openapi.json) is canonical for **implemented control routes**. [Request fixtures](../packages/contracts/fixtures/agent_requests.json) and [proposal fixtures](../packages/contracts/fixtures/agent_proposals.json) are synthetic decoding examples; Magic fixture timestamps are intentionally fixed, not fresh recommendations. Generate TypeScript/Swift clients from this artifact with the client owner's selected tool; none have been hand-written or claimed as generated here.

```sh
uv run python -m scripts.export_control_contract
uv run pytest -q -m 'not network'
uv run ruff check super_travel/control super_travel/agents/proposals.py super_travel/agents/planning super_travel/agents/packing super_travel/agents/explore scripts/export_control_contract.py tests/test_control.py
```

Tests cover token/actor/trip isolation, strict inputs/money, replay/conflict including omitted overrides, queue limits/pagination, cancellation/late completion, lease recovery/restart, expiry redaction, saving/deletion, three-agent results, fake model API execution, private-context nonmutation, DST/onward/budget/unknown feasibility and checked artifact drift. Existing Essentials/Recovery tests are retained. Tests use synthetic tokens and localhost fake servers; no provider credentials are needed.

Future domain prose in DATA_MODEL/CONTRACTS remains the private-beta design. This local TripCreate adds a required destination and interests, excludes membership/budget/guest lifecycle and does not imply the full Trip is shipped. See decision T14 for this deliberate staging boundary. D1 and affected web/iOS owners should review the exported contract before wiring clients.
