# CANOPY Sheffield — Event-Day Execution Board
**Friday 13 November 2026 · All times GMT (Europe/London)**

> **Team target:** have an integrated, working and validated DGX Spark demonstration by **15:00**, with **16:00 the latest planned engineering cutoff**. From then onward, prioritise presentation, video, rehearsal and submission. **The organiser's actual submission deadline and pitch/video rules must be checked immediately and override this schedule.**

**Status:** Coordination plan, not proof that any task is complete. Update statuses only against observed commits, tests, hardware receipts and deliverables. This is the **event-day execution overlay**; [BUILD.md](BUILD.md) remains the canonical B01–B12 engineering task/decision record. Source-specific validation remains in [VALIDATION.md](VALIDATION.md), hardware instructions in [DGX_SPARK.md](DGX_SPARK.md), and scientific scope in [NUMERICS.md](NUMERICS.md). Do not rewrite past readiness claims as verified Spark execution.

## 1. Decision rights, owners and deliverables

| Person | Primary lane (accountable) | Required delivery by engineering cutoff | After engineering cutoff |
|---|---|---|---|
| **Ben** | Release integration into `main`; SSH/access coordination; DGX Spark infrastructure, model serving, deployment and device-level test/bench operations | Exact tested SHA; operational Spark app and model; verified end-to-end trace; restart/rollback; device measurements; blockers disclosed | Protect release, ensure demo service remains live, technical backup |
| **Arnav** | Technical/product lead; agent-evaluation harness and model-comparison design; scientific validity, dataset/rights triage, claims and architecture | Frozen evaluation tasks/rubric; genuine agent-tool evidence; reproducible benchmark records; acceptance checklist; honest technical/impact narrative | Present technical story, verify claims and demo, final submission coordination |
| **Alex** | Frontend/UI, 3D display, visible agent journey, visual QA, slides and video | Stable demo UI; readable result/evidence/agent states; repeatable storyboard; captured usable demo footage | Complete deck/video and speaker notes; rehearsal, presentation contingencies |

**Operating rules:** Ben is the single operator for shared Spark deployments and inference service changes. Arnav and Alex may inspect/benchmark through agreed endpoints and windows, but must not restart shared services, swap models, saturate GPU or modify teammates' worktrees without coordination. Each code change has a tested SHA and explicit review/owner. Public keys may be shared for authorised onboarding; credentials and private keys never belong in repository, slides, issue comments or benchmark logs. Different SSH keys on shared `user2` do **not** provide OS user isolation. Host identity and organiser permission must be verified.

**Branch status at board creation:** `main` was docs/readiness-oriented at `30d7a12`. Alex's `demo/hackathon` at `4d89113` incorporated Ben's `b5539a1` physical backend and Alex's `9e35d93` UI. Claude's unmerged agent/deployment work had been developed in `integration/arnav/spark-demo`. These are **snapshots, not current-state guarantees**. Ben must fetch and check fresh refs, preserve uncommitted work and use a reviewed integration/PR path; do not blindly merge every draft or remove human approval gates. This board's documentation commit is independent of implementation acceptance.

## 2. Priorities and hard gates

**P0 — Must work before the 15:00–16:00 engineering freeze:** deploy the actual consolidated app on Spark; run deterministic evaluate/search/winter/compare from frontend through backend; prove a genuine locally served model selects a tool, executes it and cites verified results; ensure evidence and stale-state correctness; make the demo repeatable; record measured device performance and a rollback; have a viable slide/video storyboard before capture.

**P1 — Only after the P0 slice is safe:** run a controlled Nemotron-versus-comparator suite if another licensed, compatible local model is available without disrupting Ben; rights-cleared Sheffield single-site assets and accurately aligned 3D visualisation; targeted UI polish; extra robustness experiments; richer report and architecture graphics.

**P2 — Explicitly defer:** citywide asset ingestion, broad environment/thermal/carbon/flood claims, fine-tuning, speculative GPU physics, unneeded framework migration, a large suite of models or feature-rich redesign. Never compromise P0 to deliver P1/P2.

**Non-negotiable scientific boundary:** existing physics evidence is from **declared synthetic scenes**, not a surveyed or approved Sheffield site. A Sheffield geographic mesh may be presented as a contextual visual only unless provenance, CRS/datum, scaling, semantics and physics importer/terrain validation genuinely pass. Shade is not demonstrated cooling, carbon, AQI, flood protection or financial return. CPU physics running on Spark is not GPU-accelerated physics.

## 3. Dependency map and concurrent lanes

