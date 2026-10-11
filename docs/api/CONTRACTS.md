# Wonder API contracts v1

Implementation boundary: [CONTROL_API.md](../CONTROL_API.md) and [checked OpenAPI](../../packages/contracts/openapi.json) describe the implemented local subset and deliberate staging differences. The remaining operations below are beta design, not working endpoints.

Status: normative proposed wire specification for contract review before implementation. No endpoints exist yet. Phase 0 must produce `packages/contracts/openapi.json` (OpenAPI 3.1) and checked TypeScript/Swift clients from these operations, including examples and rejection fixtures. Do not let generated FastAPI defaults silently redefine this spec.

## Protocol

Base `/v1`; JSON snake_case fields; UTF-8; UUID IDs, RFC3339 UTC instants, ISO dates, IANA zones, integer money as defined in [data model](../DATA_MODEL.md). User routes require `Authorization: Bearer <Supabase JWT>`. Share and invitation routes use explicitly limited capability tokens; they never accept an unverified trip ID as authority. Beta Magic is authenticated and invite-only, not an anonymous unlimited AI endpoint.

Success entity: `{data: <entity>, meta: {request_id}}`; list: `{data: [...], meta: {request_id, next_cursor: string|null}}`; cursor pagination `limit` 1–100, default 20, stable sort by created_at/id. Errors: `{error: {code, message, details: [{field, reason}], retryable}, meta: {request_id}}`. Never leak provider credentials or stack traces.

HTTP statuses: 200 reads/updates; 201 created resources plus Location; 202 queued run; 204 deletion/revocation where specified; 400 malformed request; 401 invalid/expired identity; 403 known actor lacks permission; 404 absent **or inaccessible trip/resource** to prevent enumeration; 409 stale context/idempotency/state conflict; 412 stale ETag; 422 invalid fields; 429 quota + Retry-After; 503 unavailable dependency. Error code is stable, human message may be localized.

Reads/mutations of versioned resources return `ETag: "<version>"`. PATCH/DELETE/revoke operations require `If-Match` for the resource; absent is 428. Trip-derived agent apply additionally checks context_version. PATCH accepts only documented fields, rejects unknowns, distinguishes omitted (unchanged) from null (clear nullable field). Client cannot set owner, actor, trip_id on child updates, rank verification or booking confirmation evidence automatically.

Creation/action POSTs require `Idempotency-Key` UUID. Store actor+route+key+canonical input hash and response transactionally for 24h. Replay same input returns original status/body/Location; different input returns 409 `idempotency_conflict`. Keys scoped to token session for guest actions. On timeouts clients retry same key; database uniqueness of accepted proposal items prevents duplicate apply beyond key retention. GET/PUT semantics do not spend new AI runs.

## Operation inventory

All IDs below are UUID except opaque share/invite tokens. All nested resource routes verify parent and child match. “Participant” refers to an authenticated active participant unless explicitly guest.

