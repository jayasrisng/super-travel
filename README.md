# Wonder

**Less searching. More experiencing.**

Wonder is a personal travel notebook: a trip checklist, five travel agents, a digital wardrobe, lighter packing, a daily morning note, and Magic for the moments in between. It uses warm paper and pencil in light mode and a muted chalkboard in dark mode.

## Run the consumer app

Requirements: Python 3.12+ (verified with 3.13), `uv`, Node 22.19+, and pnpm 10.18.3. Run from the repository root.

```sh
uv sync --frozen
pnpm --dir apps/web install --frozen-lockfile
uv run python scripts/run_consumer.py
```

In a second terminal:

```sh
pnpm --dir apps/web dev
```

Open **http://127.0.0.1:5173**. API documentation: http://127.0.0.1:8000/docs. No paid credentials are needed. Both servers bind locally. Keep this adapter on your own computer.

The launcher creates an ignored, private `.wonder.local.env` signing secret and `wonder-consumer.sqlite3` database. A signed HttpOnly cookie identifies each browser notebook; it expires after seven days. Neither the signing secret nor a shared bearer token goes into JavaScript. Restarting the server and refreshing the browser preserves your records. Clearing the cookie, rotating the secret, or session expiry creates another notebook; this is not account recovery or production authentication. Access logging is disabled to keep share capabilities out of logs. Never commit local databases, secrets or uploaded photos.

## What works now

- Home with multiple independent trips, progress and next task; standalone Magic and Wardrobe.
- Three-step onboarding with destination/undecided destination, date certainty, traveler counts and child ages, preferences, activities, budget and existing booking notes. Details remain editable.
- Personalized, persisted checklist. Add/edit/assign/delete tasks; queued execution, actual worker states, results/history, cancel, rerun, approve/reject, manually complete and reopen. User instructions survive agent runs. Approval applies draft itinerary notes, and never implies a reservation or purchase.
- All five registered specialists through the existing control service: Plan & Book, Pack & Shop, Explore & Experience, Travel Essentials, Manage & Recover. The latter two reuse the existing specialist runners in optional model mode on an isolated proposal snapshot.
- 34 original illustrated clothes: 10 tops, 10 bottoms, four shoes, 10 accessories. Filters, favorites, manual tags, photo upload/edit/delete. Uploaded photos are size-limited, resized and stripped of metadata.
- Deterministic compatible capsule outfits, manual temperature/occasion controls, illustrated lookbooks, mouse/touch swipes, keyboard and accessible voting buttons, persisted likes/dislikes and last-vote undo. Rejected combinations are excluded from subsequent generation.
- Per-trip deduplicated packing from liked outfits; extra pieces/essentials, packed state and ready/worn/dirty/unavailable state. Saved outfit photos, relevant dates and tomorrow's options. Packing rebuilds preserve wear and packed state; unavailable pieces are excluded from new generation and carry warnings in saved looks.
- Opt-in synthetic calendar events, explicit selection and disconnect. Persisted daily briefing combines selected events and saved itinerary, sample weather, ready packed outfits and outstanding tasks. Notification preference is stored; delivery is in-app only.
- Magic uses the existing feasibility engine, scoped asynchronous runs, expiry/provenance, time/budget/buffers and optional next commitment. Manual or permission-based location, Save, Navigate and details; saved moments persist.
- Owner-managed partial-trip participants, date-bounded destination segments and itinerary notes with same-trip participant assignment. Exact equal expense splits in integer minor units. One-day, revocable, redacted itinerary share links.

Try the full journey: create a Tokyo family trip → edit a task and ask Wonder → review/accept its sample proposal → open 34-piece wardrobe → generate/swipe outfits → build/check packing → reopen saved looks → select demo calendar events → read the morning note → use Magic and save a moment → refresh.

## Demo versus live

| Capability | Current behavior | Needed for live use |
|---|---|---|
| Agents | Fixture proposals by default; real queue and state transitions | Anthropic credentials for optional model drafts; verified research/booking adapters remain separate |
| Magic | Simulated places, routes, hours and costs at an entered origin; location does not assert real coverage | Permitted places/events/hours/routes adapters and source licenses, budget and monitoring |
| Wardrobe | Original SVG illustrations or user photos; manual tagging; deterministic lookbooks | Optional garment recognition/renderer adapter, with confirmed user tags |
| Calendar | Selected synthetic events only | Implement read-only Google OAuth adapter, consent, encrypted tokens, refresh/revocation and permission handling |
| Weather | Explicit sample forecast or manually entered outfit temperature | Implement a licensed weather adapter |
| Sharing | Owner notebook plus read-only guest itinerary | Verified accounts, memberships, invitations and collaborative permissions |
| Notifications/iOS | Stored preference and documented briefing contract | Scheduler, delivery permissions, native SwiftUI app, signing and WidgetKit target |