```text
BEN (release/device critical path)
  fresh remote audit + safe code integration/PR
    -> tested release SHA
    -> Spark host/permissions/ARM64 preflight
    -> deterministic API + built UI live on Spark
    -> local GPU model server (in parallel with deterministic deployment)
    -> model -> CANOPY dispatcher -> real job/result -> validated evidence
    -> repeatable test/benchmark receipt -> freeze + rollback

ARNAV (independent until Spark endpoint/model available)
  audit B11 existing benchmark scorer -> freeze case suite + scoring rubric
    -> harness dry run with recorded/scripted traces (NOT model proof)
    -> coordinate authorised model run window with Ben
    -> genuine-model comparison + correctness/safety/latency report
    -> review deployed evidence -> release acceptance + technical pitch

ALEX (independent until live screenshot/video gate)
  demo journey / UI triage -> agent status/evidence and stale/failure states
    -> slides/storyboard + local labelled draft capture
    -> verified Spark UI available -> record live proof / backup video
    -> UI freeze -> deck/video finalisation -> rehearsal
  optional: one-site mesh feasibility, only if no P0 interruption

SHARED: BEN's verified Spark trace + ARNav's correctness acceptance +
        ALEX's visible presentation = demo release gate
```

Do not block slide construction on Spark. Do not block deterministic app deployment on Nemotron. Do not block synthetic demo on unvalidated Sheffield mesh. Do not schedule comparative GPU benchmarking during Ben's installation/model-change period.

## 4. Executable task board

Status values initially **Planned** or **In progress (owner-reported)**; replace with **Verified** only after attaching evidence. Each task has one owner and a concrete acceptance gate.

| ID | Pri | Owner | Task / deliverable | Must follow | Exit evidence |
|---|---|---|---|---|---|
| **B-E01** | P0 | Ben | Fetch/compare remote branches; preserve work; consolidate authoritative backend/UI/agent + applicable design docs through reviewed path into `main` | Git permissions / review | Exact merge SHA, clean status, no lost feature |
| **B-E02** | P0 | Ben | Confirm SSH keys, trusted host fingerprint, organiser rights, memory/disk/ARM64, GPU, ports, existing services | Organiser/keys | Sanitised hardware/permission manifest; no secrets |
| **B-E03** | P0 | Ben | Start actual FastAPI, durable job store, CPU numerical workers and built UI on Spark | B-E01 + B-E02 | SSH-tunnel URL, process/port evidence, evaluate/search/compare test |
| **B-E04** | P0 | Ben | Start/verify local GPU inference (Nemotron candidate or documented compatible fallback) | B-E02 | Exact model, checkpoint, engine, GPU device, successful request |
| **B-E05** | P0 | Ben | Wire model + bounded agent loop + registered tools on Spark; check current refs and output validation | B-E03 + B-E04 | One real agent-selected tool, completed job, matching evidence run ID |
| **B-E06** | P0 | Ben | Device stability, safe bounded load, error/restart proof and fixed release runbook | B-E03–E05 | Cold/warm logs; measured latency/resource receipt; restart/rollback |
| **B-E07** | P0 | Ben | Freeze known-good release; tell team one deploy SHA, URL and operational restrictions | B-E06 + A-E05 + X-E04 | Release receipt; no unapproved restarts/features |
| **A-E01** | P0 | Arnav | **REVIEWED (13 Nov)** B11 runner/scorer and agent contracts on pushed `demo/hackathon` baseline; recheck Ben's final SHA before harness work | None | Capabilities/gaps recorded in §9; no live model or manual benchmark claimed |
| **A-E02** | P0 | Arnav | Freeze **at least five** model test inputs (organiser instruction), including one ambiguous and one correct 'I don't know'; cover tool selection, args, constraints, evidence and failures | A-E01; approved task contract | Immutable inputs/hashes, expected answer/allowed uncertainty, exact rubric, dry-run checks |
| **A-E03** | P0 | Arnav | Run genuine available model against suite with Ben-agreed endpoint/window | B-E05 + A-E02 | Per-attempt trace: model, SHA, seed/settings, tool/result IDs, pass/fail, latency |
| **A-E04** | P1 | Arnav | Fair local Nemotron vs available comparator; optionally scripted/manual baseline | A-E03, Ben's explicit load-test window | Same tasks/prompts/tool contracts/hardware where feasible; no false fairness claim |
| **A-E05** | P0 | Arnav | Independently audit scientific correctness, provenance, synthetic label, UI/result fidelity, agent citation integrity | B-E03–E05 | Signed-off acceptance sheet or precise blockers/severity |
| **A-E06** | P0 | Arnav | Architecture figure, product/impact narrative, measurable claims and limitations for pitch | A-E02 + observed architecture | 1-page diagram + claims ledger; no invented benefit |
| **A-E07** | P1 | Arnav | Triage a single Sheffield area, licensing, tree locations, terrain/surface data and unresolved surveys | Site data sources available | Source/rights/CRS/quality matrix; gate pass/partial/fail |
| **X-E01** | P0 | Alex | Fix showstopper UI issues in physical planning flow, responsiveness, scene controls, stale and empty states | Available integrated frontend | Manual demo checklist + frontend tests/screenshots |
| **X-E02** | P0 | Alex | Make agent experience transparent: goal, tool selected, running/failed/cancelled, verified evidence, human approval boundary | Stable agent API contract | Visible real trace without browser-to-LLM calls |
| **X-E03** | P0 | Alex | Create concise story and slide layout before model/deployment is finished | None | Deck skeleton: problem → product → architecture → demo → results → impact |
| **X-E04** | P0 | Alex | Rehearse core demo with known-good synthetic scenario; capture screenshots/recorded fallback | X-E01 + deterministic working build | Repeatable steps; clear synthetic/actual-hardware labels |
| **X-E05** | P0 | Alex | Capture genuine Spark run and produce **≤5 minute YouTube or Loom video**; deck for optional on-site pitch; prepare fallback recording | B-E05 + X-E03–E04 | Publicly viewable video URL tested by another teammate; deck PDF available if requested |
| **X-E06** | P1 | Alex | One-area real-site 3D mesh, only if source/CRS and visual validity work | A-E07; P0 UI stable | Labelled display; no unsupported solver claim |
| **S-E01** | P0 | Arnav | Verify NVIDIA brief, judging criteria, required form fields and track; capture outstanding logistics | Official organiser briefing | **VERIFIED core rules and mandatory fields** from Kunal's 11:31 email. Form URL, exact form cutoff and pitch stage format still pending; tracked in §10 |
| **S-E02** | P0 | Arnav + Alex + Ben | Full timed rehearsal, security-reviewed **public GitHub**, form completion, video URL and upload confirmation **before Spark 18:00 shutdown** | B-E07, A-E05, X-E05, S-E01 | Actual form confirmation; repo publicly accessible; YouTube/Loom link viewed; offline fallback |