| Phase / owner | Method and path | Request → response / permissions |
|---|---|---|
| Magic / D1 | GET `/me` | UserProfile; authenticated |
| Magic / D1 | GET, PATCH `/me/preferences` | PreferencesPatch → UserPreferences; own account |
| Magic / D1 | POST `/magic/runs` | MagicRequest → AgentRun (202); own context, optional trip membership |
| Magic / D1 | GET `/agent-runs/{run_id}` | AgentRun with proposal when ready; actor only, plus current trip access if scoped |
| Magic / D1 | POST `/agent-runs/{run_id}/cancel` | `{}` → AgentRun; actor; ETag required |
| Magic / D1 | GET, POST `/me/saved-experiences` | SaveRequest `{run_id,recommendation_id}` → SavedExperience (201); actor run, unexpired result |
| Magic / D1 | DELETE `/me/saved-experiences/{saved_id}` | 204; own resource, ETag |
| Magic / D1 | DELETE `/me` | deletion request (202); reauthentication, revokes shares/sessions |
| Magic / D1 | GET `/me/export` | own redacted export payload; no tokens |
| Trips / D1 | GET, POST `/trips` | TripCreate → Trip (201); list active membership |
| Trips / D1 | GET, PATCH `/trips/{trip_id}` | TripPatch → Trip; organizer/editor edits; read permitted view |
| Trips / D1 | DELETE `/trips/{trip_id}` | 202 purge request; organizer, ETag, explicit confirm |
| Trips / D1 | GET, POST `/trips/{trip_id}/segments` | SegmentCreate → TripSegment; organizer/editor |
| Trips / D1 | PATCH, DELETE `/trips/{trip_id}/segments/{segment_id}` | SegmentPatch / 204; reject deletion with linked items until resolved |
| Tasks / D3 | GET, POST `/trips/{trip_id}/tasks` | TaskCreate → ChecklistTask; editor creates |
| Tasks / D3 | PATCH `/trips/{trip_id}/tasks/{task_id}` | TaskPatch → ChecklistTask; editor edits, participant assigned status only |
| Plans / D1 | GET, POST `/trips/{trip_id}/itinerary-items` | ItineraryCreate → ItineraryItem; editor writes |
| Plans / D1 | PATCH, DELETE `/trips/{trip_id}/itinerary-items/{item_id}` | ItineraryPatch / 204; editor |
| Packing / D3 | GET, POST `/trips/{trip_id}/packing-lists` | PackingListCreate → PackingList; editor shared or participant own private |
| Packing / D3 | GET, POST `/trips/{trip_id}/packing-lists/{list_id}/items` | PackingItemCreate → PackingItem; list owner/editor subject to visibility |
| Packing / D3 | PATCH `/trips/{trip_id}/packing-lists/{list_id}/items/{item_id}` | PackingItemPatch → PackingItem; own/assigned packed flag, editor shared changes |
| Agents / D1 | POST `/agent-runs` | AgentRequest → AgentRun (202); plan_book/pack_shop/explore_magic, own or authorized trip |
| Agents / D1 | POST `/trips/{trip_id}/agent-runs/{run_id}/apply` | ApplyRequest → AppliedProposal (200); editor, current context |
| Group / D2 | GET, POST `/trips/{trip_id}/participants` | ParticipantCreate → TripParticipant; organizer/editor create guest representation |
| Group / D2 | PATCH `/trips/{trip_id}/participants/{participant_id}` | ParticipantPatch; organizer roles/removal, editor display/attendance only |
| Group / D2 | PUT `/trips/{trip_id}/participants/{participant_id}/segments/{segment_id}` | `{joined_date,left_date}` → SegmentParticipation; editor, ETag on existing association |
| Group / D2 | POST `/trips/{trip_id}/invitations` | `{participant_id,expires_in_days}` → InvitationIssued; organizer, max 7 days |
| Group / D2 | POST `/invitations/{token}/guest-session` | `{}` → sanitized guest access (201); valid unrevoked invite |
| Group / D2 | POST `/invitations/{token}/claim` | `{}` → TripParticipant; authenticated one-time claim |
| Group / D2 | POST `/trips/{trip_id}/invitations/{invitation_id}/revoke` | `{}` → Invitation; organizer, ETag; revokes derived guest access |
| Sharing / D2 | POST `/trips/{trip_id}/shares` | `{scope,selected_item_ids,expires_in_days}` → ShareIssued; organizer/editor, explicit opt-in |
| Sharing / D2 | GET `/shares/{token}` | RedactedShare; valid capability only; no ledger, live location or child details |
| Sharing / D2 | POST `/trips/{trip_id}/shares/{share_id}/revoke` | `{}` → ShareSnapshot metadata; issuer/organizer, ETag |
| Finance / D3 | GET, POST `/trips/{trip_id}/expenses` | ExpenseCreate → Expense; editor or participant paid-by-self |
| Finance / D3 | PATCH `/trips/{trip_id}/expenses/{expense_id}` | ExpensePatch → Expense; creator/editor, no editing refunded allocation |
| Finance / D3 | POST `/trips/{trip_id}/expenses/{expense_id}/void` | `{reason}` → Expense; creator/editor, explicit confirm, ETag; reject refunded expenses |
| Finance / D3 | POST `/trips/{trip_id}/expenses/{expense_id}/refunds` | RefundCreate → Refund; editor or original payer |
| Finance / D3 | GET `/trips/{trip_id}/balances` | `{currency,balances:[{participant_id,amount_minor}]}`; editor all, participants own involved view |
| Finance / D3 | POST `/trips/{trip_id}/settlements` | SettlementCreate → Settlement; editor or sending participant; manual attestation |
| Finance / D3 | POST `/trips/{trip_id}/settlements/{settlement_id}/void` | `{reason}` → Settlement; creator/editor, ETag |
| Essentials / D3 | GET `/trips/{trip_id}/guidance` | GuidanceReference[]; membership with appropriate redaction |
| Essentials / D3 | POST `/trips/{trip_id}/recovery-tasks` | `{trigger,description,source_url?}` → ChecklistTask; editor/manual only |
| Bookings / D1 | GET, POST `/trips/{trip_id}/bookings` | BookingCreate → Booking; editor, manual evidence only |
| Bookings / D1 | PATCH `/trips/{trip_id}/bookings/{booking_id}` | BookingPatch → Booking; editor, confirmation evidence explicit |
| Passport / D3 | GET `/me/passport` | `{confirmed_visits,counts}`; account-owned derived view |
| Passport / D3 | POST `/me/completed-experiences` | `{saved_experience_id?,trip_id?,destination,occurred_on,user_confirmed:true}` → CompletedExperience |
| Summary / D3 | GET `/trips/{trip_id}/summary` | role-redacted counts, next_task, next_commitment, updated_at, context_version |

