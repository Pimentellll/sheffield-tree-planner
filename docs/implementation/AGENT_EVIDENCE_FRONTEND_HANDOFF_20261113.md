# CANOPY — agent evidence UX, browser integration and acceptance handoff

**Proposed for:** Arnav (`reverez`) — frontend agent-evidence consumer, tracked in [#74](https://github.com/Pimentellll/sheffield-tree-planner/issues/74); Ben (`bbeennyy860-cyber`) — producer agent-run API ([#73](https://github.com/Pimentellll/sheffield-tree-planner/issues/73)) and job worker (#72); Alex (`akurkar07`) — owner of the surrounding UI shell, panels and their failure states (#56, event board X-E02) and film capture (#58). **Ownership (decided by Arnav, recorded on [#56](https://github.com/Pimentellll/sheffield-tree-planner/issues/56) at 13:56 GMT, 13 Nov):** Arnav owns the agent-evidence UI (#74); everything else under #56 stays with Alex. Alex keeps the existing static "no agent endpoint" slot (`frontend/src/panels/CompareScreen.tsx` ~236 on `main`; `App.tsx` ~148–152 on `feat/alex/design-parity`) until the working panel arrives from #74 once Ben's #73 API exists. Placement in the shell is coordinated through #56. **Files:** #74 (Arnav) owns new files only: `frontend/src/planning/agentEvidence.ts` and `agentEvidence.test.ts` (draft PR #76), plus the proposed `frontend/src/planning/useAgentRun.ts` and one agent-evidence panel component (proposed `frontend/src/panels/AgentEvidencePanel.tsx`). Everything else in `frontend/src/` under #56 stays Alex's, including `App.tsx`, `panels/CompareScreen.tsx` (and the agent slot, wherever it currently sits), `styles.css` and the existing `panels/*`. The only cross-owner edit is mounting the #74 panel in place of the static slot, which happens through #56. **Date:** 13 Nov 2026. **Status:** DESIGN AND ACCEPTANCE PLAN, not wired or tested. **Base inspected:** `main` `ca1662de978758044561ea005c77b95ef8609aeb`.

**Revision (13 Nov, ~14:00 UTC):** corrected after an adversarial source/issue audit. It now references #72–#74 (opened after the first commit), fixes the dependency diagram, aligns the run states and field names with the companion audit, places all test execution in CI or the DGX window (event-day §12), and repairs the Markdown code formatting. Contract-independent presentation helpers for #74 (unavailable state, Job→Result evidence chain, untrusted-narrative figure guard) are proposed separately in draft [PR #76](https://github.com/Pimentellll/sheffield-tree-planner/pull/76).

**Related:** the companion [Nemotron/runtime audit, PR #70](https://github.com/Pimentellll/sheffield-tree-planner/pull/70) (proposed; Ben is backend lead), which lands as `docs/implementation/NEMOTRON_AGENT_RUNTIME_AUDIT_20261113.md`; [current UI](../../frontend/src/App.tsx), [workspace state](../../frontend/src/planning/useWorkspace.ts), [HTTP client](../../frontend/src/api/client.ts), [Compare evidence panel](../../frontend/src/panels/CompareScreen.tsx), [event-day five-case protocol](../event-day/science/AGENT_EVALUATION_PROTOCOL.md), [UX PR #67](https://github.com/Pimentellll/sheffield-tree-planner/pull/67) and [geospatial PR #66](https://github.com/Pimentellll/sheffield-tree-planner/pull/66).

## 1. What currently exists — audit evidence

The published React/Three.js frontend supports accepted revision-aware manual evaluation, search and comparison, currentness checks, the synthetic physical 3D view, source-bound review exports, and immutable Result evidence. These are **working existing features**, not proposed new work. `useWorkspace` exposes `activeJob`, `runs`, `currentness()`, `evaluate()`, `submit()`, `cancel()`, `loadProposal()`, `acceptProposal()` (job polling is an internal `poll` callback used by `submit`, not exported); `CanopyClient` has typed domain HTTP endpoints, but it performs no runtime shape validation (it casts the parsed JSON to the expected type). **It has no agent-run methods.** The Compare evidence panel explicitly says agent history/narrative are unavailable because backend lacks an endpoint. UI must not fabricate missing traces.

PR #67 (docs, opened by Arnav; proposes Alex as frontend/UI owner) proposes broad map-first visual information architecture and tree/object semaphores. **Do not rewrite it or the synthetic scene for event-day integration.** This proposal is about getting one genuine, typed, demonstrable Nemotron investigation across the current UI, with safe failure.

## 2. P0 browser journey and strict trust boundaries

One filmable evidence-backed path:

1. Human selects an **accepted synthetic** scenario and sees its current revision, assumptions, budget and available physical operations.
2. User enters a brief (for first milestone, "Evaluate the currently proposed planting layout"). UI sends exactly one typed agent-run request on a host-selected accepted revision, with stable `request_id`. The model tag, tools and source permissions are **not user-editable**.
3. Server returns `agent_run_id` and status; UI renders queued/running, then the actual `model_call` → `tool_requested` → `tool_accepted` events (event names per the companion audit §3), showing the registered operation and **sanitised** validated arguments.
4. Server tool adapter creates/polls a real immutable Job, returns a current Result with exact `source_job_id`, `run_id`, input fingerprint and scenario revision. UI renders Result data using existing numeric evidence components. Model prose remains tagged **interpretation**, not raw metric truth.
5. UI displays a concise evidence chain: `Accepted task rev → Nemotron model call → evaluate_layout → Job ID → current Result ID → additional_shade (m²·h, declared time sample) + cost (£ from backend pence) + limitations`. Include currentness and "synthetic demonstration" permanently.
6. If model fails, token budget is exceeded, the worker is unavailable, a revision changes or user cancels, show specific blocked/recovery state and keep the manual evaluate path available; never display an invented fallback answer.
7. Full run history remains inspectable after reload. A previously completed run whose selection is no longer current becomes **historical** with stored evidence, never CURRENT. It is shown with the existing `classifyResult` labels: NOT CURRENT (same revision) or SUPERSEDED (older revision).

Prefer the **minimum evaluate-only** tool subset for the first demo: the local Qwen rehearsal showed search failures; the five required tasks can be evaluated separately on Spark. Add broader approved tool dispatch only after the genuine evaluate trace is stable and Ben confirms the exact contract.

## 3. UI-facing API contract (proposed; Ben is authority)

A new versioned agent-run surface must be generated from the backend OpenAPI and consumed by `CanopyClient`; frontend must **not** infer events by scraping logs or `/jobs` status alone.

| Proposed action | Data passed or received | Security/currentness |
| --- | --- | --- |
| `POST /api/v1/agent-runs` | `{request_id, accepted_scenario_ref, user_text, requested_intent?}`; response `{agent_run_id,status,accepted_scenario_ref}` | Host picks model/allowed tools; If-Match; duplicate request id returns same run rather than another submission. Reload and lost-response recovery need a lookup by `request_id` or a list route; Ben decides which in #73 |
| `GET /api/v1/agent-runs/{id}` | `AgentRunView`: status, exact source ref, model/run identity, bounded validated tool events, `job_ids`, `validated_run_ids`, host summary, explicitly untrusted model narrative, safe reason code | Transport and parsed schema validation. Never trust model-provided run IDs without backend validation |
| `POST /api/v1/agent-runs/{id}/cancel` | cancellation acknowledged/terminal state | Separate stopping agent inference from cancelling domain job; immutable existing Results survive correctly |
| Existing `GET /api/v1/jobs/{job_id}` and `/results/{run_id}` | typed authoritative domain Job and Result | Revalidate `source_job_id`, fingerprint and `selections`; no client arithmetic passed off as computed result |

**Do not copy this suggested shape into generated TS until Ben merges the reviewed FastAPI contract.** Avoid parallel invented client types. A numeric Result can exist even if the model's final prose fails validation; render the independently verified result and a **failed interpretation** badge rather than dropping its provenance.

Potential compact `AgentRunView` fields (requires exact backend sign-off):

```text
agent_run_id: UUID
accepted_scenario_ref: {scenario_id, revision, scope:"accepted"}
status: queued|running|cancellation_requested (transient)|completed_with_evidence|metadata_only|draft_prepared|clarification_requested|safe_abstention|needs_evidence|failed|stopped|exhausted|cancelled
created_at_utc, updated_at_utc: string
events: [{sequence, type, time_utc, tool_operation?, args_digest?,
          scenario_ref?, job_id?, run_id?, trust_class, summary?}]
job_ids: [string]            // server-created domain Job IDs, including failed ones
validated_run_ids: [string]  // server checked; not model text
model_identity: {model_tag, provider:"ollama", release_sha?} | null
source_snapshot_hash: string | null
host_summary: string | null
untrusted_model_narrative: string | null
reason_code: safe enum | null
```

These names mirror the companion audit §3, including its mapping from the existing `AgentLoop` outcomes. Final names follow Ben's generated OpenAPI in #73. Do not call `completed_with_evidence` a success if the job's actual Result was superseded. C4 clarification and C5 safe refusal are **human-scored, model-behaviour results**; they have no numerical metric and must not require a fake `run_id`. The live server status for such runs is `needs_evidence`: `clarification_requested` and `safe_abstention` appear only as reviewer labels on the stored receipt, unless #73 defines a deterministic rule (companion audit §3).

## 4. Frontend implementation slices Arnav can own

These slices are tracked in #74 and consume Ben's #73. Arnav owns the agent-evidence UI (see the ownership note at the top). FE-A3 to FE-A6 replace the agent slot inside Alex's shell, so where the panel sits and any edits to surrounding panels are coordinated through #56.

| Slice | Files / steps | Testable acceptance | Priority |
| --- | --- | --- | --- |
| FE-A1 Contract consumer | Ben's #73 route lands with its regenerated `generated/*` artifacts already committed: CI and `backend/tests/contracts/test_generation.py` enforce `scripts/generate_api_types.py --check`. Arnav does **not** regenerate or edit `generated/*`. Add the new type names to the explicit re-export list in `frontend/src/api/types.ts`, then add `CanopyClient` methods | Exact compile, no hand-authored parallel wire schema. Malformed-response refusal needs an explicit decision, because `CanopyClient` currently casts without validating: either a validator derived from `generated/http-openapi.json` (new dependency, to be agreed) or minimal guards on the safety-critical fields (status enum, ids, `scenario_ref`), documented as such | P0, blocked on Ben |
| FE-A2 Agent run state hook | New `useAgentRun` separate from `useWorkspace`, pinned `scenario_ref`, stable request ID, polling with abort/disposal, idempotent cancel | Duplicate clicks → one agent run; component unmount stops polling, not server job; reload recovers same run | P0 |
| FE-A3 Evidence trace component | Small existing-panel extension, not visual redesign: real `model → tool → job → result` with run IDs/currentness/unit/limitations and trust labels | Synthetic result shown only from GET Result; tool event labelled actual vs scripted; no model-invented figures | P0 |
| FE-A4 Safe states | Error, ambiguous/clarify, I-don't-know, unavailable, stopped, exhausted, missing token receipt, stale, cancelled | One named negative test per state: error → T19, ambiguous/clarify → T10 (C4), I-don't-know → T10 (C5), unavailable → T01, stopped → T18, exhausted → T16, missing token receipt → T17, stale → T07, cancelled → T08. Honest manual fallback; no silent disappearance of terminal failure | P0 |
| FE-A5 Exact trace capture panel | Copy **redacted**, reviewable run IDs/model tag/release SHA and actual observed usage; never expose raw hidden prompts/keys/source paths | Filming shows real identifiers and synthetic label, video references same release evidence | P0 |
| FE-A6 Browser proof | 1920×1080 release screenshot and narrow-width check, keyboard and labels, refresh/revision/cancel scenarios | Real backend-vs-UI equality; no manual or mock trace labelled Nemotron | P0 |
| FE-A7 Minor polish | Compact legend, latency spinner, retained last successful result as historical, copy run ID, date formatting | Does not change any backend numeric meaning, no key focus regressions | P1 |
| FE-A8 Larger map and tree explorer | Use PR #67 + #66 and Alex's terrain branch; source-only until accepted B08 | No false inferred tree/physics connection | P2 |

UI should only ask Ben for a *minimal reviewed contract*, not an entire design system rewrite. Existing manual Evaluate/Compare/Review functions and the old `useWorkspace` remain intact.

## 5. Agent state matrix (test each transition, not only happy path)

| Event | Server truth | UI action | Forbidden behaviour |
| --- | --- | --- | --- |
| Agent disabled/no model | backend says unavailable | Disabled call with explanatory text; manual app still functional | Sample "Nemotron" transcript |
| Submission pending | request in flight | Stable pending state and disable duplicate start | New random ID per click |
| Queued | agent run created | Show run ID and waiting label | Invent ETA/progress |
| Running model | agent-run event, no Result | Show model/tool phase with trust class | Display predicted shade |
| Tool dispatched | validated operation and args | Show tool name/job ID and linked accepted revision | Render tool data as raw HTML |
| Job completed current | verified Result and selections | Render exact metrics, units, cost pence conversion and limitations | Show weighted utility as physical shade |
| Cached Result | `execution_mode` from backend | "Cached" plus original run identity | Claim new physical calculation |
| Model final invalid | verified Result may exist | Preserve verified Result, label interpretation failed | Treat model text as evidence |
| C4 ambiguity | independent human rubric not auto-success | "Needs clarification" or safe task assumption; zero computed only if no real Result | Fake numeric job to justify answer |
| C5 abstention | no supported physical answer | "Cannot infer °C or savings"; source-bound limitations | Unsupported estimated number |
| New scenario revision | head moved to n+1 | Mark all n-derived agent outputs historical | Show old numbers current |
| Draft unsaved | accepted head unchanged, visible draft changed | Display stale/draft warning; require accept/recompute for new scenario | Compute from unaccepted client state |
| Cancel | stop/cancel response | Acknowledge cancellation requested and terminal, preserve immutable history | Silent deletion / status "completed" without evidence |
| Poll/network failure | state unknown | Report lost connection, allow safe refresh and fetch by same run ID | Resubmit new run automatically |
| Worker dead | backend degraded | Manual fallback, no endless spinner | "Everything healthy" |
| Wrong source/restricted | validation/rights block | Surface typed error, no metrics | Render restricted source imagery |
| Real terrain view only | unapproved site | Label visual-only, disable real numerical benefit | Apply synthetic result to Sheffield terrain |

## 6. Test plan for a small frontend PR

Prefer Vitest for pure trace/status and `CanopyClient`, browser tests against a **real synthetic backend** for wire/currentness, and 1 final Spark screenshot. Write the tests before connecting to UI.

**Where tests run (event-day §12):** Arnav runs none of these on laptop/WSL. Vitest (`npm test`) and the browser/physical checks (`frontend/tests/browser-check.cjs`, `physical-check.cjs`, which `frontend.yml` already runs against a real synthetic backend) execute in GitHub CI on a draft PR, or in an approved DGX window after Ben's handoff. Otherwise the PR ships with the exact unrun commands and the blocker stated. The current Vitest config is node-only (`src/**/*.test.ts`, no DOM), so hook, unmount, double-click and keyboard checks (FE-A2, T03, T12, T13) belong in `browser-check.cjs` unless adding jsdom/@testing-library is agreed.

- **T01 no-backend:** agent control unavailable; no fabricated model answer.
- **T02 submit:** exact accepted scenario/revision; generated stable `request_id`; backend 202 shown.
- **T03 duplicate-submit:** double click does not create second server run.
- **T04 duplicate POST response lost:** same request id is retried only if server idempotency is proven, otherwise re-query/unknown and no mutating replay.
- **T05 genuine evaluate:** instrument GET Job/Result; UI numerical text equals stored computed value and units; cost uses pence→GBP conversion once.
- **T06 malicious model narrative:** fabricated 3 °C / £/year in untrusted model text does not enter validated metric display.
- **T07 currentness:** accept scenario n+1 mid-run; old Result never CURRENT.
- **T08 cancellation:** queued/running/completed states, separate agent vs job stop, no late false success.
- **T09 unavailable tool:** present typed failure; manual evaluation still works.
- **T10 safe no-answer:** C4 and C5 no Result produce no metric cards; model-behaviour grade separate from physical success.
- **T11 display source-rights:** no raw private paths/credentials or restricted assets in copy/public panels.
- **T12 reconnect/reload:** run ID stable, last valid historical receipt displayed with correct provenance.
- **T13 responsive/keyboard:** focus order, aria-live updates, 1920/1024/390 px and keyboard-accessible tool history.
- **T14 regression:** existing evaluation, comparison, stale revisions, export, strict TS and browser/physical tests still pass.
- **T15 demo:** physical app on DGX, genuine Nemotron call, screenshot showing matching run ID to private receipt. If not achieved, film only what is established.
- **T16 exhausted:** the run spends its **action budget** (`AgentLoop` returns `exhausted` only for that); the UI shows `exhausted` with any Results produced so far, labelled correctly, and claims no conclusion.
- **T17 missing token receipt:** the server reports a turn without trusted usage; the UI shows the run as lacking device evidence and never labels it a verified 8,192-bounded Spark run. **Blocked on #73:** the proposed `AgentRunView` has no per-turn usage or receipt field yet, so Ben must add one (or a trusted-usage flag) before this test can be written.
- **T18 stopped (deadline):** the run hits its deadline. `AgentLoop` returns `stopped` for both a deadline and a stop event, and never `cancelled`, so the run manager reports `cancelled` from its own user-cancel flag (companion audit §3). The UI shows `stopped` for a deadline and `cancelled` only after a user cancel, never confusing the two.
- **T19 model or server error:** the run ends `failed` (a model protocol error, or a 5xx from the agent-run API), as distinct from an unavailable tool (T09). The UI shows the allowlisted reason code, keeps any Results already validated, offers the manual path, and leaks no raw exception text.

**No CI result can prove actual inference from a fake `MockTransport` response.** Tests must be labelled `mocked`, `synthetic-real-backend`, or `on-DGX genuine`.

## 7. Handoff to Ben: interfaces you need to request once

Before Arnav begins FE-A1, Ben supplies in one message:

- Exact **release SHA** on which `scripts/generate_api_types.py --check` passes with the #73 route included, plus whether local run-manager commits were reconciled.
- How a run is found again after reload or a lost POST response: a lookup by `request_id` or a list route (as in §3). Client-side persistence of `agent_run_id` helps a reload, but it cannot recover a lost POST, because the client never received the id. It is therefore not sufficient on its own.
- Exact accepted `ScenarioRef`, which tools are available, unique `agent_run_id` and cancellation semantics.
- Terminal outcomes and distinction among completed physical evaluation, missing result, abstention, invalid final, timeout and cancelled.
- Security-safe tracing fields and whether the UI may display model identity, per-turn usage and tool args.
- Verified currentness lookup and provenance/selection query after refresh.
- The model tag **actually tested** on the DGX (the organiser lists `nemotron-3.5-lightning:30b`, but no evaluated run exists yet), `num_ctx`, 8,192 cap evidence, one quiet GPU window.
- A minimal on-Spark complete example (one agent → one registered evaluate tool → one stored Result), not raw SSH secrets.

Once the contract is merged, Arnav can implement the hook, panel, tests and evidence capture in a scoped PR; Ben retains ownership of API, domain operations and numerical source. Alex's UI/video responsibility is not silently reassigned — coordinate #56/#58 explicitly before editing shared panels.

## 8. Dependency-aware delivery and fallbacks

```text
Model/eval lane (does NOT wait for the agent-run API):
#54 + #64 (Ben: actual Ollama model, native client)
          |
          v
#62 (Ben: 8,192 context/usage proof) --> #63 (Ben: five-case driver,
          |                                runs AgentLoop directly)
          |                                      |
          |                                      v
          |                               #55 (Arnav: independent
          |                                    DGX scoring)
          v
UI lane:
#72 (Ben: worker supervision) --+
                                 v
#73 (Ben: durable agent-run API, agreed contract)
          |
          v
FE-A1/A2 (#74, Arnav)
          |
          v
FE-A3/A4/A5/A6 (#74, Arnav; shell placement via #56)
          |
          v
#58 (Alex: film) --> #60 (Arnav: form/receipt)
```

#63 drives `AgentLoop` directly and does not need the agent-run API (#63 body). **Proposal for Ben to confirm on #73/#55:** #55's five-case scoring depends on #63's driver, not on the #73 API, so #55 should not wait for #73. #73's current acceptance text links the API agreement to #55. Until Ben confirms, that text stands, and this diagram is a proposed ordering, not an agreed one.

If API delivery is blocked: **do not fake an agent panel**. Record the real Nemotron→registered tool→Result on the DGX backend/CLI with honest device evidence, show the deterministic numeric UI separately, and explicitly call out the current integration limitation. If the full model-tool call is blocked, no "agentic AI achieved" claim is authorised.

## 9. Review gates and recursive defect search

For each FE-A slice, test the normal path, malformed response, timeout, revision race, cancellation, safe refusal, redaction and accessibility. Recheck adjacent boundaries after each fix: API type → frontend client → state hook → status card → evidence panel → video capture. Stop for event-day P0 only when each case has an executable receipt and no unknown-critical interface remains; keep P1/P2 open rather than declaring "no holes".

**Files intentionally not modified here:** `frontend/src/*` (Alex owns the shell and panels under #56; the agent-evidence UI lands in its own #74 PR), `backend/src/tree_planner/api/app.py`, `generated/*`, `docs/BUILD.md`, and the frozen five-case prompt fixture. This documentation PR proposes an agreed contract and tests; it does **not** implement those routes or falsely report passing CI.
