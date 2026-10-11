# Wonder prioritized MVP roadmap

Release order agreed by owner: Barcelona Magic private beta with web/native iOS core parity, followed by connected travel MVP. Today's hackathon demo uses the same direction with a smaller acceptance gate. Priority P0 blocks the first beta; P1 completes the brief's connected MVP; P2 follows validated usage. Partner integrations have event-specific priority and may be disabled for beta if their operational gates fail.

Estimates are relative effort: S ~ half to one developer day, M ~ 1–3, L ~ 3–5; uncertainty is high until access spikes. Estimates exclude credential approval and app distribution delays. No fixed beta release date is promised.

| ID | Priority | Work / owner | Depends on | Acceptance / effort |
|---|---|---|---|---|
| F01 | P0 | contract/DTO/fixture freeze — D1+D4+D5 | planning review | both clients decode success/empty/errors; versioning defined / M |
| F02 | P0 | versions, workspace, lint/test/CI, setup — D1+D5 | F01 | clean second checkout builds; secrets isolated / M |
| F03 | P0 | identity, private schema, RLS/runtime roles — D1 | F02 | valid/revoked identity; user isolation tests / M |
| F04 | P0 | durable runs/worker, quotas, replay — D1 | F03 | restart recovery, lease/retry/schema rejection / M |
| M01 | P0 | Barcelona source+route adapter access — D1 | F01 | real sourced data + routes, policy review, explicit unknowns / M |
| M02 | P0 | deterministic feasibility — D3 | F01, M01 | known hours/routes/buffer fit; DST/budget unknown fixtures / M |
| M03 | P0 | structured Explore ranking — D1 | F04, M02 | ranks eligible candidates only; provenance and empty states / M |
| M04 | P0 | web Magic/auth/saved actions — D4 | F01, F03 | form, polling, errors, save/navigation and accessible mobile UI / L |
| M05 | P0 | native Magic/auth/saved actions — D5 | F01, F03 | same core behavior on real iPhone; denied GPS/manual origin / L |
| M06 | P0 | persisted private saves/preferences — D1 | F03, M03 | visible across web/iOS; deletion, expiry, attribution policy / M |
| M07 | P0 | beta operational gate — all | M01–M06 | live journey, quotas, export/deletion, retention/restore, privacy and parity / M |
| H01 | event P0 | Alike shared decision/session workflow — D1/all | consent/setup | next authorized session retrieves prior contract decision / S |
| H02 | event P0 | Darwin capability discovery — D1 | F01 | real search states and demonstrated useful verified handoff / M |
| H03 | event P1 | Dial opt-in result sharing — D2 | M03, DTO review | approved test-recipient send/status; explicit consent and replay / M |
| H04 | event P1 | Keewano feedback-driven follow-up — D3 | M03, outcome fixtures | ingest → query → suggestion changes visibly, with privacy / M |
| H05 | event P1 | Sparta state-verification tests — D3 | agent boundary | live scenario proves authorized changes and prohibited-action failure / M |
| T01 | P1 | multiple personalized trips/segments — D1 | M07 | traveler overrides and same-trip/date constraints / M |
| T02 | P1 | master checklist/templates — D3 | T01 | deterministic next task and persistent versioned status / M |
| T03 | P1 | participants/segment invites/guest views — D2 | T01 | claim/revoke, partial attendance, no ledger leakage / L |
| T04 | P1 | Plan & Book proposals/itinerary — D1 | T01, F04 | sourced plan, explicit apply, stale context rejection / L |
| T05 | P1 | Pack & Shop proposals/persistence — D1+D3 | T01, F04 | private/shared lists, purchased separate from packed / M |
| T06 | P1 | ledger/refunds/manual settlements — D3 | T03 | rounding, custom total, refund limits, zero-sum balances / L |
| T07 | P1 | essentials/recovery sourced tasks — D3 | T02 | manual recovery and authoritative guidance freshness / M |
| T08 | P1 | redacted web share fallback — D2+D4 | T03, T04 | explicit opt-in, expiry/revoke, no private fields / M |
| T09 | P1 | Passport/confirmed visits/recap — D3+D4+D5 | M06, T01 | visits explicitly confirmed, private default / M |
| T10 | P1 | connected UI parity — D4+D5 | T02–T09 | full brief journey across two trips; core offline read view / L |
| T11 | P1 | full connected MVP gate — all | T10 | all original required capabilities accepted, no transactional claims / M |
| E01 | P2 | native iMessage target — D2+D5 | T08, T10 | supported Messages share interaction + web fallback / M |
| E02 | P2 | WidgetKit/App Intents — D5 | T10 | redacted stale-aware snapshot and tested lifecycle / M |
| E03 | P2 | licensed event feeds/weather expansion — D1 | M07 | commercial/data access and expired-event fallback / L |
| E04 | P2 | actual bookings/payments/monitoring/merchants | T11, new ADRs | provider contracts, confirmation, refunds and operational support / L+ |

## Cut lines

For today's submission, finish one useful Barcelona request end to end before expanding. Aim for all five sponsor proofs, but drop nonworking extras at the event integration freeze; do not imply an integration is used because a logo appears. An app demo with synthetic data can be honest; it is not a live-data beta. An iOS screen-only prototype does not satisfy the user's beta parity requirement.

For Magic beta, cut advanced events, messaging automation, widgets and transactions before cutting authentication, feasibility, provenance, privacy or native parity. For the connected MVP, equal/custom splits and manual settlements are sufficient; percentage/weighted/FX follow later. Single-feature planning/packing requires only fields needed by that feature, not a forced complete trip.

## Full brief traceability

Auth/multiple trips/personalization → F03/T01. Checklist → T02. Three agents/basic itinerary/packing → M03/T04/T05. Magic → M01–M07. Participants/shared expenses/share links → T03/T06/T08. Web/iOS → M04/M05/T10. Basic Passport → T09. Essentials/recovery → T07. Remaining vision capabilities → E01–E04 and future ADRs. No requirement is silently discarded; the first release is deliberately narrower following the owner's prioritization.
