# CANOPY Sheffield — Event-day issue index and reconciled progress
**Friday 13 November 2026 · GMT · Source of operational task ownership**

This is an **index**, not a claim that every issue is implemented. The [detailed event-day board](EVENT_DAY_EXECUTION_2026-11-13.md) retains dependencies/target times. [BUILD](BUILD.md) owns historical B01–B12 acceptance and past decisions. Existing GitHub issue bodies remain intact; the event-specific tickets below are deliberately cross-linked.

## Definitive critical-path issues

| Order | ID | Owner | Priority | Deliverable and exit gate | Can proceed without Spark? |
|---|---|---|---|---|---|
| 1 | [#54](https://github.com/Pimentellll/sheffield-tree-planner/issues/54) | Ben | P0 | Preserve/merge local integration changes, deploy supplied Ollama+frontend/backend/numerics on Spark, prove local Nemotron→registered tool→current result, record release SHA and recovery; freeze by 15:00 target / 16:00 latest | Engineering preparation yes; **test on Spark** |
| 2 | [#55](https://github.com/Pimentellll/sheffield-tree-planner/issues/55) | Arnav | P0 | Five required genuine **DGX-only** model inputs, including ambiguous and correct “I don't know”; recorded score and honest failures | Prompts/rubric yes; actual tests **no** |
| 2 | [#56](https://github.com/Pimentellll/sheffield-tree-planner/issues/56) | Alex | P0 | Agent/tool/evidence/failure UI and coherent filmable scenario, no invented numerical figures | UI refinements yes |
| 1–3 | [#57](https://github.com/Pimentellll/sheffield-tree-planner/issues/57) | Arnav | P0 | Council/Forestry Research grounded problem, video narration, accurate impact+technical+feasibility story and claim ledger | Yes, except results-dependent claims |
| 3 | [#58](https://github.com/Pimentellll/sheffield-tree-planner/issues/58) | Alex | P0 | Record verified DGX demo, edit and publish **≤5-minute** YouTube/Loom video, independently check URL | Storyboard yes; capture awaits #54 |
| 3 | [#59](https://github.com/Pimentellll/sheffield-tree-planner/issues/59) | Ben | P0 | Rights/history/credential audited public GitHub source, anonymously accessible, from tested release | Audit may start now; publication after team approval |
| 4 | [#60](https://github.com/Pimentellll/sheffield-tree-planner/issues/60) | Arnav | P0 | Complete **every** mandatory NVIDIA form field, public repo + video URLs, submit and confirm by **17:30** internal target | Collect metadata yes; submit awaits #58, #59 |

**Key blocker chain:** #54 → (#55, #56, Spark video capture in #58) → #60; **#59** → #60 in parallel. #57 starts immediately, then incorporates proven technical findings.

## Mapping every task from the old execution board (do not duplicate existing issues)

| Board tasks | Existing long-term issue(s) | Event-critical issue | Reconciliation / priority |
|---|---|---|---|
| B-E01 branch reconciliation | [#5](https://github.com/Pimentellll/sheffield-tree-planner/issues/5), [#33](https://github.com/Pimentellll/sheffield-tree-planner/issues/33) | #54 | Ben; unmerged local agent/deploy work not yet confirmed on main |
| B-E02 approved SSH + Spark hardware | #23, #33 | #54 | Ben; only approved Spark account and keys |
| B-E03 backend/physics/frontend device deploy | #18, #33 | #54 | Main carries core frontend/backend, Spark evidence missing |
| B-E04 supplied model startup | #23 | #54 | Ben; supplied Ollama preferred, not fresh vLLM download |
| B-E05 real agent to tool to result | #26, #23 | #54 | Critical proof; contextual 8192-token cap |
| B-E06 device performance/recovery | #33 | #54 | On Spark only; record exact environment, not laptop |
| B-E07 release freeze | #33 | #54 | 15:00 target / 16:00 latest |
| A-E01 existing harness audit | #31 | #55 | Reviewed original B11 code; new agent_eval only locally developed |
| A-E02 five test cases/rubric | #31 | #55 | Five cases specified in board, bindings and execution still needed |
| A-E03 real Nemotron tests | #31 | #55 | Blocked by Ben handoff; **DGX only** |
| A-E04 optional second-model comparison | #31 | #55 | **P1 optional; no GPU model switching during recording** |
| A-E05 science/results audit | #14, #19, #30, #31 | #55, #57 | Audit calculated shade, constraints and source identity; no real-site claims |
| A-E06 architecture and claims | #33 | #57 | Research/script can proceed now, numeric results after Spark |
| A-E07 real Sheffield dataset provenance | #9, #10, #30 | — | **P1/P2, non-blocking** for explicitly labelled synthetic demonstration |
| X-E01 UI blocker correction | #17, #22, #25 | #56 | Fix only user-visible critical regression |
| X-E02 visible agent states | #29 | #56 | Coordinate interface with Ben; no browser→model direct route |
| X-E03 video/deck storyline | #32 | #58 | Video is required; slides only if useful for video graphics |
| X-E04 rehearsed scenario/fallback | #32 | #56, #58 | Real Spark evidence mandatory for final footage |
| X-E05 final video and optional slides | #32 | #58 | YouTube/Loom up to 5 minutes |
| X-E06 Sheffield mesh | #9, #30 | — | **P2 deferred** until rights and CRS/solver parity pass |
| S-E01 organiser requirements | #5 | #60 | Organiser Kunal email gives required fields; form URL/precise closure still need confirming |
| S-E02 submission/links/receipt | #33 | #59, #60 | 17:30 target based on 18:00 team-reported shutdown/form timing |

## Reconciled code/evidence status at this audit

- **On GitHub `main` at inspection:** core physical simulation, typed service + original `backend/tests/benchmarks/runner.py`, React 3D UI. New committed source must be checked against a **fresh main SHA** before making assertions.
- **Only seen in the attached Claude Code local execution log:** `backend/src/tree_planner/agents/runs.py`, `backend/tests/benchmarks/agent_eval.py`, `backend/tests/benchmarks/agent_eval_tasks.json`, `deploy/spark/bench.py`, `deploy/spark/canopyctl` and worktree `integration/arnav/spark-demo`. Ben must inspect `git status`, preserve uncommitted changes and integrate selectively. Do not give them a fictitious merged SHA.
- **Development evidence in attached log, NOT device proof:** Python unit tests, 53 frontend tests, 19 browser checks and authentic *laptop* Qwen experiments. New agent-evaluation ladder's three scenarios × three local repeats reported evaluation 3/3, search 2/3 and safe failure 3/3; these are strictly labelled laptop/WSL, not Nemotron/Spark. In the search run, some model prompt counts exceeded **8192 tokens**. This is a **risk to fix/test on Spark**, not a measured Spark failure.
- **Not yet verified:** on-Spark Nemotron evidence, final merged agent code, public-repo safety, externally playable video, submitted form acknowledgement. Never mark green based on a task plan or AI statement alone.

## Organiser brief and time control

NVIDIA organiser's 13 Nov 11:31 email is authoritative for: one track (choose **Urban Operations**), agent with local model on assigned DGX Spark, 5 tested prompts including ambiguous and correct unknown, Nemotron bonus, provided Ollama and model tags, 8192 tokens/request, one model loaded at a time, public GitHub repository, YouTube/Loom video <=5 min, description, all team/model/NVIDIA tooling fields, Impact/Technical Execution/Feasibility. User reports Spark shutdown **18:00** and expects form closes then; **form URL and exact cutoff have not been independently confirmed**. Target submit **17:30**, not 18:00; abort P1 before it threatens form.

**Communication:** Each owner update uses `START / STATUS / BLOCKED / READY / INTEGRATED`, exact commit SHA if code, on-Spark evidence or URL if claim, dependencies, and handoff. A named owner does not equal done. Ben owns Spark actions, Arnav cannot run laptop tests, Alex owns video capture. All collaborate on final link check.

## Autonomous work already prepared

- [Judge-facing narrative, scientific research and safe description](EVENT_DAY_CONTENT_AND_CLAUDE_HANDOFFS_2026-11-13.md)
- [Claude Code prompts for Ben, Arnav and Alex](EVENT_DAY_CONTENT_AND_CLAUDE_HANDOFFS_2026-11-13.md#claude-code-handoffs)
- [Original task board](EVENT_DAY_EXECUTION_2026-11-13.md)

**Work-in-progress policy:** preserve no-stage-merge and authorisation gates, but prioritise the 17:30 deadline over cosmetic changes. Do not publish secret credentials or unlicensed geographic assets.
