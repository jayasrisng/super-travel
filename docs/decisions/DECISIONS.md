# Wonder decision register

Source hierarchy: preserved product brief → explicit product-owner changes → reviewed architecture/data/API specs → task plan. This register distinguishes agreed direction from selected technical defaults and unresolved commercial details. Updated October 11, 2026.

## Confirmed by product owner

| ID | Decision | Implication |
|---|---|---|
| P01 | App name Wonder; repository remains super-travel | use Wonder in new UI/docs; preserved original brief unchanged |
| P02 | Private beta first | event demo and beta readiness have distinct gates |
| P03 | Magic first; trip tools follow | standalone discovery is first vertical slice; original connected MVP stays in roadmap |
| P04 | Barcelona launch area | Europe/Madrid, EUR; precise supported boundary needs review |
| P05 | Web and native iOS equally complete | both meet Magic core gate before beta; no prototype exemption |
| P06 | D3 takes deterministic backend workflows | D1 agents/shared core, D2 coordination, D3 operations, D4 web, D5 native |
| P08 | Complete consumer application and notebook design explicitly authorized in new owner briefs | Build connected Tokyo trip/checklist/wardrobe/packing/Magic/briefing; supersedes P03 for local delivery and earlier exclusive website ownership. Home-city fixture origins do not change P04 live launch gate. Native production parity remains gated. |
| P07 | Building for SpeedHacks; integrate as much as possible | plan meaningful use of all five partners, time-box access and retain reliable core |

## Concrete technical defaults for review

| ADR | Choice / alternative | Reason and reconsideration trigger |
|---|---|---|
| T01 | modular FastAPI monolith vs separately deployed agent/integration services | simplest shared context for five people; reconsider on independent scaling/security requirement |
| T02 | PostgreSQL/Supabase Auth vs five distinct data stores | relational trip/ledger integrity; provider interfaces retain portability |
| T03 | API-only domain data; polling vs direct client writes/Realtime | consistent authorization/contracts; revisit realtime once collaboration latency is measured |
| T04 | OpenAPI 3.1/Pydantic with generated TS/Swift vs manually maintained models | cross-language drift prevention; formalize all schemas in Phase 0 |
| T05 | SwiftUI vs cross-platform wrapper | native product intent and extensions; accept three build toolchains |
| T06 | durable Postgres jobs vs Redis queue/LangGraph | low traffic and restart-safe runs; introduce orchestration only for demonstrated branching/throughput |
| T07 | Google Places/Routes proposed baseline; Darwin capability search optional adapter | known POI/routing semantics; don't assume Darwin is an event catalog; credential/license spike gates choice |
| T08 | guest read-only capability session vs anonymous unrestricted membership | useful no-install fallback with narrower leakage risk; writes wait for account claim |
| T09 | equal/custom splits, one trip currency vs FX and weighted ledger now | exact determinism; broader splits remain later vision work |
| T10 | explicit proposal apply, ETag/context version vs autonomous agent writes | prevents stale plan overwrite and preserves control |
| T11 | Postgres canonical state; Keewano read-only event insight | no conflicting authoritative copies; sponsor query must demonstrably change follow-up |
| T12 | reviewed external links; no payments/purchases/calls by default | actionability without unsupported transactional claims |
| T14 | local SQLite run store and private bearer token for authorized three-agent integration work | Preserve current Python package and avoid blocking teammate integration on provisioning. This does not replace beta Postgres/Auth/RLS: no public deployment or real tester identity with this adapter. Required local destination/interests are documented in CONTROL_API; reviewed domain apply and generated clients follow. |
| T13 | Vercel web / proposed Render API+worker / Supabase | separates async backend from frontend hosting; confirm region/cost/limits before provisioning |

These defaults are sufficiently specific for contract drafting. They do not authorize provisioning, billing or recording real user data. Change through a focused ADR update with affected-owner review. Prefer one source definition per semantic contract.

## Open product/commercial questions

| Question | Current safe assumption | Needed before / owner |
|---|---|---|
| Monthly hosting/AI/maps/messaging ceiling | no paid provisioning; quotas/kill switches required | enabling paid providers / product owner |
| Exact Barcelona coverage polygon and tester group | city-scale supported boundary, invite-only accounts | live Magic acceptance / owner+D1 |
| Model vendor and credential availability | one structured-output adapter; no arbitrary runtime vendor fan-out | live ranking / D1+owner |
| Sponsor keys/Act pilot/test numbers/world access | integrations remain planned, separate flags | each live proof / assigned developer |
| Apple team/signing/TestFlight path | validate available account/device setup; no claim of distribution | native beta / D5 |
| Legal entity/jurisdiction, retention, consent and support contact | minimize data; proposed expiry policies in architecture | private-beta onboarding / owner |
| Real developer handles and backup reviewers | numbered roles only; no invented CODEOWNERS identities | Phase 0 / D1 |
| License choice | repository has no license; no assumed external reuse grant | external contributions / owner |
| Partner prize-pane inconsistency | rely on published rubric; organizer clarification for awards | submission planning / owner |

Do not block documentation/fixture work on unanswered commercial questions. Do not convert silence into spending authorization. User requests to maximize integrations do not require sacrificing feasibility or truthful claims. Event eligibility of reused assets should be clarified with organizers by the team; this task has not contacted anyone or submitted feedback.

## Implemented consumer choices

- T15: React + TypeScript + Vite static consumer client instead of introducing Next.js server features for this local slice. Reuses FastAPI via same-origin `/v1` proxy, a small frontend runtime and generated OpenAPI DTOs. Trade-off: no SSR/production account infrastructure; revisit hosting/SSR with the web owner before beta.
- T16: Extend the existing SQLite control store with actor-scoped consumer objects and versioned transactions. Preserve shared worker/replay semantics and source package; do not duplicate backend or agents. Trade-off: generic JSON records need reviewed relational migration/RLS before beta.
- T17: Signed HttpOnly, same-site, localhost-only demo sessions; backend launcher generates an ignored secret. No shared bearer secret in JS. Trade-off: seven-day browser identity and no account recovery; cannot represent production accounts.
- T18: Original SVG capsule lookbooks, manual image tags, deterministic outfit ranking and vote history. No recognition/photorealistic try-on claim. Trade-off: heuristic styling and manually supplied occasion/temperature rather than live destination forecasts or automatic calendar styling.
- T19: Explicit synthetic calendar consent and in-app daily brief; event/weather interfaces fail or label fixtures honestly. No OAuth or automatic delivery until credentials, consent, token security and scheduling are implemented and tested.

Source briefs are preserved as docs/product/CONSUMER_BRIEF.md and NOTEBOOK_DESIGN.md. The resulting local app is a connected prototype; prior native/live beta requirements are not silently waived.
