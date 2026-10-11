# Wonder — three-agent dashboard handoff

Scope: shared product/API specification for the teammate building the website and D5 building native iOS. No website implementation or alternate frontend is included. Implemented route schemas come from [checked OpenAPI](../packages/contracts/openapi.json) and [CONTROL_API.md](CONTROL_API.md). [CONTRACTS.md](api/CONTRACTS.md) and [DATA_MODEL.md](DATA_MODEL.md) govern remaining beta domains. Preserve the owner's Magic-first Barcelona direction.

## Three workspaces, one trip context

| Workspace | API agent key | Inputs | Structured result / next action |
|---|---|---|---|
| Explore & Experience / Magic (default) | `explore_magic` | origin, available time, interests, EUR budget, walk/transit, next commitment, buffer | ranked feasible candidates, sources, freshness, costs/uncertainty; save, navigate or reviewed itinerary add |
| Plan & Book | `plan_book` | destination/dates, traveler configuration, budget, interests, constraints | itinerary proposal, checklist tasks, budget estimates and sources; select items and explicitly apply |
| Pack & Shop | `pack_shop` | destination/dates, traveler needs, activities, baggage mode; weather when sourced | categorized packing proposal, preparation tasks and missing items; explicitly create list, then separately track packed/purchased |

Magic may run without a trip. Standalone Plan/Pack asks only fields needed for that feature. Trip-scoped requests use an authorized server snapshot; do not send an entire private trip from the client or create separate agent-owned copies. D1 defines the translation between prototype `planning/packing/explore` names and these v1 keys.

## Dashboard data and interaction responsibilities

Show active trip or standalone mode, its destination/date/timezone and relevant minimal preferences. Three agent entry points lead to independent inputs but share authoritative trip context. A trip switch must discard incompatible in-flight views and refetch permitted state; no results, expenses or packing items leak across trips.

For each agent show idle, submitting, queued/running, succeeded, failed/cancelled/expired. During a run, describe actual server status; do not invent percentages or completed steps. On success show typed results and explicit sample/manual/live/estimated/verified labels. Agent runtime readiness is based on real supported capability/configuration, not a static “online” dot. Plan/Pack now return fixture proposals or model drafts when enabled; show synthetic versus model-generated/unverified clearly. Live Magic provider access remains pending.

Recent runs are actor-scoped and display agent, trip/standalone scope, status, creation time and expiry. No prompts or sensitive traveler details appear in public summaries. Reopen only authorized unexpired results. Quota/auth/provider failures display stable error code, retry guidance and fallback. No raw provider errors or credentials.

Magic result cards include total time assumptions (outbound/activity/onward/buffer), price certainty, opening/event certainty, source and observed time. At most five primary results; unknown hours/routes/required cost go in a separate uncertain section only if requested. Booking availability is distinct from opening hours. An empty result is a legitimate outcome, not permission to fabricate a venue.

Packing completion is separate from checklist completion and purchase state. Planning acceptance selects explicit proposal item IDs. Never treat a recommendation, outbound click, share or booked item as confirmed attendance/payment. Guest viewers cannot run agents or apply changes under the beta contracts.

## API handoff sequence

1. POST `/v1/magic/runs` with MagicRequest for Magic; POST `/v1/agent-runs` with discriminated AgentRequest for Plan/Pack. User token + Idempotency-Key required.
2. 202 returns the AgentRun envelope; poll GET `/v1/agent-runs/{run_id}` with backoff until terminal status. Cancel through the reviewed cancel endpoint, not by deleting server data.
3. Render the validated PlanProposal, PackProposal or ExploreProposal. A successful HTTP response is not itself a booking/purchase or completed provider action.
4. Save a Magic recommendation through POST `/v1/me/saved-experiences`; navigate via an allowlisted external action. Revalidate expired candidate data before save/application.
5. For authorized trip editing, POST `/v1/trips/{trip_id}/agent-runs/{run_id}/apply` with selected IDs, expected context version and explicit confirmation. Handle 409 stale context with regeneration; preserve manual edits.
6. Checklist and packing mutations use domain endpoints with ETag/If-Match. The client never writes domain tables directly or calculates authoritative finance/permission logic.

Steps 1–4 (except external navigation) are implemented in the local control backend. Steps 5–6 remain planned domain services; do not offer a working apply action yet. Checked OpenAPI and synthetic fixtures are available now; client owners generate TypeScript/Swift clients from that artifact. Local token authentication is not beta identity. Keep any UI presentation fixture separate from authoritative API DTOs. No duplicate Next.js agent backend or browser model calls.

## Backend deliverable checklist for D1

- Completed: three proposal engines and the five-name registry, preserving Essentials/Recovery modules.
- Completed: strict schemas, scoped context, synthetic fixtures and artifact drift checks.
- Completed: create/poll/list/cancel/results and private Magic bookmarks. Next: reviewed domain apply.
- Provide canonical success/empty/uncertain/error/replay/stale-context fixtures so web and Swift build independently.
- Define live Barcelona source/routing access, expiry, quota/cost limit and provider isolation; treat third-party content as untrusted.
- Preserve proposal-only behavior for consequential actions; no direct bookings, purchases, cancellations or communications.

## Acceptance for the teammate's dashboard

Run one Barcelona Magic request end to end and demonstrate source/uncertainty/time arithmetic. Web and native iOS decode identical DTOs and share saved state once auth/persistence exist. Plan and Pack must either work against real typed agent output or be visibly unavailable/sample mode. Validate empty/failure/expiry, denied location/manual origin, cancellation, stale results, trip switching and explicit apply. Use accessible controls and keyboard/device interaction. This task supplies the handoff, not a competing website or a claim that beta parity exists today.