Guest sessions use a distinct `Authorization: Guest <opaque_token>` scheme, accepted only by dedicated GET `/guest/trips/{trip_id}/summary` and GET `/guest/trips/{trip_id}/itinerary` routes. They cannot call ordinary authenticated trip routes or mutate domain data. Invitation acceptance and public share creation are not automatic email/iMessage sending. Clients present links and system share UI; the user chooses delivery.

No unimplemented route returns “success”. Unsupported capabilities use explicit errors or do not appear in generated clients until their phase ships. Maintain additive v1 evolution; breaking changes require v2, deprecation plan and older-iOS compatibility tests.

## Request schemas

Required fields are marked **required**; others omitted by default. Bounds are contract requirements, not merely UI hints.

- `PreferencesPatch`: optional interests (max 20 tags), dietary/accessibility tags (max 20 each), locale, timezone. User-controlled tags, no demographic inference.
- `MagicRequest`: **location**, **available_minutes** (15–480), **interests** (0–20), optional `budget` Money, `trip_id`, `next_commitment:{starts_at,location}`, `travel_mode:walk|transit` (default walk), `buffer_minutes` (0–60, default 15), `timezone` (default Europe/Madrid in launch coverage), `allow_unknown_feasibility` (default false). Server computes starts_at from received time, not an arbitrary client clock. Coverage validates origin and candidates against a configured Barcelona boundary polygon; polygon selection is a Phase 0 product review. Outside coverage returns 422 `unsupported_area`. Currency EUR for first-area Magic; no hidden FX. At most five primary results. Known total cost must fit a supplied budget; unknown costs appear only in the uncertain list when allowed.
- `AgentRequest`: **agent** enum plan_book/pack_shop/explore_magic, `trip_id` nullable, **input** discriminated by agent. Plan input requires destination, dates, traveler counts, interests, optional budget for single mode; pack input requires destination, dates, traveler counts, activities[], baggage_mode. In trip mode snapshot supplies those fields; explicit overrides are shown in assumptions. Explore input is MagicRequest. Request must fit 32 KiB and reject unsupported fields.
- `TripCreate`: **title** (1–120), **start_date**, **end_date**, **timezone**, **currency**, **traveler_configuration**; preferences default empty, budget_minor nullable. Organizer created server-side. `TripPatch` allows those fields plus status planned/ongoing/completed/archived, never owner. Completion does not mark visits.
- `SegmentCreate/Patch`: destination_label, timezone, dates, location?, sort_order; create requires destination/timezone/dates.
- `TaskCreate/Patch`: title, description?, system, assigned_participant_id?, priority low/normal/high, due_at?, status; create requires title/system, status default todo.
- `ItineraryCreate/Patch`: title, starts_at, ends_at, timezone, kind activity/transport/stay/commitment, location?, segment_id?, participant_ids[]. Create requires title/times/zone/kind; server computes overlap warnings.
- `PackingListCreate`: title, visibility private/shared, owner_participant_id (required for private). `PackingItemCreate/Patch`: title, quantity (1–1000), category, assigned_participant_id?, packed default false, purchase_status default not_needed.
- `ParticipantCreate`: display_name, role participant/viewer, optional segment_participations[]. No direct account binding; use invitation claim. `ParticipantPatch`: display_name, role, status active/removed; promote role organizer/editor only by organizer, reject removing last organizer.
- `ApplyRequest`: **selected_item_ids** (unique nonempty list), **expected_context_version**, explicit `confirm:true`. Proposal output can only create allowed task/itinerary/packing records. Explore apply creates selected itinerary items only when proposed scheduling fits; otherwise use save or manual itinerary entry.
- `ExpenseCreate`: **description**, **payer_participant_id**, **amount** Money, **split_method** equal/custom, **participant_ids** unique nonempty; custom also **splits:[{participant_id,owed_minor}]** exactly matches participants. `ExpensePatch` allows description/amount/payer/split fields with full recalculation if any split input changes; status uses void action only.
- `RefundCreate`: **amount_minor**, **received_by_participant_id**, **allocations:[{participant_id,credited_minor}]**, reason?, occurred_at. Amount and allocations explicitly reviewed; server validates remaining limits.
- `SettlementCreate`: **from_participant_id**, **to_participant_id**, **amount** Money, **attested:true**; manual record, not a provider payment.
- `BookingCreate/Patch`: type flight/stay/experience/transport, provider_name, external_url?, status, confirmation_reference?, verification_source manual, verified_at?; confirmed requires explicit manual confirmation assertion and verified_at. Sensitive reference excluded from share and viewer DTOs.

