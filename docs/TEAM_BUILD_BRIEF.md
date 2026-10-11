# Wonder — team build brief

> Current consumer supplement: [CONSUMER_APP.md](CONSUMER_APP.md). Checked OpenAPI defines implemented local routes. Latest consumer scope supersedes older Magic-first/website ownership; production beta gates below remain separate.


**Less searching. More experiencing.** Repository: `jayasrisng/super-travel`. Product renamed Wonder by owner; original brief retained in [PRODUCT_BRIEF.md](product/PRODUCT_BRIEF.md).

## Agreed direction

Owner decisions: **Magic first**, **Barcelona**, **private beta first**, and **equally complete core web/native iOS**. D3 takes deterministic backend workflows. Today's SpeedHacks entry is a focused demo, with an integration-maximizing plan across Alike, Darwin, Dial, Keewano and Sparta. A same-day demo does not waive beta reliability/privacy criteria or imply the full travel super-app is complete. See [PLAN](../PLAN.md), [roadmap](MVP_ROADMAP.md) and [hackathon integrations](HACKATHON_INTEGRATIONS.md).

## Five owners and exclusive edit boundaries

| Owner | Magic-first responsibilities | Connected MVP responsibilities | Owned paths / shared boundary |
|---|---|---|---|
| D1: lead, agents, API | auth/context/jobs, structured ranking, Darwin, approved live discovery | trip/segments, Plan & Book, Pack & Shop, itinerary/manual bookings | `services/api/.../core`, `agents`, `integrations/darwin`, root configs/contracts; migration coordinator |
| D2: coordination/iMessage | Dial opt-in sharing adapter, coordination contract, native share flow | participants, segment attendance, invitations, guest scopes, web share DTOs; later Messages | `domains/coordination`, `integrations/dial`, `apps/ios/.../Features/Coordination`, `Extensions/Messages`; D4 owns web page rendering |
| D3: essentials/recovery and domain backend | feasibility rules with D1 interface, provider regression cases, Keewano, Sparta scenarios | checklist/packing persistence, expenses/refunds/manual settlement, sourced essentials/recovery, Passport API | `domains/operations`, `integrations/keewano`, domain tests, `database/seeds`; migration proposals reviewed by D1 |
| D4: web and design | Magic web/auth/saved states, accessibility, action funnel | landing/onboarding, trip dashboard, all responsive connected views and redacted share pages | `apps/web`, `packages/design-tokens`; consumes API, owns no independent ledger |
| D5: native platform | SwiftUI Magic parity, auth lifecycle, location permission fallback, native save/navigation | native trips/checklist/packing/expenses/Passport; later widgets/push | `apps/ios` except D2 source folders; exclusive editor of project.pbxproj, schemes, entitlements/signing |

`services/api/...` abbreviates `services/api/src/super_travel/`; architecture contains complete layout. Provider adapters other than assigned sponsors are D1-owned by default, with explicit handoff possible after interface approval. D3's feasibility module is `domains/operations/feasibility`; it is deterministic shared logic consumed by the Explore agent. D1 coordinates Alike adoption; each developer controls their own authorized setup/transcript capture.

D1 must not implement everyone’s backend. D2/D3 own route/domain tests in their folders, using core persistence/auth interfaces. They propose schema/contract changes through review rather than maintaining divergent schemas. D4 implements Essentials/Recovery web views from D3 contracts; D5 implements native equivalents. D2 must not independently rewrite host navigation, auth or Xcode targets.

## Shared files and review

- API spec/generated clients: D1 owns integration; each affected consumer reviews. Contracts merge before dependent feature work; no hand-edited generated output.
- Migrations: D1 assigns ordering, reviews same-trip constraints/RLS and clean-database replay. Each domain owner authors its schema proposal; append-only after merge.
- Xcode project and target configuration: D5 serializes changes. D2 works inside agreed source folders, requests configuration changes.
- Tokens/shared web components: D4 owns changes; D5 consumes versioned JSON token export without editing web CSS.
- Root manifests, lockfiles, CI: D1 owner; avoid unrelated reformatting. Real names/handles and CODEOWNERS remain Phase 0 work.

