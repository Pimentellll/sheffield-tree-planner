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
| **A-E01** | P0 | Arnav | Review `backend/tests/benchmarks/` B11 runner/scorer and existing agent test contract, reuse instead of replacing | None | List of existing capabilities/gaps; stable test case format |
| **A-E02** | P0 | Arnav | Freeze small scored scenario suite: tool selection, valid args, budget, comparison, evidence, unsupported claims, stale/failure cases | A-E01 | Immutable inputs/hashes, expected outcome, exact rubric, dry-run checks |
| **A-E03** | P0 | Arnav | Run genuine available model against suite with Ben-agreed endpoint/window | B-E05 + A-E02 | Per-attempt trace: model, SHA, seed/settings, tool/result IDs, pass/fail, latency |
| **A-E04** | P1 | Arnav | Fair local Nemotron vs available comparator; optionally scripted/manual baseline | A-E03, Ben's explicit load-test window | Same tasks/prompts/tool contracts/hardware where feasible; no false fairness claim |
| **A-E05** | P0 | Arnav | Independently audit scientific correctness, provenance, synthetic label, UI/result fidelity, agent citation integrity | B-E03–E05 | Signed-off acceptance sheet or precise blockers/severity |
| **A-E06** | P0 | Arnav | Architecture figure, product/impact narrative, measurable claims and limitations for pitch | A-E02 + observed architecture | 1-page diagram + claims ledger; no invented benefit |
| **A-E07** | P1 | Arnav | Triage a single Sheffield area, licensing, tree locations, terrain/surface data and unresolved surveys | Site data sources available | Source/rights/CRS/quality matrix; gate pass/partial/fail |
| **X-E01** | P0 | Alex | Fix showstopper UI issues in physical planning flow, responsiveness, scene controls, stale and empty states | Available integrated frontend | Manual demo checklist + frontend tests/screenshots |
| **X-E02** | P0 | Alex | Make agent experience transparent: goal, tool selected, running/failed/cancelled, verified evidence, human approval boundary | Stable agent API contract | Visible real trace without browser-to-LLM calls |
| **X-E03** | P0 | Alex | Create concise story and slide layout before model/deployment is finished | None | Deck skeleton: problem → product → architecture → demo → results → impact |
| **X-E04** | P0 | Alex | Rehearse core demo with known-good synthetic scenario; capture screenshots/recorded fallback | X-E01 + deterministic working build | Repeatable steps; clear synthetic/actual-hardware labels |
| **X-E05** | P0 | Alex | Capture verified Spark run, edit video, polish deck, prepare speaker and failure fallback | B-E05 + X-E03–E04 | Complete video, exported slide PDF, screenshots, narrated demo |
| **X-E06** | P1 | Alex | One-area real-site 3D mesh, only if source/CRS and visual validity work | A-E07; P0 UI stable | Labelled display; no unsupported solver claim |
| **S-E01** | P0 | Arnav | Confirm organiser deadline/pitch length/video format/repo deliverables + assign team speakers | Organiser | Submission requirements captured and acknowledged |
| **S-E02** | P0 | Arnav + Alex + Ben | Full timed rehearsal, show hardware/evidence receipt, freeze and submit | B-E07, A-E05, X-E05, S-E01 | Submission confirmation + offline fallback copies |

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
| **16:00 onward** | Keep live service healthy; no feature churn | Pitch/rehearsal/submission and questions | Final video/slides/PDF/export and rehearsal | Organiser deadline overrides all; submit with buffer |

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