## Run/result schemas

`AgentRun`: id, actor_user_id (self responses only), trip_id nullable, agent, status queued/running/succeeded/failed/cancelled/expired, context_version nullable, version, created_at, expires_at, proposal nullable (typed PlanProposal/PackProposal/ExploreProposal), error nullable `{code,message,retryable}`. Terminal status never returns to running. `expired` represents proposal no longer usable. Poll 1 second initially, exponential backoff to 10 seconds, stop at terminal status or foreground interruption. Display a retry action for failed runs; retries create a new run/key.

`ExploreProposal` and recommendation fields are fully enumerated in [DATA_MODEL.md](../DATA_MODEL.md). Route duration is in minutes and source-tagged; recommendation includes outbound and onward durations, activity duration, buffer and remaining slack. `coverage:{area:"barcelona",data_mode,providers,partial}` and warnings identify unsupported category/feed outages. Empty results are a successful outcome with explanation, not fabricated recommendations. Recommendation valid_until is at most 15 minutes after evaluation, shortened by provider expiry/event bounds; rerun/revalidate after expiration. Run retention may be 24 hours but does not extend candidate validity. Ranked primary results must be feasible and fit any supplied budget with known cost. Unknown results, if allowed, appear in a separate `uncertain_recommendations` list with visible limitations.

`AppliedProposal`: run_id, trip_id, created_tasks[], created_itinerary_items[], created_packing_lists[], created_packing_items[], context_version, warnings[]. `TripContext` is internal, never a public full-snapshot endpoint.

## Examples and contract fixtures

Magic beta request (synthetic location; no real user's coordinates):

```json
{
  "location":{"latitude":41.3874,"longitude":2.1686},
  "available_minutes":90,
  "interests":["art","vegetarian_food"],
  "budget":{"amount_minor":4000,"currency":"EUR"},
  "travel_mode":"walk",
  "buffer_minutes":15,
  "timezone":"Europe/Madrid",
  "allow_unknown_feasibility":false
}
```

202 envelope:

```json
{"data":{"id":"00000000-0000-4000-8000-000000000001","actor_user_id":"00000000-0000-4000-8000-000000000002","trip_id":null,"agent":"explore_magic","status":"queued","context_version":null,"version":1,"created_at":"2026-10-11T16:00:00Z","expires_at":"2026-10-12T16:00:00Z","proposal":null,"error":null},"meta":{"request_id":"synthetic-request"}}
```

Feasibility fixture: 90-minute window, outbound 10, activity 35, onward 20, buffer 15 gives slack 10 → feasible **only if** known hours/event bounds cover the planned visit. A 55-minute activity gives slack −10 → infeasible. If onward route is unknown with a next commitment, outcome unknown. Without a next commitment, onward travel may be omitted only as an explicit “no return requirement” assumption; available time means time to activity completion.

Stale apply response:

```json
{"error":{"code":"stale_context","message":"Trip changed; generate a fresh proposal.","details":[{"field":"expected_context_version","reason":"version_mismatch"}],"retryable":false},"meta":{"request_id":"synthetic-request"}}
```

Phase 0 fixtures must cover success, empty results, partial provider failure, fixture labeling, outside Barcelona, unknown hours, budget unknown, daylight-saving transitions, expired/revoked access, wrong trip child ID, idempotent replay/conflict, stale ETag/context, packing privacy, three-way rounding, refund caps, settlement void and older mobile DTO decoding. Web/iOS build against the same fixtures while backend implementation proceeds.

## Optional sponsor operations

The normalized partner interfaces and optional capability-search, outcome and communication draft/send/status operations are specified in [HACKATHON_INTEGRATIONS.md](../HACKATHON_INTEGRATIONS.md). They use these same identity, error, ETag/idempotency and privacy rules. Enable individually after checked schemas and live proof; no arbitrary provider access or outbound messages from a search match.
