# Wonder — repository integration snapshot

October 11, 2026. This snapshot reconciles the latest main onboarding commit (`6956b57`), the teammate orchestrator/dashboard contribution (PR #5, reviewed head `a08b99b`), and the three-agent control contribution (PR #4, initial head `96addff`). No additional product features or deployments are started by this integration task.

## Contributions and compatibility work

| Contribution | What it supplies | Current limit |
|---|---|---|
| [PR #5](https://github.com/jayasrisng/super-travel/pull/5) | CLI orchestrator, deterministic event dispatch, in-memory sessions, static five-agent advisor dashboard, generated synthetic dashboard data, installable Python packaging | Dashboard reads `data/demo.json`; local review actions do not call the control API or execute external actions |
| [PR #4](https://github.com/jayasrisng/super-travel/pull/4) | Three proposal backends, authenticated FastAPI run controls, durable local runs, minimal trips, Magic bookmarks, checked OpenAPI and fixtures | Local token/SQLite adapter; Magic live discovery/routes are not configured |
| Main onboarding commit | Saved landing-page HTML plus a scripted intake conversation and editable form | Nine referenced local assets are absent; no live call, auth, persistence or backend intake integration |
| Earlier PR #2 | Essentials/Recovery prototypes, deterministic helpers and CLI examples | Prototype tools can mutate an in-memory TripContext; not exposed through the production domain API |
| Earlier PR #3 | Product/architecture/contracts/ownership/roadmap foundation | Beta design exceeds what is implemented today |

Reconciliation retains all five registered specialist names, removes stale claims that the first three are unbuilt, preserves deterministic EVENT_ROUTES, and teaches custom orchestrator registries to distinguish an unavailable session agent from a registered global agent. New specialists accept the orchestrator's optional `today` dispatch argument. Combined registry tests prevent the former TypeError regression.

The installable Hatch packaging fix is preserved together with the API dependencies and updated lockfile. README includes both the control API and teammate CLI/dashboard launch commands. Specialist exceptions no longer echo private provider details into returned errors/model history. The static demo server binds to loopback and returns 400 for malformed URLs without crashing. No alternate frontend is created.

## What works now

- Five specialists are discoverable by the CLI orchestrator. Planning/Packing/Magic fixture dispatch succeeds; Essentials/Recovery retain their existing offline tool/model tests.
- Three-agent HTTP control: create/list/poll/cancel with strict schemas, actor/trip isolation, idempotency, versions, bounded queues, lease recovery and expiry.
- Minimal owner-only trip context and Magic save/list/delete share the local SQLite store.
- Planning/Packing optionally invoke the inherited model runner. Fake model API tests verify the loop; live account/model access has not been tested.
- Magic deterministically filters normalized candidates by time, onward commitment, buffer, cost, hours and freshness. The runnable provider is visibly synthetic.
- Advisor dashboard serves its page, JavaScript, CSS and five-agent JSON as a standalone local demonstration. No new claim of full visual/device QA is made here.

## Verification

Combined suite: **51 passed, 1 network test deselected**. Includes two added integration regressions for actual three-agent orchestrator dispatch and private-error redaction. Scoped Ruff checks, JavaScript syntax checks, lockfile synchronization and whitespace checks pass. Local HTTP smoke verifies dashboard assets, synthetic data labeling and malformed-URL recovery. Tests and checks call no paid model/discovery provider.

Onboarding asset audit identifies missing font stylesheet, two compiled app assets, analytics script, three photos and two logos. The inline scripted intake is present, but the saved HTML is not a complete source/build package. Preserve the teammate's artifact and ask its owner for the missing source/assets before describing onboarding as deployable.

## Where the project stands

There are working backend components and two presentation demos, **not one connected private-beta product**. The advisor demo is a different surface from the planned consumer Magic dashboard. The CLI orchestrator operates on the permissive prototype TripContext; the HTTP control uses a smaller strict owner-scoped context. They are not yet one durable authenticated conversation flow.

The major remaining seams are:

1. Connect the chosen web experience to checked OpenAPI and real control states; restore complete onboarding source/assets and map confirmed intake fields into the minimal trip API.
2. Add real Barcelona discovery/hours/routes adapters, a reviewed coverage polygon, provider licenses and an owner-approved budget with enforced caps.
3. Replace local token/SQLite identity/storage with verified JWT/current membership, PostgreSQL/RLS and managed durable workers.
4. Add reviewed itinerary/packing/checklist apply services; retain explicit confirmation and context-version protection.
5. Deliver native iOS Magic parity, cross-client saved state and private-beta operational checks.
6. Implement and prove the desired sponsor integrations; none is silently inferred from static samples or imported tools.

The user will choose the next direction after this merge/status report. Do not begin these workstreams or launch paid/live services merely because they appear in this list.