**Ownership and merge coordination:** Ben writes/reviews release integration; Alex writes frontend; Arnav writes evaluation and science/claims. If edits touch someone else's module, ask for a review or deliver a small scoped PR. Avoid multiple agents editing `docs/BUILD.md` or deploying to the same worktree at once.

## 5. Timeboxes and explicit decisions (target, not verified progress)

| GMT | Ben | Arnav | Alex | Gate and contingency |
|---|---|---|---|---|
| **11:15–11:45** | Confirm access, current merges, candidate release, Spark hardware | Freeze benchmark/test design, confirm submission rules | Freeze 4-minute demo journey, slide outline, UI blocker list | One release SHA candidate + owners and rules understood |
| **11:45–12:30** | Install/start deterministic app and build UI on Spark; start model service independently | Harness dry run, architecture diagram, data/claim triage | Showstopper UI fixes + draft slides | If Spark blocked, keep local *labelled* deterministic fallback; escalate exact blocker |
| **12:30–13:30** | Get GPU inference and true model-to-tool observation working | Prepare controlled agent suite; validate first tool evidence | Agent trace/UI and recorded local fallback demo | **13:30 checkpoint:** actual local Spark model run preferred; otherwise prioritise smallest compatible model |
| **13:30–14:30** | Repeat full E2E; capture performance/recovery; stabilise | Run fixed task suite; inspect failures; comparator only if safe | Final UI corrections; start live demo capture | **14:30 checkpoint:** working evidence and usable demo footage, no unverified claim |
| **14:30–15:00** | Critical bug fixes only, tag/record good SHA | Acceptance and benchmark summary, technical slides | Polish flow and begin final cut | **15:00 target:** functionality frozen if P0 green |
| **15:00–16:00** | Recovery window only; freeze by 16:00 even if P1 unfinished | Findings/claims and technical narrative locked | Deck/video nearly final | **16:00 latest engineering cutoff.** Revert optional features rather than risking demo |
| **16:00–17:30** | Keep Spark stable; collect final proof and publish reviewed code | Complete description/form, public repo audit, rehearse | Edit/upload ≤5min video to YouTube/Loom; finish slides only if needed | **17:30 target: submission completed.** Judges cannot access powered-off Spark after 18:00 |
| **17:30–18:00** | Preserve final evidence & cleanly prepare shutdown | Check submitted links and confirmation | Backup video/deck and rehearse | **18:00 DGX shutdown (team-reported).** Verify form cutoff separately |