Entering credentials does not silently enable unimplemented providers. Event boundaries for Luma, Partiful, Eventbrite and Meetup fail as unconfigured until a legitimate adapter exists. There are **no executed bookings, purchases, payments, outbound claims or messages**. Sample navigation links lead to illustrative coordinates. No photorealistic try-on, live forecast, live calendar, automated morning delivery or native widget is claimed.

Optional model drafts use the existing Anthropic integration:

```sh
WONDER_AGENT_MODE=llm uv run python scripts/run_consumer.py
```

Set `ANTHROPIC_API_KEY` only in your ignored backend environment. This opts into paid calls. Planning/Packing use their existing proposal adapters; Essentials/Recovery run against isolated snapshots. No live smoke test has been run in this change. Magic model mode fails explicitly without a live discovery adapter.

## Check the implementation

```sh
uv run pytest -q -m 'not network'
uv run ruff check super_travel/consumer super_travel/control scripts/run_consumer.py scripts/build_wardrobe_assets.py tests/test_consumer.py
uv run python scripts/export_control_contract.py
pnpm --dir apps/web contracts
pnpm --dir apps/web build
pnpm --dir apps/web exec playwright install chromium
pnpm --dir apps/web test
```

Playwright starts local fixture API/web servers when they are absent, reuses existing servers outside CI, and tests the Tokyo journey, persistence, empty/loading/error recovery, mouse and touch swipes, keyboard controls, responsiveness and automated accessibility checks. Tests use synthetic data and separate browser identities. The network-marked model smoke test is excluded. CI also checks exported OpenAPI/TypeScript drift; hosted CI results must be checked separately from local results.

[Desktop paper](docs/screenshots/home-light.png) · [desktop chalkboard](docs/screenshots/home-dark.png) · [outfit lookbook](docs/screenshots/outfits-light.png) · [mobile paper](docs/screenshots/mobile-light.png) · [mobile chalkboard](docs/screenshots/mobile-dark.png) · [mobile outfit](docs/screenshots/mobile-outfits.png).

## Structure and contracts

```text
apps/web/                     React + strict TypeScript + Vite consumer app
  src/api.generated.ts        generated from checked OpenAPI; never hand-edit
  src/notebook.css            shared paper/chalkboard tokens and components
  tests/                      browser journeys and accessibility checks
super_travel/control/         existing FastAPI identity, SQLite jobs/replays/leases
super_travel/consumer/        owner-scoped consumer models, routes and services
  coordination.py             participants, segments and exact expenses
  wardrobe.py                 wardrobe, outfits, votes and packing
  providers/                  event/calendar/weather boundaries
super_travel/agents/          existing five specialists and orchestrator
packages/contracts/           canonical implemented OpenAPI and fixtures
scripts/run_consumer.py        local fixture launcher
scripts/build_wardrobe_assets.py original asset generator
docs/                         briefs, handoff, beta design, screenshots
```

REST `/v1` is the domain boundary. Pydantic models define the wire contract; generated TypeScript consumes it. UUID ownership, same-trip checks, idempotency, ETags, context versions, civil dates/IANA zones and integer money are enforced by the backend. UI approval applies current proposals through application services. SQLite is shared with the existing local control API; no duplicate authoritative store or agent stack was introduced.

Vite is the implemented local frontend choice; the earlier Next.js/Supabase deployment plan remains a separate beta architecture. This keeps a small static client and reuses FastAPI directly. It sacrifices server-rendered pages and production account infrastructure, which this local implementation does not need. Production requires reviewed identity/membership, PostgreSQL/RLS, managed workers, quotas, migrations and licensed live providers.

The teammate's `dashboard/` advisor demo, `super_travel/onboarding/` saved HTML and CLI orchestrator are preserved. Their limitations are recorded in [integration status](docs/INTEGRATION_STATUS.md). For the model-based CLI: `uv run python scripts/chat.py` or `uv run python scripts/chat.py --event all`.

## Continue here

The latest [consumer brief](docs/product/CONSUMER_BRIEF.md) and [notebook design](docs/product/NOTEBOOK_DESIGN.md) supersede older consumer priorities. The original [product brief](docs/product/PRODUCT_BRIEF.md) remains preserved.

[Consumer handoff and wire semantics](docs/CONSUMER_APP.md) · [plan](PLAN.md) · [architecture](ARCHITECTURE.md) · [roadmap](docs/MVP_ROADMAP.md) · [next steps](docs/NEXT_STEPS.md) · [team brief](docs/TEAM_BUILD_BRIEF.md) · [decisions](docs/decisions/DECISIONS.md) · [agent instructions](AGENTS.md) · [beta data model](docs/DATA_MODEL.md) · [beta API design](docs/api/CONTRACTS.md) · [widget contract](docs/WIDGET_CONTRACT.md).

Assets are original illustrations, generated locally. Caveat is bundled with its [SIL Open Font License](apps/web/public/fonts/OFL.txt), from [Google Fonts](https://github.com/google/fonts/tree/main/ofl/caveat). The repository's overall license has not been selected by the owner.
