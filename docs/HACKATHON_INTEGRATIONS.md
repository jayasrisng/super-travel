# Wonder — SpeedHacks integration and demo plan

Verified October 11, 2026 from the user's signed-in dashboard and official public builder guide. **SpeedHacks: The Official speedrun Hackathon #SFTechWeek**. This document plans integrations; none have been implemented, registered or tested by this change.

## Event constraints

Deadline: **October 11, 2026, 5:00 PM PDT**. Begin submission preparation at 4:00 PM. Submit project details, accurate team/technology list, judge-accessible source link, and a video no longer than five minutes; saving a draft/recording is insufficient. New work must be built during event hours. Mark mocks and support time-saved claims. [Official rules](https://hackersquad.io/events/speedhacks-oct11/resources?tab=rules)

Scoring: impact/time saved 40%, execution 25%, market/path 15%, originality 10%, product/demo 10%. Partners are optional for overall scoring; separate awards recognize meaningful use. [Judging guide](https://hackersquad.io/events/speedhacks-oct11/resources?tab=submission)

The dashboard prize pane said no announced prizes while the guide lists awards; confirm details with organizers if needed. Do not assume dashboard points or tool count replace the judging rubric. Planning/commit provenance is recorded in PLAN; no claim of organizer-approved eligibility is made.

## Integration choices

The owner wants as much integration as possible. Target all five in one coherent workflow, with each contribution observable and isolated behind an adapter. Core Magic feasibility remains deterministic. A sponsor tool is not automatically a POI feed, confirmed reservation source or travel partner.

| Partner / owner | Proposed Wonder use and boundary | Required proof / fallback |
|---|---|---|
| Alike / D1 coordinates, all developers use | development coordination: preserve API decisions and retrieve context in the next coding session; does not receive traveler runtime data | retrieve a prior decision in a fresh authorized session; markdown/Git stays authoritative |
| Darwin / D1 | backend capability discovery for an unmet Barcelona request, show match readiness and explain useful next step; approved read-only specialist adapter if available | live search + correct needs-input/no-match/readiness + verified selected-provider reply or explicit handoff; curated POIs/routes remain core fallback |
| Keewano / D3 | opted-in recommendation outcomes form ordered event history; query recent rejected categories and adapt follow-up candidate selection | live query changes follow-up suggestions; deterministic preferences fallback if stale/unavailable |
| Dial / D2 | user explicitly sends a selected redacted activity card/link to a consenting test recipient; later inbound replies can become proposed preference updates | provider receipt/status shows real test delivery; native share sheet fallback; never autonomous mass messaging or venue calls |
| Sparta / D3 | agent evaluation using a supported test world to assert requested state changes and reject unauthorized actions, tied to Wonder action boundary | run scenario and show world state/evaluation; Pytest boundary fixtures fallback; do not call it production provider execution |

Alike's documented use is coding-session context, not consumer travel recommendations. Setup/session capture needs privacy review and each developer's own authorization; do not install or upload transcripts during a planning-only task. [Alike documentation](https://alike.help/)

Darwin Search supports `POST /api/v3/search`. Handle its response states and connection readiness; Search does not execute a provider. Act is a separately gated beta with pilot credentials and pending approval/payment states; default disabled for Wonder. Do not auto-connect arbitrary returned MCP endpoints; allowlist vetted providers and enforce egress/SSRF protections. [Darwin SpeedHacks guide](https://darwin.so/docs/speedhacks)

Keewano qualification requires event queries that affect the application, rather than unused storage. Its quickstart warns new events take about five minutes to become queryable. Seed synthetic demonstration outcomes early; show freshness and distinguish seeded vs observed events. Keep ordered consumer feedback pseudonymous; no exact coordinates, private trip text or financial/health fields. [Keewano quickstart](https://docs.keewano.com/getting-started/speedhacks-quickstart)

Dial documents SMS, voice calls and inbound messaging through APIs/SDKs. Start with explicit SMS sharing to a controlled test number; Barcelona/EU reach, number availability, permissions and rates are unverified and must be checked before enabling. WhatsApp and voice are separate optional spikes, not promised first-beta capabilities. [Dial docs](https://docs.getdial.ai/documentation/get-started/introduction)

Sparta's dashboard description covers testing worlds; the linked agent guide and rubric were not readable as substantive content through web retrieval. Verify supported worlds/setup/assertions with the resource documents or onsite representative before selecting a concrete scenario. No invented Sparta endpoint or claimed custom Wonder world support. [Official resource index](https://hackersquad.io/events/speedhacks-oct11/resources?tab=resources)

## Runtime/data contracts for sponsor adapters

`CapabilityDiscoveryProvider.search(task, redacted_context)` returns status matches/needs_input/no_match/unavailable, question?, reason?, matches[{external_id, name, reasons[], uncertainties[], readiness, required_setup, connection_methods[], revision?}]. Keep match ordering distinct from Wonder's POI ranking. Only actual attributed provider replies may become normalized activity candidates.

`OutcomeHistoryProvider.record(event)` and `.recent_categories(subject_id, window)` return typed counts/history, observed_at and completeness. Event fields: event_id UUID, pseudonymous subject UUID, occurred_at, type suggestion_shown/suggestion_saved/suggestion_rejected/action_opened, category, run_id opaque. Keewano wire mappings must be validated from official SDK before implementation; this normalized contract is internal, not an invented provider payload. A rejected category can reduce future ranking weight, never override explicit interests/accessibility or feasibility.

`CommunicationProvider.send(approved_draft, consent_record, idempotency_key)` returns provider_ref and status accepted/delivered/failed/unknown. Recipient/payload cannot be changed after confirmation without new approval. A timeout does not imply retry is safe: use provider idempotency if supported or reconcile receipt before resending. Webhooks require verified signatures, duplicate-event protection and no authoritative itinerary edits from inbound text.

`AgentEvaluationProvider.evaluate(scenario)` returns scenario_id, expected_state, observed_state, assertions[], evidence_ref. Evaluation data is synthetic. Test proposed mutations and refusal paths; if Sparta only supports external sample worlds, describe the connection to Wonder's action boundary without claiming native Wonder-state coverage.

## Public API additions (optional sponsor slice)

These routes extend v1 only after checked schemas/permissions are reviewed:

- POST `/capability-searches`: authenticated `{task,area:"barcelona"}` → discovery result (200), Idempotency-Key. No arbitrary secrets/files or precise location sent by default.
- POST `/magic/outcomes`: authenticated `{run_id,recommendation_id,type:saved|rejected|action_opened,category}` → recorded outcome (201); validate actor owns run and category matches recommendation. Reliable outbox forwards allowed fields to Keewano; API response is not proof of query readiness.
- POST `/communications/drafts`: authenticated `{run_id,recommendation_id,recipient}` → allowlisted draft (201). Selected activity only, no precise traveler origin. Store recipient server-side encrypted with short retention; draft displays actual message/recipient.
- POST `/communications/drafts/{draft_id}/send`: `{confirm:true,expected_version}` + ETag/idempotency → receipt (202). Only draft owner with explicit consent; guest cannot send; provider status accepted does not mean delivered.
- GET `/communications/{communication_id}`: actor-owned status; do not expose recipient to unrelated trip members.

Prefer `/magic/outcomes` over an analytics SDK carrying private UI text. General app routes remain in [CONTRACTS](api/CONTRACTS.md). For current planning, no provider calls, outbound messages or data uploads are authorized merely by writing this design.

## Spike and cut policy

Time-box each access spike to 20–30 minutes during event implementation. Record credential type, actual supported region, returned payload, cost/quota, success/failure evidence and license requirements. If it fails, preserve the adapter interface and disclose disabled status. No headless login automation, personal-account API key in client, or integrations for logos alone.

Recommended order: minimal Magic vertical slice → Darwin real discovery → Keewano follow-up query → Dial explicit share → Sparta verified scenario. Alike supports coordination in parallel after authorized setup. D3 starts event ingestion early to accommodate indexing delay. D2 can build approved drafts/status UI against shared fixtures while D1 assembles core. Native parity is a beta requirement; event prototype maturity must be disclosed accurately.

## Deadline working backward

| PDT / October 11 | Target |
|---|---|
| Until 3:00 PM | integrate one functioning Magic journey; credential spikes and independent client/adapter work |
| 3:00–3:30 PM | cross-client run/save, supported sponsor proofs and failure path; cut nonworking extras |
| 3:30–4:00 PM | freeze core, measure task baseline vs Wonder, rehearse; preserve evidence and mock labels |
| 4:00–4:40 PM | project details, repo access, <=5-minute video, team/technology list; user submits |
| 4:40–5:00 PM | verify submission/links and resolve technical problems |

This is a proposed future execution schedule, not work being performed in this documentation task. If implementation starts later, shrink scope rather than moving the official cutoff or calling an incomplete beta finished.

## Five-minute demonstration outline

0:00–0:35: Barcelona traveler, 90 minutes, current app-switching bottleneck. 0:35–2:00: Wonder request → sourced feasible choices → save/navigation; show real data and explicit unknowns. 2:00–3:15: demonstrated sponsor contribution(s): capability handoff, feedback changing follow-up, user-approved share. 3:15–4:00: state-verification test and development coordination evidence. 4:00–4:40: measured TTUA/baseline, limitations, web/iOS status. 4:40–5:00: private-beta gate and connected travel roadmap. Adjust emphasis to actual working integrations; don't narrate unwired capabilities as complete.

Compare identical user tasks, include setup/review/correction, report sample size and actual timings. Estimate savings only when clearly labeled; clicks don't prove reservations or attendance. Submission remains a separate user-authorized action.