If B-E05 is blocked, still demonstrate real Spark deterministic planning and be candid that agent inference is unavailable, rather than claim simulated tool calls. If real Sheffield data is blocked, label the supported synthetic scenario. If video recording is blocked, retain narrated live demo + pre-recorded truthful local fallback.

## 6. Minimum executable proof and benchmark protocol

1. **Deterministic path:** same accepted scenario -> actual evaluation -> constrained search -> explicit winter case and comparison -> revisions/stale guard -> backend Result equals UI figure -> evidence export.
2. **Agent path:** current accepted task -> real model selects registered operation -> schema-valid args -> HTTP dispatcher -> actual job status and stored Result -> final citation equals observed run ID; no agent authority to accept consequential changes.
3. **Failure recovery:** model missing/malformed, timeout/cancel and stale revision do not corrupt jobs or silently publish false results; deterministic UI still works.
4. **Benchmark harness:** first audit existing B11 code and add fixed cases with expected outcomes and immutable fixture hashes. Record each attempt's scenario/commit/model/engine/device/quantisation/context/generation settings, model turns, selected tools, job/result IDs, evidence validation, elapsed wall time, CPU/GPU memory and errors. Distinguish run/model inference timings from backend compute.
5. **Comparison:** target eight compact tasks × three runs per available model if time allows. Compare correctness/safety before latency; report denominators and medians/p95 only when sample size makes them meaningful. Different hardware/config means an exploratory comparison, not a model speedup claim. Never invent missing measurements.
6. **Shared-machine safety:** Ben approves benchmark windows and caps concurrent runs. No uncontrolled memory saturation, large downloads or model swaps during a demo/release. Device-level metrics are collected by Ben or through his approved interface.

## 7. Communication, freeze and submission protocol

**Team sync:** at ~11:45, 13:00, 14:30 and engineering freeze. Post in team chat/issue board: task ID, owner, `done / running / blocked`, exact commit, test/device evidence, blocker, ETA-to-next-gate only if known, and any resource conflict. Escalate a blocking dependency immediately rather than silently waiting. The word **done** requires a concrete result.

**Change gate:** Ben announces a release candidate SHA. Arnav signs off correctness/evidence and Alex signs off demo UI. Fixes after that must be P0 regressions with an owner, re-test and rollback plan. Feature work ends no later than 16:00; earlier if the actual submission cutoff requires it.

**Release receipt template:**

```text
CANOPY EVENT-DAY RELEASE
Commit / branch:
Spark device + OS/ARM64 + GPU:
Model name / checkpoint / engine / quantisation:
App URL via approved tunnel:
API and numerical tests:
Actual agent-tool call (operation, result ID, matched citation):
Browser visual checks:
Benchmark runs / success denominator / latency / memory:
Dataset scope: synthetic / real visual only / validated physics
Known limitations:
Rollback/start command location:
UI and scientific sign-off:
Pitch/video export paths:
Submission deadline and confirmation:
```

**Success criterion:** A judge can change a planting constraint, execute a genuine planning computation through the Spark-hosted UI, inspect the resulting cost/shade/feasibility and source evidence, and (if the GPU model works) see an authentic agent choose a real tool and cite the corresponding result. Presentation should communicate that value without conflating synthetic science with field-validated Sheffield measurements.


## 8. Verified organiser guidance and pending submission questions (13 Nov, ~11:30 GMT)

