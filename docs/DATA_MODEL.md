# Wonder shared data model v1

> Current consumer supplement: [CONSUMER_APP.md](CONSUMER_APP.md). Checked OpenAPI defines implemented local routes. Latest consumer scope supersedes older Magic-first/website ownership; production beta gates below remain separate.


Status: normative proposed contract; implementation and SQL migrations follow Phase 0 review. Entity names here are logical; SQL uses plural snake_case in the private `app` schema. Full vision entities are not all first-beta tables. Read [architecture](../ARCHITECTURE.md) and [API](api/CONTRACTS.md) together.

## Shared primitives

- IDs: UUID strings; guest participants also receive UUIDs. Never use emails as keys.
- Audit timestamps: UTC RFC3339; SQL `timestamptz`. Civil dates: `YYYY-MM-DD`, SQL `date`. Timezone: IANA name, Barcelona `Europe/Madrid`. Local dates cannot be inferred by slicing UTC timestamps. DST ambiguity needs an explicit offset validated against zone.
- Money: `{amount_minor: integer, currency: ISO-4217 string}`. Use currency exponent metadata; EUR/USD two digits, JPY zero. No floats. Nonnegative amounts unless a record explicitly represents an adjustment. API integer amounts restricted to safe JSON integer range; SQL bigint and checked limits. MVP trip ledger has one currency; no hidden FX conversion.
- Mutable aggregates: `id`, `created_at`, `updated_at`, `version` (positive integer). Trip-owned rows include `trip_id`, including association rows. Immutable rows retain timestamp and actor without editable versions.
- Location: WGS84 latitude [-90,90], longitude [-180,180]; optional display label. Exact Magic origin is ephemeral, never an analytics identifier.
- Provenance: `provider`, `source_url`, `provider_id?`, `observed_at`, `expires_at?`, `data_mode: live|fixture|manual`, `availability: verified|unverified|unavailable|not_applicable`, `cost_status: verified|estimated|unknown`. “Live” does not itself mean availability verified.

## Identity, context and access

| Entity / stage | Fields and relationships | Constraints |
|---|---|---|
| UserProfile / Magic beta | `id` = Auth subject, display_name, locale, timezone | account-owned; no credentials in domain DB |
| UserPreferences / Magic beta | user_id, interests[], dietary_tags[], accessibility_tags[], version | explicitly optional; never infer identity from template |
| AgentRun / Magic beta | actor_user_id, trip_id nullable, agent, status, input_hash, context_version nullable, started_at, completed_at, expires_at, proposal, error_code | single-feature runs actor-private; trip runs require membership |
| AgentJob / Magic beta | run_id unique, attempt_count, lease_owner, lease_until, next_attempt_at | durable queue; no plaintext prompts in logs |
| SavedExperience / Magic beta | user_id, recommendation_id, trip_id nullable, title, source reference, minimal permitted display fields | saving is not attendance; unique user + recommendation |
| Trip / connected MVP | title, owner_user_id, start_date, end_date, timezone, currency, budget_minor nullable, traveler_configuration, preferences, status, context_version | inclusive civil-date bounds; start <= end; at least one organizer; personal constraints minimal |
| TripSegment / connected MVP | trip_id, destination_label, timezone, location?, start_date, end_date, sort_order | within trip dates; overlapping segments allowed for different subgroups |
| TripParticipant / connected MVP | trip_id, user_id nullable, display_name, role, status, guest_claimed_at? | role organizer/editor/participant/viewer; status invited/active/removed; unique active user per trip |
| SegmentParticipation / connected MVP | trip_id, segment_id, participant_id, joined_date, left_date | joined <= left within segment; composite same-trip FKs |
| Invitation / connected MVP | trip_id, intended_participant_id, token_hash, expires_at, revoked_at?, claimed_by? | one-time account claim; token raw value never stored |
| GuestSession / connected MVP | invitation_id, token_hash, expires_at, revoked_at | sanitized viewer scope; every read checks trip/share validity |
| ShareSnapshot / connected MVP | trip_id nullable, actor_user_id, scope, allowlisted_payload, token_hash, expires_at, revoked_at | scope itinerary/recap; snapshot never full trip serialization |

Traveler configuration contains template key plus adult/child/infant **counts**, travel purpose and explicitly chosen constraints. It is not a rigid identity classification. User defaults are copied/merged explicitly; trip overrides take precedence. Request overrides affect only that run unless separately saved. Segment attendance and activity participation are separate from access roles.

## Tasks, plans and preparation

| Entity / stage | Fields | Constraints |
|---|---|---|
| ChecklistTask / connected MVP | trip_id, segment_id?, system, title, description?, assigned_participant_id?, status, priority, due_at?, source_kind, source_ref?, template_key? | system plan_book/pack_shop/explore_experience/travel_essentials/manage_recover; status todo/in_progress/done/skipped; unique trip + template_key for seeded tasks |
| ItineraryItem / connected MVP | trip_id, segment_id?, title, starts_at, ends_at, timezone, location?, kind, booking_id?, proposal_item_ref? | starts < ends; must fit segment/trip civil dates; overlaps warn, not universally reject |
| ActivityParticipation / connected MVP | trip_id, itinerary_item_id, participant_id | explicit attendees; same-trip FKs |
| PackingList / connected MVP | trip_id, owner_participant_id nullable, visibility, title | private owner-only or shared; private data excluded from default context |
| PackingItem / connected MVP | trip_id, list_id, title, quantity, category, assigned_participant_id?, packed, purchase_status, proposal_item_ref? | quantity positive integer; purchased does not imply packed; purchase_status not_needed/missing/purchased |
| Booking / connected MVP manual only | trip_id, type, provider_name, external_url?, confirmation_reference?, status, verification_source, verified_at? | status suggested/pending/confirmed/cancelled; reference private; no status inferred from clicks |
| BookingParticipant / connected MVP | trip_id, booking_id, participant_id | composite FKs, unique booking + participant |
| GuidanceReference / connected MVP | task_id, trip_id, jurisdiction, topic, authoritative_url, checked_at, review_due_at, uncertainty | essentials guidance freshness visible; no document scans |
| AuditEvent / both stages | actor_user_id, trip_id nullable, entity_type, entity_id, action, request_id, occurred_at | append-only minimal metadata; no secrets or copies of sensitive fields |

