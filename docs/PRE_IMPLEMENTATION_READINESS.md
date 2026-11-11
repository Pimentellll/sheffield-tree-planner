# CANOPY Sheffield — pre-implementation design baseline and release gates

**Prepared:** 11 November 2026. **Status:** documentation synthesis completed as an authored artefact; proposed team integration baseline, not functioning software or teammate approval. **Initial event:** NVIDIA Hack for Impact Sheffield, 13 November 2026; event-specific advance-code, AI-assistant, submission and device rules still require organiser confirmation.

**Purpose:** reconcile Arnav's approved product direction and visual UI, Ben's research, the existing scientific/API contracts, the DGX deployment design and Alex's independently prepared [PR #34 execution plan](https://github.com/bbeennyy860-cyber/sheffield-tree-planner/pull/34). This is the final **analysis/design checkpoint**, not a second backlog. [BUILD](BUILD.md) remains the single task/decision-status authority. Alex's PRD owns issue-sized implementation instructions once reconciled and approved.

## 1. Authoritative document map

| Question | Authoritative source | Supporting sources |
| --- | --- | --- |
| Product objectives, user, agent limits, claims | [SPEC](SPEC.md) | [Integrated architecture](ARCHITECTURE_DESIGN.md) |
| What is P0, P1, P2, P3 and M0–M7? | [FEATURE_PRIORITIES](FEATURE_PRIORITIES.md) | [BUILD](BUILD.md) |
| API/domain object, coordinates, units, revisions, state and tool meanings | [CONTRACTS](CONTRACTS.md) | Integrated architecture explains semantics but does not revise fields |
| Solar/occlusion, crown, optimisation and uncertainty maths | [NUMERICS](NUMERICS.md) | Ben's [dossier](references/DEEP_RESEARCH_DOSSIER.md) and papers justify methods |
| Source discovery, licence and geographic evidence | [SOURCES](SOURCES.md) | [Architecture audit](ARCHITECTURE_AUDIT.md); source discovery is not accepted use rights |
| Scientific, agent and hardware acceptance | [VALIDATION](VALIDATION.md) | Design audit scenarios are not executed tests |
| Screen appearance, tokens, controls, demo values and UI mapping | [UI_DESIGN_REFERENCE](UI_DESIGN_REFERENCE.md) | Four original Claude-derived exported artboards are illustrative, not a working GIS/numerical app |
| Spark access, pinned candidate, ARM64 recipe and diagnostics | [DGX_SPARK](DGX_SPARK.md) | No device/model/GPU execution proved by documentation |
| Ownership, original B01–B12 and decisions D01 onward | [BUILD](BUILD.md) | GitHub STP issues refine tasks, not replace BUILD |
| Executable coding-agent issue packets | [Alex's PR #34](https://github.com/bbeennyy860-cyber/sheffield-tree-planner/pull/34) | [AGENT_EXECUTION_PRD](https://github.com/bbeennyy860-cyber/sheffield-tree-planner/blob/docs/agent-execution-prd/docs/AGENT_EXECUTION_PRD.md) is a separate DRAFT until team reconciliation |

**Conflict rule:** producer/consumer semantics are not decided by a paper, UI prototype or coding agent. Pause, reference the owner document, propose one change with migrations and tests, and require affected human approval. No new numeric, request or tool semantics are silently created here.

## 2. Frozen scientific/product scope

**Core planning question:** for one bounded Sheffield site and explicitly declared receiver surfaces, case/time window, profiles and upfront GBP budget, where can planting yield *additional useful direct shade* under known model constraints? What alternatives perform differently, what survey facts are missing, and can a local agent investigate a material challenge?

**Initial P0 (F001–F010):** supported site bundle (verified Sheffield or truthfully synthetic development fixture), map/target interaction, correct solar orientation and baseline-vs-tree evaluator, unweighted shade in m²·h, versioned planting/cost assumptions, independently checked geometry/budget/exclusion/spacing constraints, reproducible finite-candidate search, real local Nemotron registered-tool observation, accepted budget/constraint change and recalculation, current result provenance with zero/failure/stale states.

**Proof order:** (1) M2 baseline versus one tree from real backend into UI; (2) M3 competent reference vs constrained search; (3) parallel B03 real site and B08 proof when possible; (4) early real local model/tool validation; (5) one preferred P1 evidence-directed counterfactual and bounded repair/no-change; (6) evidence-checked demonstration and recovery. Synthetic CPU and UI development must not wait for Spark or Sheffield data clearance. A real-site claim cannot skip the latter.

**Unsupported until distinct science modules exist:** ambient temperature or UTCI change, AQI improvement, avoided runoff/flood losses, electricity savings, biodiversity units, carbon offset, multi-decade discounted ROI and four-axis weighted Heat/Equity/Flood/Air optimisation. The exported Studio's 45/25/15/15 percentages, £75k plan, 46 trees and sample runtime are **illustrations**, not implemented evidence. Disable, qualify or replace unsupported controls with a clearly accepted shade-only interpretation; no silent mapping to invented environmental scores.

**Hard constraint rule:** if a scenario requires winter sunlight protection but the winter evaluator/independent validator is not implemented, reject/disable that scenario rather than turning off its constraint or silently violating it. A physically model-feasible site still requires utilities, title, roots/soil, permissions and professional survey.

## 3. Research adoption and exact evidence boundaries

| Research-derived choice | Decision | Proof needed later |
| --- | --- | --- |
| TreePlanter and Freiburg optimisation | Adopt tested marginal greedy, local improvement, baseline, shadow overlap and reusable masks | Actual CPU evaluator and tiny exact cases; no global optimality claim |
| Crown geometry and solar radiation literature | Opaque analytic trunk/ellipsoid baseline, true ENU and UTC, separate horizon/leaf cases | V02/V04; state/profile sensitivity; no immediate mature-crown benefit |
| i-Tree/green-infrastructure effects | Preserve modular future rain, heat, air, carbon and economics components | Each needs its own inputs, equations, units, baseline and validation; not shade-to-£ conversion |
| Existing municipal/AI climate tools | Do not claim to invent tree optimisation; focus on local transparent, survey-aware decision workflow | Honest competitor comparison; user/task evidence |
| ReAct and tool agent benchmarks | Single bounded Nemotron dispatcher selecting implemented tools and observing real results | Local model-selected tool trace, correct constraints, same-tools manual/fixed comparison |
| Counterfactual and survey sensitivity | Preferred P1 fixed-layout stress test, optional constrained redesign, honest no-change/survey question | Real observed run IDs and same-case comparable results |
| DGX Spark and NVIDIA numerical libraries | Local pinned inference candidate, portable CPU oracle, optional profiled CUDA kernels | Actual ARM64/driver/model load, context/memory co-residency, performance/equality tests |
| Sheffield public/open geospatial sources | Candidate sites and source manifests; no automatic planting rights | B03/B08 exact licence, CRS/datum, capture date, context, vegetation and viewer/evaluator parity |

**Authority status:** Arnav has accepted this product/design direction (BUILD D13–D15). Ben and Alex have **not been recorded as accepting any changed shared contract or owner obligation**. No implementation or live site/device evidence is implied by that design acceptance.

## 4. Three workstreams and cross-interface freeze

**Ben:** core schema/API, immutable scenario+job+selection, dispatcher, local inference, integration and final build.  
**Arnav:** geometry, solar reference, shade/candidate computation, search, numerical/constraint tests and scientific claims.  
**Alex:** site-source/rights coordination, frontend geometry/view state, UI, comparison, planning report and demo interaction.

**Four mandatory contract handshakes:** Ben–Arnav agree ENU true north, UTC, receiver/candidate/profile IDs, current job result and metric units; Arnav–Alex verify viewer transform and the same physical scene, target and evaluation case; Ben–Alex agree draft/accepted/hypothetical and currentness/cached/delivery/error semantics; all three agree the first site, only supported UI objectives, optional agent challenge and final claims.

No coding agent invents alternate shared types or changes authoritative schemas independently. Separate Git worktrees and one active writer per shared file; small issue-specific PRs. STP issue comments hold development evidence; BUILD holds accepted integrated state.

## 5. Necessary reconciliation with Alex's live PR #34

Alex has already created a 29-task issue plan STP-001–STP-029, GitHub issues #5–#33, three initial agent branches, and an integration branch. **Keep this plan; do not create a second issue numbering scheme.** These specific review findings must be resolved before adopting it as the execution baseline.

| Finding | Priority | Required correction or explicit interpretation |
| --- | --- | --- |
| PRD currently predates the integrated architecture and inspected UI handoff | High | Add links to [ARCHITECTURE_DESIGN](ARCHITECTURE_DESIGN.md), [ARCHITECTURE_AUDIT](ARCHITECTURE_AUDIT.md), [UI_DESIGN_REFERENCE](UI_DESIGN_REFERENCE.md) and this final gate; do not replace the science/contracts |
| STP-026 real-site proof sits at M7 although B08/G2 requires real site | High | Site acquisition and rights begin M0 in STP-005/006; reach a **site candidate/readiness decision early**. Bring first B08 real-scene integration forward as soon as B03+B04+B05 permit. M7 can retain *final* site proof/report, not first discovery |
| STP-022 early agent loop precedes STP-023/024 B07 tools | High | M5 agent may call only implemented inspect/evaluate/search/revision functions. Do not promise P1 crown/winter fixed-layout counterfactual until B07 compare handlers and frontend evidence are real |
| STP-019 incorrectly names STP-023 “agent loop” as its consumer | Concrete typo | Change to **STP-022**; STP-023 is Arnav's crown/growth task |
| Four UI weighted objectives and winter toggle exceed simple P0 evaluator | Critical | Unsupported weighting and winter modes disabled/labelled or rejected; never allow an unimplemented hard rule to silently pass |
| Both documentation PRs add docs/README navigation | Integration | Merge PR #4 (architecture) first; then update/rebase PR #34 on merged main and retain both navigation entries |
| PRD initial agent/integration branches derive from unmerged PRD branch | Integration | After merge, refresh from **accepted main** non-destructively. Preserve any divergent contributor work rather than force-pushing it away |
| Ben GitHub handle and repo permissions not verified by PRD | High | STP-001 checks actual authenticated owner/account before assigning Ben issues; no invented assignee |
| UI export source archives are not checked into repository | Medium | Alex obtains the six exported HTML archives from the user; source SVGs are illustrations, not legal geometry, and third-party assets/fonts require rights checks |

**M2 means actual working backend numerical output into frontend, not a Claude artboard.** M4 means actual local model/tool observation, not synthetic HTTP fixture. G3 P1 concern means actual fixed-layout/conditional evaluation, not the mock “18/20 runs” and a nonregistered sensitivity_sweep tool.

## 6. Nine cross-system design states and how they fail safely

1. **Site:** source rights, north/CRS/datum and context incomplete → mark real site not ready; synthetic analysis may remain.
2. **Scenario:** drafts do not have accepted run identity; model-created hypothetical cannot self-activate.
3. **Evaluate:** same baseline and tree receiver/time cases; zero extra shade is a valid observed result.
4. **Optimise:** known hard constraints independently checked, plausible reference, best evaluated search, no unsupported infeasibility proof.
5. **Currentness:** queued/running/completed/failed/cancelled and selection sequence; older result never becomes current after accepted edit/new request, even if it finishes later.
6. **Compare:** same definition or explicitly described changed inputs; fixed-layout before redesign when isolating an assumption.
7. **Agent:** chosen registered tool arguments, actual observation and current run citation; stop/ask human on rights, unsupported metric, failures or no progress.
8. **Report:** itemised capital/establishment estimates, actual shade, indicative contextual metrics, explicitly nonquantified claims, survey and rights/attribution.
9. **Device/recovery:** memory/model/GPU failure means honest manual CPU fallback or labelled recorded evidence, not fabricated live inference or speed.

Detailed checks map to V01–V12; ten paper-case challenges are in [ARCHITECTURE_AUDIT](ARCHITECTURE_AUDIT.md). Those are **design scenarios**, not runtime tests.

## 7. Practical before-code and before-demo gates

| Gate | Required evidence | Present state |
| --- | --- | --- |
| Research/design synthesis | Linked architecture/audit/UI/data/agent/Spark decisions and coherent priorities | **Authored on PR #4 branch**, not merged |
| Task decomposition | One mapped owner/dependency and tests per STP issue | **Authored in PR #34**, pending reconciliation/merge |
| Contract/team acknowledgement | Ben, Arnav and Alex explicit agreement on exact contract/numerics revision, roles and merge protocol | **Open: STP-001 issue #5** |
| Primary site / fallback and rights | Actual B03 source manifest, use/display/export status, physical scene, receiver and control points | **Open; candidate sites only** |
| Supported P0 UI wording | Approved shade-first objective, explicit unavailable secondary benefits | **Open team UI/product decision** |
| Single agent test question | Tool-supported concern and success/stable/no-change criteria | **Preferred P1; team selection open** |
| DGX/local inference | Device owner approval, model/version/parser, actual observed tool call, memory/latency | **Unverified; readiness diagnostic only** |
| Contest eligibility | Sheffield organiser confirms advance code/AI use, required disclosure, deadline and format | **Unverified; other-event rules do not transfer** |
| Numerics/UI product evidence | CPU evaluator + job API + current scenario result and test receipts | **Not yet implemented** |

**Parallelisation policy:** do not block isolated synthetic arithmetic, source research or UI scaffolding on unknown site/model access. Do block integration against contested contract semantics or any unsupported success claim. A coding-agent prompt cannot count as a human acceptance or test receipt.

## 8. Documentation PR/integration sequence

1. Affected owners review [PR #4](https://github.com/bbeennyy860-cyber/sheffield-tree-planner/pull/4) for architecture/scientific/UI accuracy and contract nonchanges. Merge into main **only after required reviews/permissions** and record actual merge SHA.
2. Alex refreshes [PR #34](https://github.com/bbeennyy860-cyber/sheffield-tree-planner/pull/34) from accepted main, fixes the concrete STP-019 reference, early real-site and staged agent dependencies, references new docs, then obtains owner review and merges.
3. Integration and agent branches update **non-destructively** to accepted base; one STP issue → one task branch/PR. Do not force reset colleagues' working trees.
4. STP-001 records actual contract+roles acknowledgement; early site decision and supported UI objective are confirmed.
5. Start portable M1/M2 development and B09 preparation in parallel; verify integration at every gate; reserve demo/testing time relative to actual submission deadline D.
6. Do not label a product production-ready or competition-eligible until independent V evidence and organiser approval exist.

## 9. Final disposition

**GO for completing analysis/design and allowing Alex to finalise implementation packets.** The system's problem statement, source pipeline, model assumptions, optimisation, API and concurrency authority, bounded agent, UI, local GPU/runtime, professional/economic limits, failure states, validation and future scale are sufficiently documented.

**CONDITIONAL GO for parallel code:** contract producer/consumer acknowledgements, clean branch ownership and task prerequisites. Honest isolated synthetic work can proceed without claiming integrated acceptance.

**NO-GO for claims of a complete Sheffield/DGX system:** until actual rights-cleared site data, tested numerical engine, backend/frontend result, model-selected domain-tool observation, relevant validation and submission eligibility.

**Stop generating broad architecture documents.** Any new material blocker gets one focused source/contract amendment and a matching test, not another overlapping project specification.