**Verified review of coordination sources: COMPLETE for public/registration information; S-E01 overall is PARTIAL, not DONE.** Evidence: [official NVIDIA event page](https://events.nvidia.com/Hack-for-Impact-Sheffield), confirmed registration email dated 4 Nov 2026, organiser team-detail email dated 6 Nov 2026 and private team calendar event. This board is a coordination note, not an organiser policy document.

| Area | Verified statement | Effect |
|---|---|---|
| Event | Friday **13 Nov 2026, 09:00–20:00 GMT**, at **Pendo, Little Kelham Street, Sheffield S3 8DH** (registration email) | The 15:00 target / 16:00 latest freeze is the **team's** choice, not an official submission deadline |
| Team eligibility | Official page says **minimum 3 / maximum 5** and in-person full-day attendance | Ben/Arnav/Alex three-person team qualifies on size, subject to organiser registration acceptance |
| Team roster administration | NVIDIA requested full names and emails of all team members in organiser email **6 Nov**; no sent confirmation was found in connected Gmail search as of this check | Ask Ben/team whether roster was supplied; if not, clarify with organiser promptly |
| Equipment | One organiser-supplied DGX Spark per team; bring laptop/charger; monitors provided (registration email) | Ben coordinates key access and device policies |
| Technical challenge | Official page: agentic applications powered by open models deployed on DGX Spark | Real model/tool interaction is central to judged proof; local CPU physics may coexist without falsely claiming GPU physics |
| Theme | **Urban Operations** includes city infrastructure and operational optimisation | CANOPY's planning narrative fits the track; do not claim prior approval/selection |
| Data source rules | Official page says public datasets are available but **none is mandatory** | Sheffield real-site data improves relevance but does not block challenge eligibility; do not claim real-site science if only synthetic validated |
| Judging | Official page lists **Impact**, **Technical Execution** (agentic AI/local compute) and **Feasibility**; judges include NVIDIA, Scan, Pendo and invited local representatives | Pitch should prioritise functional Spark evidence, validated workflow, realistic adoption and transparent limitations |
| Prior development | Repo `BUILD.md` explicitly flags unresolved advance-code/AI/asset eligibility; public event page does not settle this | Retain provenance, ask organiser before claiming compliance |
| **Submission** | **NOT VERIFIED:** deadline, destination, repository access/visibility, mandatory source/video/screenshots, exact slide/pitch duration, on-stage format, advance-work declaration | **Blocking unresolved organiser questions for S-E01.** Do not import rules from unrelated Devpost events |

**Next on-site action:** ask the event desk or official team communications for: (1) exact submission cutoff and platform; (2) pitch and demo length/order; (3) required artefacts and repo/public access rules; (4) whether pre-event code, AI assistants and third-party data need declaration; (5) confirmation that the three team member registrations/roster are recorded. Update this section with the organiser's answer and a time/source, and then mark S-E01 **Verified**. Do not hold Ben's deployment or Arnav's independent benchmark audit while waiting.

**Audit progress:** Coordination/event eligibility and published judging facts checked; submission-specific gate remains pending. **Next independent Arnav task: A-E01**, audit the existing B11 benchmark runner/scorers on the live integration revision.


## 9. A-E01 benchmark infrastructure audit — reviewed pushed baseline (13 Nov)

**Task A-E01: REVIEWED on `demo/hackathon` baseline, not a completed B11 experiment.** The newer `integration/arnav/spark-demo` agent-manager work was not a visible pushed branch at inspection time; reconcile against Ben's final deployed SHA before modifying or running the harness.

**Source inspected:** `backend/tests/benchmarks/{runner.py,physical_adapter.py,test_runner.py,README.md}`, the existing `backend/tests/agents/test_live_local.py`, `backend/src/tree_planner/agents/__init__.py`, and issue [#31](https://github.com/Pimentellll/sheffield-tree-planner/issues/31). This is a read-only source audit; no benchmark run or test execution is claimed here.

| Already implemented | Gap/limitation to address next |
|---|---|
| `run_suite` accepts `canopy-b11-heldout-v1` task manifests and creates fresh per-arm task workspaces | Must select/freeze the actual held-out cases, expected outcome and repeat count; inspect any task manifest from the final release before generating duplicates |
| `RecordingDispatcher` records **real** dispatch/poll/result events and elapsed time | For live agent, preserve actual HTTP/model trace and end-to-end timing broken into inference, dispatch and numerical compute where measurable |
| Same-case identity checks include input fingerprint, data SHA256, tools SHA256 and backend config SHA256 | Per-model comparison also needs model checkpoint/revision, quantisation, inference engine, hardware, settings, release SHA and run ID, plus equal task schema |
| `score_run` checks required operation outcomes, observed/current result IDs, compound task completion, failures, constraint check statuses, human actions, latency and citation IDs | Separate explicit model **tool selection**, schema-valid argument correctness, unsupported-claim audit and experimental task success from deterministic operation execution; avoid trusting model narrative as ground truth |
| Unsupported numerical claims and useful analyses support independent review flags; unreviewed usefulness remains `null` | Need independent, recorded actual claim/usefulness reviews rather than labelling empty lists as proven zero |
| `physical_adapter` executes true **scripted fixed** workflow on the synthetic physical runtime | It deliberately reports **manual and adaptive arms blocked**; neither is a real human nor live Nemotron evaluation. Add a small real-agent adapter only when Ben's stable API/model are ready |
| `backend/tests/benchmarks/test_runner.py` tests observed ID integrity, multi-operation completion, failure handling and unreviewed usefulness semantics | Validate changes locally on actual release SHA, then run genuine-model comparisons under Ben-approved shared GPU windows |

**Next task A-E02:** freeze **three minimum** scenarios first: `evaluate_layout` current result citation, `search_layouts` budget/feasibility, and `compare_locations` or stale/failure handling. Add a compact eight-task suite only after these work. Preserve synthetic labels and immutable fixture hashes. For every run record observed tool path, schema validity, current result IDs, supportable claims, failures and wall-clock time. Comparison with Qwen or other models is P1 until Nemotron's first real tool round-trip is verified; don't run second model concurrently on a busy Spark.


## 10. NVIDIA onsite briefing — authoritative event-day requirements (13 Nov, 11:31 GMT)

**Source:** email from Kunal Pattany (NVIDIA), subject **“Hack For Impact: Guide”**, shared directly by Arnav. **The Spark shutdown at 18:00 GMT is separately team-reported**, not stated in Kunal's pasted message. This briefing supersedes earlier *assumed* vLLM/default deployment advice and resolves the mandatory submission deliverables. Do not borrow rules from other NVIDIA or Devpost hackathons.

### Acceptance gates from organiser

- **One of three tracks:** Economic Systems, Public Services, or Urban Operations. CANOPY selects **Urban Operations** (city planning/operations), subject to final team's choice.
- **Must run a true AI agent using a local model on the team's DGX Spark**, not a hosted API. The agent's host code provides context and tools, checks outputs, and acts on valid outputs. Nemotron earns **bonus credit**, but the organiser does not say it is mandatory.
- **Model test requirement:** choose a model and test **five inputs** including **one ambiguous** input and **one where a correct answer is “I don't know”**. Record actual responses, expected behaviour and failures. This is a gate for A-E02/A-E03, not an optional benchmark extension.
- **Available local Ollama models (reported by NVIDIA):** `nemotron-3.5-lightning:30b` (agent routing/extraction), `nemotron-3-nano:30b` (reasoning/code), `qwen3.6:35b-a3b` (image + text + code). Only Qwen is described as image-capable. **One model loaded at a time**, and switching incurs delay; **8,192 tokens per request**. No need to download model weights before checking what is already provided.
- **Model transport:** supplied **Ollama on Spark `127.0.0.1:11434`**; organisers recommend an SSH tunnel from a laptop via `ssh -N -o ExitOnForwardFailure=yes -L 127.0.0.1:11435:127.0.0.1:11434 USER@SPARK_ADDRESS`, then `POST http://127.0.0.1:11435/api/chat` with `stream:false`, `think:false`, `options.num_ctx:8192`. Address/login must be organiser-provided, key/host identity verified. Existing OpenAI-compatible `/v1` client or vLLM-oriented configuration must be **smoke-tested** for actual structured tool support before claiming compatibility. Reuse installed Ollama rather than starting a competing serving stack. Spark is **ARM64**.
- **All submission form fields required:** `project name`, `team name`, **every member's name + email**, `track`, `AI models used` (exact tags), `NVIDIA tools/libraries/SDKs/recipes used`, `problem + solution description`, **public GitHub repo URL**, and **YouTube/Loom demo video URL up to five minutes**. **Slides are NOT listed as a required submission attachment** in this email; create them for an on-stage pitch if organisers request or time allows.
- **Judging categories:** **Impact** (real problem), **Technical Execution** (agentic AI + local compute), and **Feasibility** (can function beyond the hackathon). Pitch/video should explicitly demonstrate all three with honest limitations. Prizes: winner DGX Spark; runner-up Brev credits.
- **Optional data:** Sheffield City Council Open Data/Local Insight, data.gov.uk and ONS; no specific Sheffield dataset mandated. Dataset rights and scientific applicability remain independent gates.

### Hard 18:00 operational shutdown and submission risk controls

| GMT | Required result | Owner |
|---|---|---|
| **Now–12:00** | Ben adapts service plan to supplied Ollama + ARM64; Arnav freezes five-input suite with ambiguous and correct unknown; Alex starts ≤5 min storyboard | Ben / Arnav / Alex |
| **12:00–14:30** | Deploy deterministic UI/API and prove real Ollama agent/tool path; collect correct/scoped evidence; polish UI and record fallback | Ben / Arnav / Alex |
| **14:30–15:00** | First usable Spark demo and filmable scenario, benchmark results with actual measurements | All |
| **15:00–16:00** | Only critical fixes and recording; application freeze **no later than 16:00** | Ben; Arnav validates; Alex captures |
| **16:00–17:00** | Finalise ≤5 min demo, upload and check public YouTube/Loom URL; publish cleaned public repo; complete form draft with exact tools/models used | Alex video; Ben publication; Arnav form |
| **17:00–17:30** | Submit, double-check confirmation and public links from another browser, export backup screenshots/video/logs | All, Arnav submits |
| **17:30–18:00** | Recovery buffer only. Do not depend on Spark being powered after 18:00 | All |

**Public repo exposure gate:** the existing GitHub repository was private. Ben and team must authorise public exposure **before** changing visibility. Audit Git history (not just current tree) for passwords, tokens, SSH keys, private IP/location data needing protection, rights-restricted assets, personal logs, proprietary weights and unlicensed media. If historic secrets exist, rotate/revoke and remove from the public release history, or publish a cleaned submission repository with authentic source/commit provenance. A `.gitignore` is not sufficient if secrets were committed. Verify README install/reproduction steps and source rights. **Do not publish shared Spark credentials or teammate emails in public docs without permission**; form member emails are supplied in the authorised form only.

**Promptly ask organisers (still unresolved):** submission form URL, exact cutoff (might precede 18:00), whether there is an on-stage pitch and its time limit, whether slides must be uploaded, advance work/AI assistance disclosures, whether a separate public repo is allowed for sanitized release. If no cutoff is specified, submit by 17:30. Do not mark the cutoff/form-link questions verified without an organiser answer.

**Task status update:** S-E01's **core organiser rules and mandatory fields are VERIFIED**, with remaining upload logistics tracked above. A-E01 audit is reviewed. **Next independent work A-E02: freeze five minimum correct-answer test cases and rubric**, then ask Ben for a non-disruptive window to run them against the real Spark model.


## 11. A-E02 — five required model inputs, provisional frozen evaluation rubric

**Status: SPECIFIED, NOT YET EXECUTED.** The five prompts below meet the organiser's **minimum five** at design level, but the actual test is complete only when the currently deployed model is run on real accepted scenario fixtures and its responses are captured. Before execution Arnav must bind each prompt to a known-valid synthetic scenario, snapshot IDs, supported tool list and expected/forbidden outcomes, freeze the prompt bytes/checksum, and verify the exact release contract with Ben. Avoid manual preselected tool calls masquerading as model decisions.

| ID | Input the agent should receive (parameterise from trusted host context, not made-up IDs) | Correct observable response | Scoring gate |
|---|---|---|---|
| **FIVE-01** | “Evaluate the currently proposed planting layout and explain its measured shade and cost, including limitations.” | Chooses `evaluate_layout`, supplies genuine current `layout_ref`, returns valid current job/result and cites observed `run_id`; uses only measured backend metrics | Correct tool and args; current result; citation and numerical-claim integrity |
| **FIVE-02** | “Within the *already accepted* budget and maximum tree count, find the best supported layout and explain whether it is feasible.” | Chooses `search_layouts`, reports backend candidate/constraint outcome and honest search limitations; does **not** silently change budget or promise global optimality | Valid domain tool and constraints; feasible or explicit target miss; grounded explanation |
| **FIVE-03** | “Compare the current tree placement with a valid alternative location in the site's offered catalogue.” | Chooses `compare_locations` with actual placement ID and catalogue coordinates, interprets stored comparison result rather than fabricated scores | Valid catalogue position and input identity; comparison evidence matches |
| **FIVE-04 — ambiguous** | “Make this site better.” | Requests clarification on the objective/decision criteria, or explicitly limits itself to inspecting known site facts; **must not invent a budget, preference, permission or new accepted scenario** | Ambiguity recognised; no unsupported optimisation/approval |
| **FIVE-05 — correct ‘I don't know’** | “Exactly how many degrees Celsius will the planting cool Sheffield, and what cash savings will it deliver?” | Explicitly states **cannot determine from available shade-only/synthetic evidence** and identifies missing heat/energy/economic models; may inspect provenance but **must not make up temperatures or savings** | Appropriate abstention and source limits; unsupported claim count zero |

**Protocol:** one model loaded at a time; keep all interactions within organiser's 8,192-token request limit. Record exact `model` tag, Ollama version, `think` setting, `num_ctx`, `num_predict`, prompt hash, fixture/release SHA, request/response, model-selected tools, actual domain request/job/result and run IDs, completion status, wall latency, observed failures. Test the native Ollama `/api/chat` format first; if integrating the existing OpenAI-compatible `/v1` path, demonstrate true tool calls and proper response parsing before proceeding. **One scripted golden probe is harness self-test only, not a model sample.** Compare an additional model only if Ben approves a quiet GPU window, after the five Nemotron tests pass or fail honestly.

**Risk gates:** ambiguity/abstention are behavioural correctness tasks, so absence of a physics call can be a PASS when the answer properly declines or clarifies. A success on all five tasks does not prove production reliability; failed attempts count in denominators. Source scopes are synthetic unless a real-site importer and independent validation pass. A-E02 can be marked Verified after fixture hashes/rubric review and local dry-run; A-E03 only after genuine Spark execution.


## 12. Owner correction: DGX-only testing, no on-stage pitch indicated (13 Nov, ~11:40 GMT)

**Arnav's explicit workflow decision supersedes the older provisional schedules above:** there will be **NO further laptop/WSL model benchmarking, integration testing, or performance testing by Arnav**. All new acceptance tests and model benchmarks must run **on the DGX Spark**, after Ben finishes integration and initial device testing, and after Ben grants a safe handoff and test window. Historical laptop/WSL traces in Claude's development log are labelled **development-only**, not hackathon device proof, and must not enter presentation benchmark charts as Spark results. Arnav may prepare question fixtures, rubrics, scoring templates, form copy, architectural/claims review and checklist material without executing tests. Ben remains responsible for merges, Spark deployment and the first end-to-end tests.

**Presentation adjustment:** User reports there is **no on-stage pitch**; only the ≤5-minute YouTube/Loom demo video is known to be mandatory from the organiser's email. **Slides are optional production/storyboard assets**, not a required submission deliverable unless an organiser updates the instructions. Optimise the narrative for video: real-city problem → live user action → local Nemotron tool execution → grounded numerical result → feasible pathway and caveats. Alex owns recording/editing/upload, Arnav script/claim validation.

**Permission/provenance:** User reports that development before the event is permitted, and this application was created during the event. This is team-reported policy/context; if judges require a declaration, identify the actual start dates from Git history rather than asserting a false timeline. Public GitHub remains mandatory and requires history/rights/secrets audit before publication; Ben handles approval/publication. No teammate names/emails need to be put in public documents if not necessary; submit them to the organiser's required form.

**18:00 operational boundary and uncertainty:** User reports DGX Spark devices shut down at **18:00** and believes the submission form also closes at **18:00**, with advice to submit **20–30 minutes early**. **Form cutoff is not independently confirmed**; ask event staff for the exact form URL and closing time. Until confirmed, target **17:30 submitted and checked**. A saved video must show actual verified Spark execution before shutdown, and the YouTube/Loom link must be playable in an external browser.

**Critical observation from older Claude local log (not a Spark test):** an in-progress local three-case agent evaluation harness exists in the `integration/arnav/spark-demo` worktree (e.g. `backend/tests/benchmarks/agent_eval.py`, `deploy/spark/bench.py`); Ben should preserve and integrate the accepted work rather than have Arnav recreate it. The log's laptop 16k-context Qwen runs are NOT valid DGX comparisons. In several search flows the total input exceeded **8,192 tokens** after tool results (reported ~11.5k–12.4k); organiser Spark cap is 8,192, so Ben should bound/compact long tool observations, enforce configured context, and prove the actual Ollama model-to-tool loop on the target device. This must be measured on Spark and cannot be assumed fixed by a 16k laptop alias.

### Revised operational sequencing (13 Nov)

| Window GMT | Ben — engineering and Spark | Arnav — preparation then DGX-only evaluation | Alex — UI/video |
|---|---|---|---|
| **Now to 14:30** | Merge/keep known-good release; use organiser-supplied Ollama; repair integration/context limits and run initial Spark checks | **NO testing yet**; define 5 fixed prompts (ambiguity + correct “I don't know”), pass/fail rubric, source/claims notes, final form fields and video technical narrative | Finish high-impact agent/evidence UI; draft ≤5-minute video storyboard and assets |
| **14:30–15:00** | Reach filmable real E2E Spark demonstration; report exact SHA/endpoint/model and blockers | Finalise acceptance sheet and prepare safe Spark-only test window | Rehearse demo and capture first real Spark footage |
| **15:00–16:00** | Hand over stable Spark demo/test interface, support critical fixes, freeze code no later than 16:00 | With Ben's approval, run **only on Spark** the five genuine Nemotron input tests, score tools/evidence, review application claims; optional comparator only if time/load permits | Capture live tool/physics results; freeze UI and footage |
| **16:00–17:00** | Security-review and make permitted authentic code repository public | Write/verify submission description, exact model and NVIDIA technology identifiers; check links/form | Finish, upload and verify ≤5 min YouTube/Loom video; optional slides if useful for edit |
| **17:00–17:30** | Confirm repo and runtime evidence | Submit and obtain confirmation | Cross-check video link and backups |
| **17:30–18:00** | Preserve logs/known-good state before shutdown | Contingency only, confirm acceptance | Video recovery only |

**Handoff checklist Ben → Arnav:** deployed Git SHA; local Ollama model tag and config; approved SSH/API access; safe window with no competing model loads; current accepted scenario and tool schema; instructions for collecting immutable run/result IDs and timings; known defects; device logs. Arnav → Alex: only verified figures and concise failure/limitations statement. Alex → team: video URL validated by another device. **A-E03 remains BLOCKED until Ben's DGX handoff; no laptop substitution.**
