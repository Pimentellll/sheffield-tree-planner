# CANOPY — recursive runtime, Nemotron and release-boundary architecture audit

**Audit date:** 13 Nov 2026, ~12:55 UTC. **Base:** \`main\` at \`ca1662de978758044561ea005c77b95ef8609aeb\`. **Status:** PROPOSED DESIGN AND TEST GATES, not implemented or device-verified. **Lead:** Ben (\`bbeennyy860-cyber\`); **frontend/evaluation consumer:** Arnav (\`reverez\`). No merge or model execution is authorised by this document.

**Read before implementing:** [BUILD](../BUILD.md), [CONTRACTS](../CONTRACTS.md), [VALIDATION](../VALIDATION.md), [AGENT_EXECUTION_PRD](../AGENT_EXECUTION_PRD.md), [event-day board](../EVENT_DAY_EXECUTION_2026-11-13.md), [five-case evaluation protocol](../event-day/science/AGENT_EVALUATION_PROTOCOL.md), [FIX-1..4](../event-day/science/ENGINEERING_FIX_PLANS.md). Companion implementation proposals [#66](https://github.com/Pimentellll/sheffield-tree-planner/pull/66) and [#67](https://github.com/Pimentellll/sheffield-tree-planner/pull/67) cover long-horizon 3D data and general UX; this audit does **not** supersede either.

## 0. Method, evidence grades and bounded stopping rule

Inspected the complete pushed Git tree (187 files, 13 Nov), especially \`agents/__init__.py\`, \`agents/http.py\`, \`api/app.py\`, \`api/service.py\`, \`jobs/__init__.py\`, opt-in real-agent tests, \`benchmarks/runner.py\`, the frontend client/workspace/evidence screens, \`deploy/spark/*\`, canonical docs and open issues. Code observations below are **source inspection**, not executed tests. Recorded Spark baseline and model smoke are **issue-reported** evidence at [#54](https://github.com/Pimentellll/sheffield-tree-planner/issues/54), not personally reproduced. All genuine inference acceptance must occur on DGX.

Walk the following chain repeatedly, asking at each interface: **trusted input? typed contract? identity/fingerprint? hard bounds? error/cancellation? stale result? rights? evidence? user-visible truthful state? repeatable test?**

\`licensed/declared source → site/profile/catalogue → accepted scenario/layout → registered domain operation → immutable job → numerical Result → agent observation/model tool choice → currentness validation → user evidence → private evaluation receipt → DGX release/video/export\`.

A pass stops only when every **P0** row below has a named owner, proposed change, test and signed evidence, or is explicitly rejected with reason. This is not a claim that no undiscovered bug exists. Do not conflate acceptance planning with successful execution.

## 1. What is genuinely implemented

- **Domain:** synthetic SiteBundle, source rights, immutable accepted scenario revisions, layout registration, finite candidate catalogue, strict Pydantic operation arguments, SQLite jobs and Result provenance; physical evaluator/search and comparison are real CPU calculations on **synthetic flat geometry**.
- **Agent core:** \`LocalClient\` calls loopback \`/v1/chat/completions\`; \`AgentLoop\` derives tool schemas, checks strict arguments, pins accepted context and revalidates current Results before presenting authoritative backend text. \`HTTPDispatcher\` restricts localhost and pins task headers. These are useful defenses, not a finished agent web product.
- **Gaps proven by source:** \`api/app.py\` exposes \`/api/v1/operations\` (domain dispatcher) and \`/jobs\` but **no /agent-runs endpoint**; \`frontend/src/panels/CompareScreen.tsx\` explicitly says the agent panel is unavailable. \`LocalClient\` has no mandatory exact input-token counter (optional \`max_input_tokens\`); full Result is appended as a model observation. \`JobWorker.loop()\` does not catch \`run_one()\` exceptions, so a claim-path invariant error may terminate the worker. \`deploy/spark/model-profile.json\` is a candidate **vLLM** profile, not the organiser-provided Ollama deployment.
- **Already tracked:** #54 integrated DGX agent release; #55 five probes; #56 UI; #57 claims; #58 video; #59 public-history security; #60 submission; #62 context; #63 harness driver; #64 actual Ollama configuration; #65 optional catalogue relocation. Do not create duplicate tools, agent loops or harnesses while Ben implements these.

## 2. Gap register — findings, minimal solution and acceptance

| ID / severity | Failure mode / evidence | Solution / owner | Acceptance; existing work |
| --- | --- | --- | --- |
| R01 **P0** | DGX model answered a prompt but has not selected an actual domain tool on the accepted Spark release | Ben wires **native Ollama seam** to existing \`AgentLoop\` and \`HTTPDispatcher\`, preserving pinned scope; **no second independent agent** | Model-produced call → typed validated request → stored Job → current Result ID, captured on DGX, #54/#23 |
| R02 **P0** | No stable web agent-run route, so UI cannot start/observe an investigation | Ben adds typed run manager/HTTP start-read-cancel API, exact accepted revision and idempotency, bounded task executor; Arnav consumes | Browser starts run, sees real tool history, reloads to same receipt, #54/#56 |
| R03 **P0** | \`/v1\` route does not set \`num_ctx\`; byte limit is not token limit; previously long search prompts | Implement **existing FIX-1** with verified Ollama context + measured usage + compact model observation; fail closed if unknown/over cap | Prompt/request and loaded context fit 8,192 including output reservation, receipts per turn, #62 |
| R04 **P0** | No complete five-case model driver on current main | Implement existing **FIX-2**, use frozen hashed prompt JSON, one accepted physical fixture and one model, write five immutable receipts | C1–C5 hashes, per-turn usage, operation traces, stored outcomes, reviewer grading; no synthetic simulation of model; #63/#55 |
| R05 **P0** | Candidate vLLM docs conflict with supplied organiser Ollama | Implement existing **FIX-3** in a separate actual-device profile; no downloading/replacing provided weights | Exact installed tag, digest if obtainable, Ollama version, \`/api/ps\`, \`num_ctx\`, package/commit identity, single loaded model, #64 |
| R06 **P0** | Uncaught \`JobStore.claim()\` / \`run_one()\` exception can kill \`JobWorker.loop()\` and strand queued work | Ben reproduces with controlled backward wall-clock fixture; use nondecreasing persisted timestamp bounded by created timestamp at \`claim\` **if contract permits**, plus supervised loop with finite backoff and explicit health fault; never silently retry a possibly admitted job | Clock jump creates no invalid record; worker remains live or visibly degraded, recovery handles existing records, next queued request can complete; no fabricated failure codes |
| R07 **P0** | Model completion may succeed but job/result or scenario becomes stale before UI presentation | Store exact accepted \`ScenarioRef\`, tool args, \`job_id\`, \`run_id\`, selection and head revision; recheck at delivery and on subsequent frontend refresh; history immutable | Supersession and cancellation never show old numbers as CURRENT; related #24/#54 |
| R08 **P0** | Model final JSON has \`narrative\`/\`evidence_ids\`; status \`needs_evidence\` conflates unsupported accurate abstention and failure | Separate **host-derived presentation classification** for \`clarification_requested\`, \`safe_abstention\`, \`no_evidence\`, \`completed_with_evidence\`. Do not trust model to self-certify safe behaviour | C4 and C5 no-tool outcomes are scored against independently authored rubric, never shown as computed model evidence; #55/#56 |
| R09 **P0** | Full Result JSON observations can exceed context or expose unneeded source data | Ben writes bounded semantic projection of each verified Result (operation, case/unit/value, feasibility, bounded layout/cost/constraints, run IDs, limitations); keep full Result server-side unchanged | Search + evaluate stays within observed token budget; never drops failure/unknown constraints; full results still independently fetchable; #62 |
| R10 **P0** | Worker and agent stop/cancel are separate; unclear whether cancel interrupts model and numerical job | Define distinct \`agent_cancel_requested\`, stop token, underlying \`Job.cancel\` only when host policy permits, terminal/late-result behavior, UI acknowledgement | Cancel during inference, tool pending, result available and network drop yields one final consistent state; #54 |
| R11 **P0** | Retry after HTTP timeout may be ambiguous: tool was possibly submitted before timeout | Store request ID and accepted-ref idempotency key prior to dispatch. Reconcile by querying existing run/job; never replay mutating operation solely because response was lost | Inject response loss after commit: exactly one Job, no duplicate currentness, typed recoverable unknown state |
| R12 **P0** | Local model/GPU and CPU jobs may contend; no shared deadline across all blocking stages | One active model session on Spark for P0; per-turn, entire run, polling and backend HTTP timeouts; simple busy/queue state; worker liveness/readiness | Two simultaneous agent requests: second rejected/queued boundedly; no 8192 breach or infinite spin; #54 |
| R13 **P0** | Browser could mistake model text for authoritative simulation/claim | Emit server-bound evidence object and **untrusted model interpretation separately**; only present registered Result values/units from backend | A fabricated °C/£ figure in model text never appears as validated metric; C5 abstention and metrics test; #56/#57 |
| R14 **P0** | Experimental receipts may contain full prompt/source paths and user text; public repo already visible | Private \`0700\` receipt directory, no raw credentials, hashes of frozen inputs, optional redacted submission extract; never commit raw source assets/model logs | Scan produced public demo pack and entire published Git history for secrets/rights; hashes verify without revealing secrets, #59/#63 |
| R15 **P0** | The final video could use a local trace while claiming Spark | Release manifest binds SHA, platform aarch64, model tag/context/usage, fixture hash and run/job IDs to filmable UI; record failed scenarios truthfully | Reproduce one exact SHA/device trace and show matching UI/backend result; #54/#58/#60 |
| R16 **P1** | Native tools may be passed unsupported by installed model or receive malformed call structures | Capability preflight (Ollama \`show\`), strict name/args/tool-call-id checks, reject unregistered tools, expose clean error; no silent plain-text conversion | Tool-unsupported and malformed-response negative tests; no dispatch after bad model response |
| R17 **P1** | Worker health is reported as API healthy even if background thread dies | Separate HTTP liveness from worker readiness; show \`worker_alive\`, \`queue_depth\` if verified, \`failure_reason\` allowlisted; no raw exception leak | Force worker termination; health explicitly degraded, UI disables new work or manual fallback |
| R18 **P1** | Long-lived replay traces can drift across revisions/model versions | Immutable receipt schema version, source SHA/fixture/profile fingerprints; no replay as live inference | Replay view uses \`recorded\` label and original identity; incompatible schema refuses silently incorrect display |
| R19 **P1** | Existing comparison C3 moves without rebinding catalogue ID and is correctly infeasible | Keep as diagnostic for mandatory C3; implement #65 only after accepted semantics/tests and protocol variant recorded | No feasibility laundering; current fixture C3 stays honest |
| R20 **P2** | Real Sheffield raster/individual tree semantics/non-flat solver still unverified | Dedicated [#66](https://github.com/Pimentellll/sheffield-tree-planner/pull/66) geospatial pipeline and #67 UX; retain strict visual-only isolation from synthetic solver | Real data + numerical parity independent acceptance; do not block P0 |
| R21 **P1** | Source \`LocalClient.complete\` checks reply structure but does not on its own attach per-turn tokenizer/provider metadata to \`Outcome\` | Transport records \`usage\`, \`finish_reason\`, served model, elapsed, \`/api/ps\` separately; parser validates plausible numeric ranges | Missing/negative/oversize usage invalidates organiser acceptance; no heuristics called exact tokens |
| R22 **P1** | Stale/historical model-run view could be presented with selected current scene after reload | Re-fetch accepted revision, selection, and run in typed frontend client, then render separate provenance and status | Reconnect races against another accepted revision show historical label, never CURRENT |
| R23 **P1** | Fixed five cases alone do not establish agent superiority | Preserve B11 manual/fixed/adaptive matched-evidence benchmark as separate P1 after event mandatory probe | Same task/tools/time budget; reviewers independent; no causal advantage claim from five cases |
| R24 **P1** | More agents or world-scale front-end expansion could disrupt P0 release | Keep one bounded investigator, six registered operations, server-side policy, deterministic fallback. No user-defined Python/SQL/URLs or free-form tool selectors | Prompt injection, off-task instruction and unsupported benefit attempts produce refusal or typed block |

**Evidence certainty:** R01–R05, R07–R09, R13, R16, R19–R21, R23–R24 are source/docs-supported. R06 is a **plausible fault matching the reported local reproduction**, not a measured DGX fault. R10–R12, R14–R15, R17–R18, R22 are under-specified integration/acceptance boundaries, not verified exploits.

## 3. Runtime seam: additive contract proposal, not an implemented endpoint

Do **not** expose raw \`AgentLoop\` or allow the browser to supply \`model_base_url\`, system prompts, arbitrary tools or unaccepted site identifiers. The trusted server chooses installed provider, session capacity, prompt template, tool allow-list and accepted task snapshot. Add a small manager around the existing loop; prefer its already developed local analogue after Ben reviews it.

Suggested typed contract (names require review against current OpenAPI):

\`\`\`text
POST /api/v1/agent-runs
  Body: { request_id, accepted_scenario_ref, user_text, requested_intent? }
  If-Match: "<accepted revision>"
  202:  { agent_run_id, accepted_scenario_ref, status: "queued" }
GET /api/v1/agent-runs/{agent_run_id}
  200:  { agent_run_id, status, accepted_scenario_ref, created_at_utc,
          updated_at_utc, tools: [sanitised event], job_ids, validated_run_ids,
          host_summary?, untrusted_model_narrative?, reason_code?,
          release_identity?, source_snapshot_hash? }
POST /api/v1/agent-runs/{agent_run_id}/cancel
  200:  { agent_run_id, status: "cancellation_requested" | "cancelled" | terminal }
\`\`\`

No new \`ScenarioInput\` or \`Result\` wire fields for the hackathon. When domain operations complete, resolve their **existing** Job/Result separately and validate \`validate_delivery_currentness\`. \`agent_run_id\` represents an investigation session; \`run_id\` already identifies a numerical computation, so never alias them. An agent session may contain several jobs, including failed ones.

**Run state machine:** queued → running → {completed_with_evidence, clarification_requested, safe_abstention, needs_evidence, failed, stopped, exhausted, cancelled}. \`cancellation_requested\` is transient only. Clarification/abstention categories are **presentational and independently checked against host rubric**; do not claim a success grade merely because the model says "I do not know". A late numerical Result can stay in domain history but must not make a cancelled/superseded agent current.

**Recorded event (minimal, safe):** sequence; type \`model_call | tool_requested | tool_accepted | job_queued | job_running | result_validated | terminal | error\`; UTC; registered operation; validated argument digest; exact scenario ref; job/run IDs; bounded host summary; trust label (model statement vs backend result). Never return raw local paths, credentials, unrestricted source rows or arbitrary model-supplied HTML.

**Implementation location:** a narrow \`agents/runs.py\` SQLite-backed manager behind \`api/app.py\` is acceptable if Ben's existing isolated branch is compatible; use API-generated OpenAPI/TS contracts, not a handwritten divergent interface. Derive \`max_actions\`, deadlines, model tag and allowed operations from server configuration. If critical integration fails, retain the working deterministic manual simulator and show "agent unavailable", not a scripted substitute.

## 4. Worker and concurrency tests Ben should add before the final freeze

1. **Clock regression:** monkeypatch the clock to return a time before a queued job's \`created_at_utc\` at claim. Assert no validation exception/thread disappearance; \`started_at_utc\` is valid and \`deadline\` semantics remain correct; second queued job completes. Do not hide wall-clock uncertainty by altering stored \`created_at_utc\`.
2. **Thread exception supervision:** inject a controlled \`run_one\` failure. Assert either bounded recovery with an explicit health fault or fail-closed refusal; no infinite hot loop and no "healthy" status while dead.
3. **Restart:** interrupt active job, start with exclusive lease, mark abandoned running as \`WORKER_INTERRUPTED\`, preserve completed Results and request identities. Recovery never reruns previous admitted unknown operations automatically.
4. **Cancellation:** start model, cancel before tool; start tool then cancel; cancel after terminal. No new request after stop; historical immutable result may exist but not be current.
5. **Lost POST response:** submit succeeds but HTTP response is dropped. Client re-queries saved request/agent ID; no second execution with new random request ID.
6. **Cross-revision race:** accept revision n+1 while model is returning n's result; stale evidence retained as history and not presented as current.
7. **Token context:** mocked missing usage/negative usage/oversized prompt/large search result and actual on-Spark \`/api/ps\`. Exact token counts are measured, not estimated from characters.
8. **Parallel session:** two browser users click run; server enforces capacity=1 for P0, retains typed "busy" or queued status, and keeps watchdog responsive.
9. **Prompt injection:** malicious source text attempts to alter budget/approve planting/read files; model is not permitted to do so even if it requests the action.
10. **No-answer/ambiguity:** one run with no tool and correct abstention; one with prohibited invented number. Host records both, preserves model text separately, never counts either as evaluated physical result.

Use the existing \`backend/tests/agents\` mocks, \`test_live_local.py\` recorder, \`backend/tests/jobs\` and \`backend/tests/benchmarks\` infrastructure. **A green synthetic test suite is not a Nemotron proof.** Do not run competing GPU benchmarks during Ben's deployment window.

## 5. Five-case evidence harness: acceptance, not an alternative harness

The canonical fixture is \`docs/event-day/science/five_case_prompts.json\`, five SHA-256-bound prompts C1–C5, with the [protocol](../event-day/science/AGENT_EVALUATION_PROTOCOL.md). Implement FIX-2 (#63) *once*, in Ben's branch; Arnav is scorer/independent observer, not a second harness author.

Per case collect: fixed prompt hash and filled host-context hash; accepted scenario, layout and source fingerprint; actual model tag; \`/api/version\`, \`/api/ps\` and context; release SHA and \`aarch64\`; start/end and model/dispatch/job time; every raw tool name and strict validated args (private); every exact job/result/selection; per-turn \`usage.prompt_tokens\`, \`completion_tokens\`, finish reason; final \`Outcome\`; scored rubric with failure origin. Keep private raw receipts outside git and separately prepare a small redacted public evidence digest.

**Fail closed** on missing real device, missing model identity, untrusted/oversize usage, absent fixture hashes, mismatched Result identity or omitted test case. The scorer must not treat \`pytest PASS\` (which may only mean receipts written) as behavioural PASS. C4 and C5 can correctly produce **no numerical run**. C3 may correctly be infeasible under the current candidate-ID design. C2 must preserve the actual finite-catalogue/one-hour-sample caveats.

## 6. Release ordering and acceptance

1. Preserve stable \`main\` synthetic baseline and prior CI receipts; freeze one release SHA (no unreviewed cherry-picks from old \`demo/hackathon\` or stale worktrees).
2. Ben implements #62/#64 and minimal Nemotron tool path #54; use existing loop/dispatcher, no rewrite.
3. Verify worker safety R06 and API R02; if the UI route cannot be safely finished, capture the genuine backend model→tool→Result separately and demonstrate deterministic UI truthfully; do not claim end-to-end agent UI.
4. Ben implements #63, hands exact model/config/fixture/quiet GPU window to Arnav.
5. Arnav runs C1–C5 strictly on DGX, scores model behaviour and checks numerical/evidence fidelity; every failure remains in ledger.
6. Arnav adapts frontend against reviewed agent-run contract (companion spec PR); Alex's already assigned final film capture #58 remains with Alex unless team explicitly reallocates.
7. Record model and numerical evidence in film, validate public video/repo history and submit #60 before internal cutoff.

## 7. Audit recursion matrix (all interface pairs)

| Boundary | Audit question | Guard/test owner | P0 disposition |
| --- | --- | --- | --- |
| Source → SiteBundle | lawful, actual geometry and meaningful confidence? | Arnav, #66 | **defer real site**; synthetic explicitly declared |
| SiteBundle → Scenario | immutable source identity, accepted revision, rights? | Ben, existing contract/tests | preserve |
| Scenario → Job | idempotent admitted operation, hard budget, current head? | Ben, R07/R11 | add tests |
| Job → Result | trusted producer, provenance/fingerprint/feasibility? | Ben + Arnav, existing tests | preserve and check |
| Result → Model observation | compact but unit- and failure-preserving? | Ben, R03/R09 | **fix #62** |
| Model → Tool | actual Nemotron structured call, bounded scope, no fake call? | Ben, R01/R16 | **fix #54** |
| Tool → AgentRun | durable status, cancellation, recovery, worker supervision? | Ben, R02/R06/R10 | **new design** |
| AgentRun → UI | currentness, trust label, no invented metric/unknown? | Arnav, companion PR | **new design** |
| UI → Video/public | release SHA and precise device claim match, redaction? | Arnav + Alex + Ben, R14/R15 | evidence gate |
| Demo → Submission | visible URL, receipt, source security? | Arnav + Ben, #59/#60 | human signoff |

### Recursion outcome
**Round 1 (components):** missing web agent-run seam, context budget and five-case driver. **Round 2 (failure paths):** worker crash, idempotency, stop/cancel and stale propagation. **Round 3 (evidence and public output):** refusal/ambiguity classification, source trust, recording privacy, model/run provenance and video truth. **Round 4 (cross-owner reconciliation):** known FIX-1..4 and PRs #66/#67 cover overlapping work; no new incompatible system is warranted. A fifth desk pass found no additional *untracked P0 interface category*, but the list is not a proof of system correctness. Re-run on the integrated release and keep any failed/blocked row open.
