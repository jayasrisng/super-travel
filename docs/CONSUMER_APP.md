# Consumer app handoff

Current source: [consumer brief](product/CONSUMER_BRIEF.md), [notebook design](product/NOTEBOOK_DESIGN.md), and [decision register](decisions/DECISIONS.md). This is a working local consumer application, not a private-beta deployment. See README for exact setup and demo/live matrix.

## Shared implemented model

Source definitions: `super_travel/control/schemas.py`, `super_travel/consumer/models.py`; exported wire contract: `packages/contracts/openapi.json`; generated web types: `apps/web/src/api.generated.ts`. Do not create another handwritten shared DTO set. Models reject extra input fields. Defaults must still be handled safely by older/generated clients.

| Model | Scope and invariants |
|---|---|
| Profile | Actor-owned global preferences; initialized once alongside the seed wardrobe. New trip form copies preferences; trip edits do not rewrite the profile. |
| Trip | Owner UUID, destination, optional civil dates, certainty, IANA zone, EUR/USD/JPY currency, counts/child ages, interests, activities, preferences, budget, booking notes, version/context version. Confirmed dates need both endpoints, ordered within 61 days; budget uses trip currency. |
| Participant | Same-trip record, label/category, optional arrival/departure bounded by trip dates. Explicit additions update traveler counts/context. Not an authenticated membership. Reducing counts/removing participants is not implemented; API rejects silent reduction. |
| Segment | Date-bounded destination chapter. Adding it advances context; no transport reservation is inferred. |
| Task | Exact requested editable fields, UUID/trip ownership, creator, version, history and optional run/result. Agent assignment uses all five keys. Deadline may precede trip, but cannot exceed end date. |
| AgentRun | Existing actor-owned durable queue record, nullable trip for standalone use, lease/version/status/proposal/error, context version, 24-hour retention followed by tombstone. |
| ItineraryItem | Civil day/local HH:mm/duration/category and optional same-trip participants. Assigned travelers must be present on the day. Draft apply and manual insertion advance context. |
| SavedExperience | Existing actor-owned Magic bookmark, nullable trip, fixture/live label. Save requires a succeeded, unexpired recommendation from an owned run. |
| WardrobeItem | Global to actor; category/color/image/style/season/warmth/occasions/material/weight/ownership/favorite/availability/version. Thirty-four deterministic actor-specific seeds. Deleting seeds does not recreate them. |
| Outfit | Actor-owned global or trip-specific combination; wardrobe IDs, title/occasion/suitable dates, explanation/score, temperature/source mode, renderer/version. `lookbook` is the only shipped renderer. |
| OutfitVote | Persistent like/dislike per combination, optional trip, previous decision for one-step undo. Ranking rewards favorites and items used in liked combinations; rejected combinations are filtered. |
| PackingItem | Trip/wardrobe link, unique item identity, usage IDs/days, photo/name/category, packed and wear state, manual flag/version. Rebuild deduplicates liked outfit items and preserves explicitly added essentials. |
| CalendarConnection | Actor-owned synthetic-calendar consent/selection and connected/disconnected state. No Google token exists in this adapter. |
| Briefing | Trip/day persisted snapshot of selected schedule, sample weather, outfit and reminders; delivery is `in_app_only`. An outfit requires suitable day plus all pieces packed and ready. |
| Expense | Trip currency, integer minor-unit total, same-trip payer/unique split participants and exact shares. Equal split uses `divmod`; remaining units go to stable sorted participant IDs. No FX, transfers, settlements or refunds. |
| Share | One-day capability, hashed in storage, revocable/versioned. Replay reconstructs token through keyed HMAC rather than retaining plaintext. Public response allowlists itinerary fields and omits participant/trip linkage IDs, tasks, preferences, wardrobe and ledger. |

The generic SQLite object store retains consumer objects under actor/kind with transactions; it is not the reviewed relational/RLS beta schema. Consumer records/photos persist until explicit deletion or local database removal. Jobs and idempotency records retain the existing 24-hour policy. Define account-level deletion/retention/migrations before using real tester accounts.

## API inventory

All routes use `/v1`, `{data, meta}` success and `{error, meta}` failure envelopes. POST domain mutations require UUID `Idempotency-Key`. PATCH/PUT/DELETE versioned records require quoted `If-Match`, unless creating the first calendar connection. Read the relevant record's `version` and refresh on 412; never bypass the conflict. 428 means missing precondition, 409 incompatible context/state, 422 invalid input, 401 missing identity, 403 disallowed demo origin, 404 inaccessible/missing resource. Existing cancellation endpoints keep their own replay/version semantics.

