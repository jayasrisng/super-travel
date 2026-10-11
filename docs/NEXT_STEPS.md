# Wonder — next steps from the implemented backend

Main inspected at `5ecbe06` contains the planning foundation and Essentials/Recovery prototypes. This backend change adds Planning, Packing, Explore/Magic, an actor-scoped FastAPI control API, durable local runs and checked OpenAPI. The website belongs to another teammate; no frontend is included.

## What is ready to integrate

- Three agent keys: `plan_book`, `pack_shop`, `explore_magic`, mapped to the five-specialist registry's `planning`, `packing`, `explore` names.
- Create/list/poll/cancel with typed proposals, 24-hour replay protection, versions, bounded queue, lease recovery and expiry redaction.
- Minimal owner-only trip creation/read and private Magic save/list/delete.
- Synthetic requests/proposals and canonical implemented OpenAPI in `packages/contracts/`.
- Fixture engines, optional Planning/Packing model runner, deterministic Magic feasibility and a discovery-provider interface.
- Existing Essentials/Recovery prototype modules, CLI scripts and tests preserved.

Use [CONTROL_API.md](CONTROL_API.md) for exact launch commands and limitations. Model access was tested with a local fake API, not paid providers. No production authentication, migrations, live POI/routing adapter, website/iOS implementation or deployment is claimed.

## Priority order and ownership

| Priority | Owner | Concrete next step | Acceptance |
|---|---|---|---|
| P0 | D1 + D4 + D5 | Review local OpenAPI; generate TypeScript/Swift clients; wire three dashboard panels | Both clients decode the same result fixtures; create/poll/cancel/error/expiry states reflect server status. Keep local token out of shipped clients. |
| P0 | Owner + D1 | Choose monthly budget, provider access and reviewed Barcelona polygon | Explicit costs/quotas/license boundaries and kill switch before paid/live enablement |
| P0 | D1 + D3 | Implement licensed discovery/hours/routes adapter behind DiscoveryProvider | Real origin/onward routes, source freshness, partial failures and costs; live candidates cannot borrow fixture data |
| P0 | D1 | Replace local identity/store with verified JWT/Postgres and managed worker | Current trip membership checks, runtime-role RLS isolation, restart/lease/cancel/replay tests and revocation |
| P1 | D4 + D5 | Complete Barcelona Magic core with saved state parity | Web/native iOS support manual origin, unknown/empty/error states, refresh expired recommendations and private saves |
| P1 | D1 + D3 | Add explicit selected-item proposal apply and packing/checklist domain | Context-version/ETag conflict tests; no silent overwrite or purchase/completion inference |
| P1 | D1 | Enrich Plan/Pack with sourced adapters after Magic core | Current drafts stay unverified until sources are actually consulted; structured items remain proposals |
| P1 | D2/D3 | Integrate sponsor boundaries from hackathon plan | Dial only approved recipient/content; Keewano outcome query changes a follow-up; Sparta synthetic evaluation proof; Darwin search separate from execution |
| P2 | D1/D2/D3 | Connected trip workflows | Coordination, expenses, share permissions, essentials/recovery behind reviewed domain boundaries |
| Gate | All | Private-beta validation | Real Barcelona feasibility, costs/privacy/restore/rollback, equally complete web/native Magic core |

The first teammate handoff is a local fixture request through the real API, followed by shared client decoding and saving. It is demo integration evidence; live-beta acceptance still requires the P0 gates. The hackathon submission and external communications remain team-owned; none have been submitted by this change.

## Keep five developers independent

D1 owns `super_travel/control`, the new proposal agents, checked contracts and serialized shared-core edits. D4 owns website presentation and server-side development proxy. D5 owns native host/configuration and generated Swift consumption. D2 owns coordination/Dial; D3 owns deterministic domains, provider feasibility validation and sponsor evaluation. Preserve existing root Python paths until a separately coordinated migration. Use focused PRs; do not overwrite another developer's shared-file work.
