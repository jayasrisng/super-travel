# Wonder

**Less searching. More experiencing.**

Wonder connects trip planning, preparation, local discovery, essentials, and group coordination through one personalized checklist. It supports multiple independent trips and direct use of individual tools. Magic answers “What can I do with the time I have?” using location, preferences, travel time, and the next commitment.

## Current status

The repository now contains the existing Essentials/Recovery prototypes and a working FastAPI control backend for **Plan & Book, Pack & Shop and Explore/Magic**. All three support labeled synthetic fixtures. Planning and Packing can use the existing Anthropic model runner; live Magic discovery/routing adapters are still required. The teammate-built advisor dashboard is in `dashboard/`; it reads synthetic static data and is not connected to the control API. Main also contains an onboarding HTML demo with missing local asset dependencies. Neither is a shipped consumer web app.

The local backend provides authenticated create/poll/list/cancel, durable SQLite runs, actor-owned minimal trips and Magic bookmarks. It is an integration/demo backend, not a private-beta deployment. See [control API handoff](docs/CONTROL_API.md) for runnable setup, exact endpoints, limitations and [checked OpenAPI](packages/contracts/openapi.json).
## Start here

| Document | Purpose |
|---|---|
| [Product brief](docs/product/PRODUCT_BRIEF.md) | Preserved user brief; product source of truth |
| [Team build brief](docs/TEAM_BUILD_BRIEF.md) | Refined five-person operating agreement |
| [Plan](PLAN.md) | Dependencies, milestones, integration gates, acceptance criteria |
| [MVP roadmap](docs/MVP_ROADMAP.md) | Prioritized backlog and owner assignments |
| [Architecture](ARCHITECTURE.md) | Technical choices, boundaries, security and deployment |
| [Data model](docs/DATA_MODEL.md) | Normative entities, constraints, money and time semantics |
| [API contracts](docs/api/CONTRACTS.md) | Normative v1 operations, schemas and examples |
| [Hackathon integration plan](docs/HACKATHON_INTEGRATIONS.md) | Sponsor boundaries, event deadline and proof of meaningful use |
| [Decision register](docs/decisions/DECISIONS.md) | Trade-offs, assumptions and questions for the product owner |
| [Control API handoff](docs/CONTROL_API.md) | Implemented backend, setup, wire contracts and limitations |
| [Integration status](docs/INTEGRATION_STATUS.md) | Merged contributions, checks and remaining seams |
| [Next steps](docs/NEXT_STEPS.md) | Prioritized work from the current implementation |
| [Agent instructions](AGENTS.md) | Repository-wide contributor and coding-agent rules |

The product is now named Wonder; the repository retains `super-travel`. Product intent comes from the preserved Super Travel brief plus explicit owner decisions in the decision register. Explicitly proposed scope reductions require product-owner agreement; they do not silently replace required MVP capabilities. Technical contracts govern implementation after the Phase 0 review. Conflicts must be resolved through a documented decision, rather than choosing whichever document is convenient.

## Release strategy

The owner chose a **Barcelona Magic private beta first**, with equally complete core web and native iOS. Today’s SpeedHacks demo is a separate milestone with honest limitations; its deadline is October 11, 2026 at 5 PM PDT. See [hackathon integrations](docs/HACKATHON_INTEGRATIONS.md) for the five partner tools, demonstrated-use strategy and submission plan. The full connected MVP includes auth, multiple personalized trips, checklist, three agents, itinerary and packing proposals, Magic, participants, expenses, share links, a basic Passport, essentials/recovery, responsive web, and native iOS. The original brief called for an iOS prototype; the owner now requires equally complete core web/native iOS for Magic beta. The demo may use prominently labeled fixtures; private beta requires operational integrations for any advertised live capability. Native iMessage extension, widgets, push notifications, direct bookings, payments, and merchant tools have separate later gates.

The first vertical slice is sign in → ask Magic in Barcelona → receive sourced, feasible recommendations → save or navigate → see saved state on web and iOS. Trip creation, checklists, packing, expenses and Passport follow in the connected MVP. An event prototype may use fixtures, but it cannot be described as beta-ready.

## Chosen foundation

Next.js App Router + TypeScript + Tailwind/shadcn for web; SwiftUI for iOS; Python/FastAPI + Pydantic for a modular backend; Supabase PostgreSQL/Auth; SQLAlchemy and reviewed SQL migrations; pnpm for web workspaces and uv for Python. Python dependencies are installed and locked with uv. The current local adapter uses SQLite and a private bearer token; Supabase/PostgreSQL remains the beta target. Web/iOS tooling belongs to the respective teammate.

REST `/v1` is the application boundary. FastAPI owns all trip reads/writes and authorization; clients use Supabase directly only for authentication. Agents receive scoped trip snapshots and return proposals. Clients never receive database credentials or AI keys. There is no purchase execution or payment processing in MVP.

## Target repository layout

