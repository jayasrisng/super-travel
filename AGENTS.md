# Repository-wide instructions for contributors and coding agents

These instructions apply to all repository paths. App name **Wonder**; repo remains `super-travel`. Read README, PLAN, ARCHITECTURE, docs/TEAM_BUILD_BRIEF, docs/DATA_MODEL and docs/api/CONTRACTS before modifying shared behavior. The preserved docs/product/PRODUCT_BRIEF.md is the initial product source of truth; explicit owner changes in docs/decisions/DECISIONS.md take precedence. Do not silently reinterpret a conflict.

## Current scope and truthful status

This repository is planning-only at this change. Do not build application features during the documentation task. A subsequent explicit implementation request can authorize Phase 0 and scoped roadmap work; it need not reapprove every routine technical choice. Do not imply that planned commands, tests, API routes, integrations or deployment already exist.

Priorities: Magic first in Barcelona; first usable release is private beta with web/native iOS core parity. Hackathon demo is separately gated. Preserve the full connected-travel roadmap. Integrations are maximized through meaningful, demonstrated use, not speculative claims or logos. No unrelated architecture rewrite or unbounded infrastructure additions.

## Ownership and independent work

Use team brief path ownership. D1 owns shared core/contracts/migration coordination; D2 coordination/Dial/assigned Swift sources; D3 operations/feasibility/Keewano/Sparta evidence; D4 web/tokens; D5 host iOS/Widget and exclusive Xcode project editor. Shared files have one editor at a time. Coordinate through a scoped PR; do not overwrite teammates' changes or reset a dirty checkout.

Do not spawn/delegate agents merely because five developers are mentioned. Only delegate when requested by the user or applicable task instructions. A proposed human collaboration workflow does not authorize tool-driven messages, feedback posts or submissions. Do not push directly to main. Do not push, create issues or submit the hackathon project unless the task authorizes that external action.

## Architectural boundaries

- One FastAPI modular monolith. Agents/integrations are Python modules, not separate authoritative stores/services. No LangGraph, Redis, vector DB or event bus without demonstrated need and an ADR.
- REST v1 is the domain boundary. Clients may authenticate with Supabase, but never write/read domain tables directly. No duplicated expenses/permissions/feasibility calculations in web/Swift.
- Agents read authorized minimal snapshots and produce schema-validated proposals. Application services apply selected items only with explicit confirmation/current context version. No agent direct DB writes.
- Deterministic code owns permissions, date/time arithmetic, feasibility, split/refund math, state transitions and ordering. No AI-generated calculations or availability status.
- Per-trip children and associations require trip_id and same-trip FK checks. Single-feature runs are actor-owned with nullable trip_id, never phantom trips. Guest record is not authenticated membership.

## Contract-first changes

Propose schema/operation changes before dependent features. Canonical prose is docs/DATA_MODEL.md + docs/api/CONTRACTS.md until Phase 0's checked OpenAPI exists; thereafter update source models, exported spec and fixtures atomically. Generate TypeScript/Swift clients; never hand-edit generated output or create a parallel shared-types source. Review by D1 and affected client/domain owner. Additive v1 changes preferred; breaking changes require version/deprecation/mobile compatibility plan.

Use snake_case JSON, UUIDs, integer minor-unit money, civil dates and UTC instants with IANA timezone. Preserve response/error envelopes, cursor semantics, idempotency and ETag rules. Distinguish omitted/null. Keep domain enums synchronized; unknowns must fail safely. Do not invent endpoint success for unimplemented features.

## Security, privacy and integration rules

JWT verification checks signatures/issuer/expiry/audience; load current membership from DB. Never authorize from editable user metadata. No privileged database/Supabase secret/model/provider keys in NEXT_PUBLIC vars, Swift bundles, prompts, screenshots or logs. Runtime DB role is least privilege and subject to RLS; migrations have separate credentials. Test runtime-role tenant isolation and trip bootstrap.

All adapter output is untrusted. Normalize/provenance-tag and validate before ranking; whitelist external destinations and enforce egress restrictions before connecting returned capabilities. Mock/fixture, live, estimated and verified are distinct. No inferred reservation/payment/attendance from clicks. Source license/cache restrictions govern storage.

Private by default: locations, constraints, packing, ledger and share views. No passport scans, children's identifying details or health records in MVP. Shares are allowlisted/redacted, revocable and expire. Guest tokens are hashed/server-side, scoped and never logged. Do not put real user records into fixtures, issue bodies or analytics.

No purchases, cancellations, payments, outbound calls or messages from agent output without explicit user intent/confirmation required by the action. Dial uses approved recipient/payload; inbound replies propose changes rather than write shared plans. Alike setup/transcript sharing is separately authorized per developer. Keewano contains only permitted minimal outcome events; Postgres remains canonical. Sparta test worlds use synthetic state and must be labeled tests.

## Development conventions

Future tooling: pnpm + strict TypeScript/ESLint/Prettier; uv + Python/Ruff/Pytest; SwiftUI/XCTest/SwiftLint. Exact compatible versions are pinned during Phase 0; commit lockfiles. No invented version claims. Tests near owning modules; shared fixtures in packages/contracts/fixtures after scaffolding. Python service exposes interfaces instead of clients importing internal repositories. Keep UI implementation details out of consumer workflows.

Branches docs/topic, feat/domain-topic, fix/domain-topic. Small PRs state acceptance/task ID, changes, checks, contract/migration impact, fallback and material limits. No unrelated formatting churn. Keep secrets out of tracked files; .env.example documents names/placeholders only. Root setup commands must be runnable and verified before README labels them current.

Migrations are serialized, append-only after merge, and verified from empty DB. Use expand-contract rollouts compatible with older mobile clients; no destructive migration without task authorization and recovery plan. Never bypass RLS to silence permission errors. Enforce cross-trip links and financial totals in transaction + DB constraints; verify with the runtime role.

## Required validation proportional to change

Documentation: inspect diff/whitespace, relative links, JSON examples and consistency with owner decisions. Do not invent application-test results.

Backend: meaningful tests for authorization/removal, trip isolation, jobs/leases/replay, idempotency, version conflict, private packing, money/refund caps and state transitions. Magic: route/hours uncertainty, Barcelona/DST, onward commitments, buffers, time/budget feasibility, expired provenance and partial outages. Schema: clean replay, runtime-role RLS, old-client compatibility.

Clients: core journey success/loading/empty/error/retry, accessibility, denied-location/manual origin, expired auth, safe links, save reflected cross-client. Native sign-in/deep links/device and offline timestamp/wipe behavior. Finance checks use exact values, never tolerance floats. Provider contract tests are offline by default; real smoke tests are explicit and budget-bounded. CI fails on schema/client drift; required checks must exist and pass before claiming readiness.

Run relevant checks once; broaden only for unresolved risks/new failures. No meaningless tests mirroring simple documentation edits. When blocked, report concrete missing access/credential/runtime capability and proceed with independent work. Do not silently replace a live-beta criterion with mocked output.