Before editing a shared file, reserve it in the human team coordination channel and release after PR; no implied authorization for tools to send messages. Branches are small and domain-scoped. Never push directly to main. Contract changes need D1 and affected consumer; expenses/permissions need independent review. Avoid cherry-picking a migration out of order.

## Contracts everyone shares

[Data model](DATA_MODEL.md) and [API contracts](api/CONTRACTS.md) define UUIDs, UTC instants/IANA zones, integer money, same-trip association constraints, per-resource version/ETag, context versions, errors and idempotency. No client writes trip tables directly. Guest record ≠ authenticated user. Saved/booked ≠ attended. Recorded settlement ≠ payment. Live data ≠ verified availability. Agent output ≠ applied plan.

Fixtures are synthetic and explicitly labeled. A contributor can build UI against canonical fixtures while backend catches up. No module invents its own persona, status, expense split or API envelope. Semantic changes require updating source specs and both client fixtures together.

## Handoffs and first independent tasks

D1 publishes Magic wire fixtures + run/job boundary; D4/D5 immediately implement matching form/loading/result/error flows in separate branches after implementation is authorized. D2 spikes Dial draft/send/status with test recipient and prepares coordination DTOs. D3 implements feasibility fixtures and typed Keewano outcome query contract, then deterministic task/ledger rules. D4 defines shared UI tokens; D5 scaffolds host targets and deep-link routing. Sparta test evidence is D3-owned; every adapter owner supplies one successful and one failure case.

Three integration checkpoints: (1) fixture contracts on both clients; (2) same live server Magic run consumed by web/iOS; (3) persistence, failover and partner proof across the same user action. No separate “agent demo” counts as integrated app functionality.

## Demo and beta acceptance

Event journey: user in Barcelona has 90 minutes → Wonder presents sourced feasible choices → chooses and saves/navigates → explicitly shares if enabled → feedback history affects next suggestion → show agent failure tests and measured time-to-action. Explain each actual partner contribution, remaining mocks and disabled integrations. See the event plan for deadline/submission steps; this task does not submit forms or contact sponsors.

Private beta must additionally pass real auth, private saves/preferences, location-denied/unsupported-area/error handling, operational live providers, tested retention/deletion, device delivery, rate limits and rollback. Both clients meet the same core criteria. The full Tokyo/friends/packing/expense/Passport journey follows beta, maintaining the original long-term MVP scope.

## Operating rhythm

Discuss contract blockers first, integrate continuously, and keep one canonical fixture set. Every PR states task ID, owned paths, contract/migration implications, validation and known limitations. Review against acceptance criteria, not feature count. Measure TTUA including review/correction time. A successful venue navigation/share is distinct from a reservation or attendance.

## Consumer work boundaries

| Developer | Current exclusive paths | Handoff |
|---|---|---|
| D1 | control/, consumer/models.py, consumer/api.py, contracts/export + API drift CI | Serialize schema/route registration changes; generate client atomically |
| D2 | consumer/coordination.py, apps/web/src/group.tsx | Same-trip participants/segments/expenses and redacted guest access; request shared API/model edits through D1 |
| D3 | consumer/service.py, consumer/wardrobe.py | Task lifecycle, preferences, briefing, wardrobe/votes/packing invariants; request shared contracts through D1 |
| D4 | apps/web except group.tsx, design assets | Notebook themes, primary consumer flows, browser tests and accessibility |
| D5 | future apps/ios, docs/WIDGET_CONTRACT.md | Native parity, account/deep-link/cache/signing gates; no native target is currently shipped |

API registration, root docs and CI are coordinated shared files with one editor. Keep new changes additive and avoid cross-domain formatting churn. Python domain mixins share Notebook's transaction/ownership primitives; they must not create their own authoritative stores. Teammate advisor/onboarding artifacts remain intact; the consumer app is a separately reviewable feature branch.