```text
apps/web/                         # responsive app and public share fallback (D4)
apps/ios/                         # Xcode host app and extension targets (D5)
  Wonder/Features/Coordination/ # coordination Swift sources (D2)
  Extensions/Messages/            # later extension sources (D2)
  Extensions/Widget/              # later widget sources (D5)
services/api/src/super_travel/
  core/                           # auth, persistence, context, jobs (D1)
  domains/coordination/            # participants, invites, shares (D2)
  domains/operations/              # checklist, essentials, expenses, recovery (D3)
  agents/                         # plan_book, pack_shop, explore_magic (D1)
  integrations/                   # provider interfaces and adapters (D1)
packages/contracts/               # checked control OpenAPI/fixtures; generated clients follow (D1)
packages/design-tokens/           # future shared visual tokens (D4)
database/migrations/              # serialized migration review (D1)
database/seeds/                   # synthetic demo scenarios (D3)
docs/                             # specifications and decisions
.github/workflows/                # future CI (D1)
```

This is the beta target layout. Current Python code remains in root `super_travel/`; the app directories are not created by this change. Agents and integrations are modules of one backend package, not separate deployed services. Domain tests live alongside their owning packages; cross-platform contract fixtures will live in `packages/contracts/fixtures/`.

## Working locally today

Follow [CONTROL_API.md](docs/CONTROL_API.md#run-locally) to generate a local token and launch the three-agent API on port 8000. Fixture mode requires no provider keys.

```sh
uv sync --frozen
uv run pytest -q -m 'not network'
uv run python -m scripts.export_control_contract
```

Existing specialist CLI scripts require `ANTHROPIC_API_KEY` in an ignored `.env`:

```sh
uv run python scripts/run_essentials.py
uv run python scripts/run_recovery.py ev1
```

The CLI orchestrator is implemented and delegates to all five registered specialists; an HTTP `/chat` endpoint is not implemented. Model chat requires `ANTHROPIC_API_KEY`:

```sh
uv run python scripts/chat.py
uv run python scripts/chat.py --event all
```

### Agency dashboard (live)

The advisor console reads the control API through a small Node server that keeps the token server-side. After an intake call, all five agents run for the client's trip and their proposals appear on the dashboard.

```sh
uv run uvicorn super_travel.control.app:app --host 127.0.0.1 --port 8000 --env-file .env   # terminal 1
node dashboard/serve.mjs                                                                    # terminal 2: http://localhost:5180
uv run python scripts/seed_demo.py                                                          # optional: demo client + sample delay
```

- **Onboarding:** `http://localhost:5180/onboarding/#onboard`. Play the scripted call, then **Send to Wonder agents**. It posts to `POST /v1/intakes`, which creates the trip and queues Plan & Book, Pack & Shop, Explore/Magic (Barcelona only), Travel Essentials and Manage & Recover.
- **Dashboard:** pick a client, see each agent's proposal, report a disruption (Manage & Recover computes EU261/US DOT/baggage rights and drafts the claim), save Magic ideas, re-run an agent.
- Approve/Dismiss in the review queue is recorded in the browser only; nothing is sent. The onboarding page's images, fonts and analytics script are still missing from the repo (see INTEGRATION_STATUS.md).

## Team workflow

Use `docs/<topic>`, `feat/<domain>-<topic>`, or `fix/<domain>-<topic>` branches and small PRs. Do not push directly to main. Identify the owner, affected contracts, tests, migration impact, screenshots where relevant, and fallback behavior in every implementation PR. Contract and shared-core changes need D1 plus an affected consumer; money/permission changes need an independent reviewer. See the team brief for file-level boundaries and shared-file locking.

Keep secrets, precise location history, documents and personal expenses out of Git/logs. Add `.env.example` names without values when a configuration requirement changes. Do not invent provider access, live availability, booked status or production readiness.

## Configuration and integrations

[`.env.example`](.env.example) lists planned settings. The implemented control uses `WONDER_AGENT_MODE=fixture`; planned domain adapters use `PROVIDER_MODE`. Unavailable integrations remain explicit; fixtures must be visibly marked and disabled in public release. Provider selection requires credential access, usage/cost caps, license review and a successful operational smoke test. Live Magic starts in Barcelona (Europe/Madrid, EUR); the exact coverage boundary and monthly budget remain open. Alike, Darwin, Dial, Keewano and Sparta have independent integration gates. No paid services have been provisioned.

## Success and release readiness

Measure time from a submitted need to a meaningful action: accepting a packing proposal, saving a feasible activity, completing a next task, or recording an expense. Track p50/p90 by journey, completion, AI cost, failure rates and repeat use. External link clicks are not confirmed bookings; settlement records are not payment transfers. Consent-aware analytics must exclude exact locations, traveler constraints, amounts and private itinerary text.

The release gates in `PLAN.md` require durable state, trip isolation, recoverable failures, provenance, accessible UI, cross-client consistency and a restore rehearsal. Hosting, jurisdiction, provider licensing, support and monthly budget are private-beta readiness decisions; public launch needs its own gate. No license file exists; public visibility is not a license grant. The owner should choose a license before inviting external contributions.