| Route suffix | Method | Purpose |
|---|---|---|
| `/demo/session` | POST / DELETE | Explicit localhost-only signed-cookie demo notebook / clear cookie |
| `/consumer/home` | GET | Trips, current task states, preferences and wardrobe count |
| `/consumer/preferences` | PUT | Versioned global preferences |
| `/consumer/trips` | POST | Trip plus personalized initial tasks and participant labels |
| `/consumer/trips/{trip}` | GET / PUT | Composite notebook / versioned details update |
| `/consumer/trips/{trip}/tasks` | POST | User-authored task |
| `/consumer/trips/{trip}/tasks/{task}` | PATCH / DELETE | Versioned editable fields / delete and cancel attached work |
| `…/tasks/{task}/run` | POST | Existing async run; optional explicit Magic origin/window |
| `…/tasks/{task}/decision` | POST | `complete`, `reopen`, `approve`, `reject`; current version required |
| `/consumer/wardrobe` | GET / POST | Global inventory / create manually tagged piece |
| `/consumer/wardrobe/{item}` | PUT / DELETE | Versioned edit/removal |
| `/consumer/wardrobe/{item}/photo` | POST | Versioned image replacement; ≤2 MB JPEG/PNG/WebP, ≤12M pixels |
| `/consumer/media/{media}` | GET | Owner-authenticated, no-store sanitized JPEG |
| `/consumer/outfits/generate` | POST | Trip or standalone, occasion, manual/sample temperature |
| `/consumer/outfits`, `/consumer/outfits/votes` | GET | Persisted combinations / decisions |
| `/consumer/outfits/{outfit}/vote` | POST / DELETE | Like/dislike / undo last decision |
| `/consumer/trips/{trip}/packing` | POST | Deduplicated rebuild, preserving packed/wear state |
| `/consumer/trips/{trip}/packing/items` | POST | Explicit extra wardrobe piece or essential |
| `/consumer/trips/{trip}/packing/{item}` | PATCH | Versioned packed/wear state |
| `/consumer/calendar` | GET / PUT | Synthetic connection / explicit selection or disconnect |
| `/consumer/trips/{trip}/calendar` | GET | Synthetic events for optional `day` |
| `/consumer/trips/{trip}/briefing` | GET | Persisted current snapshot for optional `day`; pre-trip default is first trip day |
| `/consumer/trips/{trip}/participants` | POST | Partial or full-trip traveler label |
| `/consumer/trips/{trip}/segments` | POST | Date-bounded destination chapter |
| `/consumer/trips/{trip}/itinerary` | POST | Note with optional same-trip/day participant assignment |
| `/consumer/trips/{trip}/expenses` | POST | Exact equal split; no money movement |
| `/consumer/trips/{trip}/shares` | POST | Redacted read-only capability |
| `/consumer/trips/{trip}/shares/{share}` | DELETE | Versioned revocation |
| `/consumer/share/{token}` | GET | Public allowlisted itinerary view; 404 on expiry/revocation |
| `/consumer/providers` | GET | Explicit current integration capabilities |

Original `/agents`, `/agent-runs`, `/magic/runs`, `/trips`, and `/me/saved-experiences` remain available; consumer tasks connect to the same run store, worker and cancellation behavior.

## Task lifecycle and consent

`not_started → queued → agent_working → ready_for_review`, or `needs_more_information`, `failed`, `cancelled`. The contract also reserves `waiting_for_approval` for future consequential actions; this adapter executes no consequential external actions. Required destination/dates or Magic origin/window must be present before work starts.

User edits never come from model output. Editing research instructions, description or assignment detaches/cancels obsolete work. Run inputs are snapshots; subsequent trip changes invalidate application through context-version comparison. Expired runs cannot apply old drafts. Accepting a draft can save itinerary notes; status remains reviewable until the user explicitly reports completion. Reopening and deleting are deterministic user operations. History records runs, transitions and decisions.

No `/chat` consumer endpoint or persistent AI conversation was added. The CLI orchestrator remains preserved; structured single-task runs are the consumer boundary.

## Outfit and packing trade-offs

The shipped generator is a deterministic capsule heuristic, not an AI stylist or optimization solver. It checks ready clothing, per-trip wear state, occasion tags, warmth for cold input and color compatibility; favorites/previous likes affect ranking. Suitable dates are suggestions across the trip, not confirmed appointments or outfit bookings. Occasion and expected temperature are manually supplied. Live destination weather, automatic event-to-outfit inference, advanced layers and explicit day-by-day assignments remain upgrades.

Packing counts unique wardrobe IDs rather than outfit rows. Likes remain reusable global preferences or belong to a specific trip. Standalone likes do not silently populate a trip. Need-to-buy pieces and removed items produce warnings; no shopping transaction is executed. During-trip saved looks warn about missing/unpacked/worn/dirty/unavailable garments; the morning note only recommends fully ready packed items.

The wardrobe render boundary is `renderer=lookbook` with `item_ids` and wardrobe media. Swap in a layered renderer through that boundary later without inventing virtual try-on claims. Original assets are generated by `scripts/build_wardrobe_assets.py`; manual photos are always owner-scoped.

## Integration boundaries

`ExploreAgent` already consumes `DiscoveryProvider` candidates with provenance, route/hour/cost semantics and partial-outage handling. `consumer/providers` defines event/calendar/weather interfaces. The four named event providers explicitly fail unconfigured, rather than inventing network responses. The fixture adapter generates illustrative coordinates near the entered origin globally; the previously selected Barcelona live launch area is still a separate release gate.

Google OAuth is not wired and no tokens are fetched/stored. A future adapter must use read-only scopes, selected calendars/events, encrypted backend tokens, authorized refresh, disconnection/revocation, expiry/missing-permission error states, consent and provider contract tests. The frontend must keep demo/live provenance visible. Calendar selections must never classify every personal event as travel.

No real provider credentials were used during validation. Before live use, obtain permission for the relevant API, check license/retention rules and enable explicit cost ceilings and kill switches.

## Release limitations

Local demo authentication, generic SQLite records and thread workers are unsuitable for public/private-beta account data. Native SwiftUI/WidgetKit, authenticated collaboration/invitations, participant removal/editing, itinerary/segment editing, custom weighted expense splits, automatic notification delivery, recognition/try-on, live calendar/weather/discovery and transaction execution remain incomplete. Nothing in the generated API or UI describes those as shipped.

Tests cover the complete local journey, owner/trip isolation, cancellation/edit preservation, stale/expired draft rejection, exact splits, partial dates, manual packing, deduplication/wear state, photo metadata stripping, guest redaction/hash-only storage/revocation/expiry, calendar selection/disconnect and explicit provider failures. Browser tests cover controls, touch/mouse/keyboard, refresh, states, mobile overflow and selected-page automated accessibility. This is evidence for the local prototype, not a full device/screen-reader or live-beta certification.