Transport is represented by itinerary `kind=transport` in MVP; dedicated transportation legs wait for disruption integrations. Place/Event/Experience are normalized adapter values, not three large persistent catalogs. Store provider IDs and license-permitted fields only. Shopping links attach to packing proposals; no purchase ledger in MVP.

## Recommendation and proposal values

`Recommendation`: id, title, category, location, rank, reason, `duration_minutes`, route legs with duration/source/observed time, opening/event windows, money estimate nullable, provenance[], feasibility `feasible|infeasible|unknown`, evaluated_at, valid_until, assumptions[], allowed_actions[]. An action is `{type: navigate|external_link|save|add_to_itinerary, url?}`. HTTPS provider URLs are allowlisted; block unsafe schemes/open redirects. A result needs required provenance and feasible time arithmetic before it appears in the primary ranked list. When a budget is specified, primary results also require known total cost within it; unknown-price candidates may appear only in a separate clearly labeled uncertain list.

`PlanProposal`: itinerary_items[], checklist_tasks[], budget_estimates[], assumptions[], sources[]. `PackProposal`: packing_lists[], checklist_tasks[], assumptions[], sources[]. `ExploreProposal`: recommendations[], warnings[], coverage. Every proposed item has an opaque item_id unique within run. Proposal items are not persisted domain records until explicitly applied. Plan/pack outputs never pretend to be booked. Magic output must distinguish place hours from reservable availability.

## Ledger: deterministic and auditable

| Entity | Fields | Constraints |
|---|---|---|
| Expense | trip_id, created_by, description, payer_participant_id, amount_minor, currency, split_method, status, version | positive amount, same trip currency; method equal/custom; status active/voided |
| ExpenseSplit | trip_id, expense_id, participant_id, owed_minor | unique expense+participant; >=0; total equals expense amount, transactionally |
| Refund | trip_id, expense_id, received_by_participant_id, amount_minor, reason, occurred_at | received_by must be original payer in MVP; total refunds <= expense amount |
| RefundAllocation | trip_id, refund_id, participant_id, credited_minor | same original split participants; sum equals refund amount; cumulative credits <= original owed |
| Settlement | trip_id, from_participant_id, to_participant_id, amount_minor, currency, status, recorded_by | manual attestation only; different participants, positive amount; status recorded/voided |

Participant can create an expense paid by themselves; only creator can edit/void their own unless organizer/editor. After any refund, freeze expense amount/payer/splits; corrections require an explicit void-and-recreate workflow reviewed for refund preservation. Reject voiding a refunded expense in MVP (`refunded_expense_locked`); preserve its ledger/refunds and use a separately reviewed adjustment workflow later. Settlements do not automatically close an expense. Balance is derived from active ledger rows; never store a mutable “amount owed” total or use AI math. Edits recompute splits atomically and retain audit metadata.

Equal split: integer division by n; distribute residual units in stable ascending participant-ID order. Example EUR 10.00 among 3 gives 334,333,333 cents in that order. Custom split: reject if any negative share or total differs. Payer need not be an attendee. Record refund allocations explicitly, with default proportional allocation by original shares using largest remainder and participant-ID tie-breaking. Adjust final allocations to honor remaining per-participant refundable limits. User reviews allocations before recording.

For each participant, balance = payments they funded − allocated expense shares − refunds they received + refund credits + settlements they sent − settlements they received. Positive means owed money; negative means owes money. Per-trip balances sum to zero. Example A pays 1000 split A/B 500 each; A receives 200 refund with 100 credits each: A +400, B −400. B records 400 to A: both zero. Voiding a settlement reverses its contribution; no money is actually moved.

No account deletion cascades silently through money history. Removed participants retain tombstone identity for ledger references; membership/access is revoked immediately. Trip deletion needs explicit retention/export policy and revokes access before background purge.

## Passport and future entities

`CompletedExperience` (connected MVP): user_id, trip_id nullable, saved_experience_id nullable, occurred_on, destination, user_confirmed_at, visibility private/group. Explicit user confirmation is required; planned/booked/completed-trip status alone cannot establish attendance. Basic Passport is a derived view over confirmed visits. Opt-in recap uses a redacted ShareSnapshot.

Later: TravelMemory media, ShareableRecap customization, notifications/push subscriptions, advanced splits/FX, merchant offers, purchase references, actual payment events, flight monitoring and dedicated transport legs. Do not create empty speculative tables just because the vision names them.

## Persistence requirements

Composite unique `(trip_id,id)` plus composite foreign keys enforce same-trip ownership for segment/participant/task/booking/expense associations; authorization checks still required. Financial constraints require a deferred constraint trigger or service transaction plus DB-enforced checks demonstrated against direct writes by runtime role. Index trip_id + sort/time for task/itinerary queries, user_id memberships, unique token hashes, job status + next_attempt_at, and run actor + created_at. Bound JSON fields and validate them; do not hide core relationships in JSON.

Migration acceptance: build from an empty database; enforce runtime-role RLS; preserve an older client fixture; test cross-trip associations, removal, last-organizer prevention, integer rounding, refunds/voids and worker lease replay. SQL schema is not implemented in this planning change.
