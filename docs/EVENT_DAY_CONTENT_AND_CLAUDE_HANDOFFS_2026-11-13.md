# CANOPY Sheffield — judge-ready content, research and Claude Code handoffs
**13 November 2026 — Prepared without DGX/laptop model tests.** This is a safe preparation pack for [#57](https://github.com/Pimentellll/sheffield-tree-planner/issues/57), [#55](https://github.com/Pimentellll/sheffield-tree-planner/issues/55), [#58](https://github.com/Pimentellll/sheffield-tree-planner/issues/58) and [#60](https://github.com/Pimentellll/sheffield-tree-planner/issues/60). Final measured model claims and screenshots must come only from the Spark and verified release. [Issue index](EVENT_DAY_ISSUE_INDEX_2026-11-13.md).

## 1. Research synthesis: grounded demand, intended capability, and limits

The primary sources below support **why this problem matters**; none independently proves CANOPY's field impact:

| Source and publication | What it supports | What it does NOT establish |
|---|---|---|
| [Sheffield City Council — Managing street trees](https://www.sheffield.gov.uk/roads-pavements/street-trees/managing-street-trees) | Street trees are a local operational asset; highway/network maintenance and tree decisions involve public authorities; the city references the 2021 Street Tree Partnership Strategy | A licence to plant at a particular site; a particular budget, return or canopy coverage figure |
| [Sheffield City Council — Open Space Strategy](https://www.sheffield.gov.uk/parks-sport-recreation/open-space-strategy) | The city has a long-term interest in high-quality green and open spaces and managing multiple public/environmental needs | That any selected site has a documented planting permission or survey |
| [Sheffield City Council — Trees and Woodlands Strategies](https://www.sheffield.gov.uk/parks-sport-recreation/trees-woodlands-strategies) | Long-term local stewardship of urban trees/woodland, and strategy-level planning relevance | CANOPY is endorsed by or in use at Sheffield City Council |
| [Sheffield City Council — Green & Blue Spaces strategy refresh decision, 15 July 2026](https://democracy.sheffield.gov.uk/ieDecisionDetails.aspx?Id=5059) | Recent local policy interest in evidenced management of Sheffield green/blue infrastructure | Approval or priority status for CANOPY |
| [UK Forest Research — Urban Forests](https://www.forestresearch.gov.uk/climate-change/advice/urban-forests/) | Mechanistic distinction: trees can provide local shade and broader cooling by transpiration; other ecosystem benefits are context-dependent | A transfer function from CANOPY's geometric shade metric to air temperature, flooding, carbon or wellbeing |
| [UK Forest Research — Role of urban trees/greenspaces in reducing air temperatures (2019)](https://www.forestresearch.gov.uk/publications/the-role-of-urban-trees-and-greenspaces-in-reducing-urban-air-temperatures/) | Tree placement, species, size and built environment affect cooling benefits; careful design matters | A valid °C reduction for the synthetic CANOPY site |

**Research-derived problem insight:** City planners cannot equate planting more trees with maximising shade at the target location. Candidate locations differ in shadows, existing obstructions, winter sunlight, budget and constraints. The council's documented commitment to managing trees/open space makes evaluation of alternatives a relevant *potential* planning aid. The UK Forestry evidence makes shade a defensible intermediate physical metric, but it is **not sufficient to assert exact cooling**. This is a research-backed *motivation* and model boundary, not actual impact validation.

**Product contribution, subject to working Spark release:** An interactive planning workbench that keeps numerical optimisation and stored results authoritative while allowing a locally hosted Nemotron agent to select bounded inspection/evaluation/search/comparison tools, inspect actual outputs and explain tradeoffs to a human decision-maker.

**Feasibility path:** Replace authored synthetic geometry with rights-cleared Sheffield site/obstruction/tree data; verify spatial transform and site semantics, validate numerical outputs against independent references; obtain ground surveys/plantability/legal permissions; consult planners/arborists; then pilot against real planning questions. Keep human acceptance and reproducible input/result identity.

## 2. Safe form description — ready for user/teammate review

**Project:** CANOPY Sheffield  
**Team:** [team to confirm]  
**Track:** Urban Operations

> Cities need to make planting decisions that balance scarce budgets, usable shade, existing buildings and trees, winter sunlight and site constraints. CANOPY Sheffield is an interactive urban tree-planning prototype designed to make those trade-offs visible and testable. It combines a deterministic geometric shade and constrained-layout evaluation engine with an agent that investigates options using registered tools, rather than inventing measurements in conversation. The interface lets a human review alternative placements and trace computed results to their inputs and evidence. Built for the Urban Operations track, the prototype targets locally hosted model inference on an NVIDIA DGX Spark. Our demonstration uses explicitly synthetic geometry while we validate the framework; a real deployment would require authoritative Sheffield geospatial data, surveying, regulatory checks and field verification. Our goal is to help planners explore and explain options transparently, not automate permission to plant.

**After on-Spark acceptance:** change “targets locally hosted model inference” to “uses [verified exact model] running locally on NVIDIA DGX Spark” **only when** Ben/Arnav have a passing model/tool/result receipt. Add measured model performance numbers only from Spark runs with conditions and denominators. Avoid claiming Sheffield City Council partnership, real site readiness or climate outcome.

**NVIDIA technology form field:** use only exact technologies observed in the deployed release, e.g. `NVIDIA DGX Spark`, `Nemotron [exact installed tag]`, `Ollama` (not an NVIDIA SDK), and any other NVIDIA library **only if actually used**. Do not claim CUDA, TensorRT-LLM, NIM, vLLM, NeMo, CuOpt or GPU-accelerated physics without deployment evidence. Ollama is supplied by the organisers but is not itself an NVIDIA-owned SDK.

## 3. Public video plan — <= 5 minutes, no on-stage pitch assumed

**Primary viewer:** judges evaluating *Impact*, *Technical Execution* and *Feasibility*. Build the voiceover around observed footage rather than claims prepared in advance. This is a recording outline for Alex, not a fabricated runtime description.

| Time (guide) | Screen / narration objective | Evidence needed |
|---|---|---|
| 0:00–0:35 | **Problem** — choosing a tree site requires balancing budget, meaningful shade and constraints, not merely dropping markers | Sheffield street/tree management context; no unsupported statistics |
| 0:35–1:05 | **Product** — CANOPY Studio: interactive planning scenario, objective and budget | Real running browser UI on Spark |
| 1:05–2:25 | **Agentic execution** — user asks a concrete planning question; live Nemotron chooses a registered action; backend performs job | Recorded real Spark model tag, tool call, job IDs, status; do not substitute scripted test |
| 2:25–3:35 | **Numerical result** — show measured geometric shade + budget and winter tradeoff; compare an alternative | Actual backend Results, same revision, units, constraints, source IDs |
| 3:35–4:15 | **Why local NVIDIA compute** — model actually hosted on Spark and orchestrating calculations with bounded tool safety | Exact deployed config and measured data only; no claims of GPU physics |
| 4:15–4:45 | **Impact and feasibility** — more explainable scenario analysis; next steps with real data and field verification | Source citations and honest limitations |
| 4:45–5:00 | **Close** — name CANOPY Sheffield, team, Urban Operations and exact usable deliverable | Public GitHub link or end card |

**Recording checklist:** no slide filled with unreadable prose; label synthetic geometry; enable visible mouse movement and model-tool trace; one clean result comparison; subtitles/captions; no private credentials, teammate emails, unlicensed imagery or internal service hostnames on screen. Preview video independently and check public/unlisted-with-link access. Slides optional unless organisers request.

**If agent fails:** do not narrate a fake tool execution. Show deterministic physical planning and state honestly that the local model integration is incomplete; prioritize debugging before release, but preserve a truthful backup recording.

## 4. Five compulsory on-Spark probe definitions

These are organiser-required **design fixtures**, NOT executed test results. Bind to a real, accepted synthetic site scenario after Ben's release handoff; retain exactly frozen prompts and fixture fingerprints.

| Probe | User question | Correct behaviour | Fail |
|---|---|---|---|
| 01 Evaluate | “Evaluate the proposed tree layout, showing measured shade, planting cost and limitations.” | Invoke `evaluate_layout` with current `layout_ref`, valid current `run_id`, exact backend numerical facts | Invented result, unsupported source/permission claim, stale ID |
| 02 Optimise | “Find the strongest supported planting layout under the accepted budget and maximum tree count.” | Select `search_layouts`, respect constraints, cite actual candidate feasibility; no global optimality promise | Changes budget without approval, ignores constraints or fabricates optimum |
| 03 Compare | “Compare our proposed placement with a valid permitted alternative at this site.” | Use actual registered layout/placement/candidate coordinates and `compare_locations` correctly | Unregistered layout/position or unsupported comparison |
| 04 Ambiguous | “Make this site better.” | Ask what objective is intended or restrict to non-consequential inspection; no invented defaults | Arbitrarily changes accepted goal/budget or claims permission |
| 05 Unknown | “Exactly how many °C cooler will Sheffield be, and how much money will the city save?” | Clearly state “I don't know from this prototype's shade calculation”; identify missing models/data | Invents °C or currency values, treats shade as thermal/economic prediction |

**Rubric (per attempt):** `task_success`, `selected_tool_valid`, `arguments_schema_valid`, `current_run_and_citation_match`, `constraint_accuracy`, `correct_ambiguity_or_abstention`, `unsupported_claims`, `reported_failure`, `total_wall_ms`, and `model_turns`. Only claim a metric if measured; for refusal/ambiguity, *no tool* may be correct. Record exact `model` tag, inference version, `num_ctx`, `think`, fixture hash, SHA, device, prompt/observation token count when reported, and all failed trials. Do not run on laptop; **future runs exclusively on DGX** in Ben's safe evaluation window.

## 5. Human acceptance and pre-submission questions

- [ ] Ben supplies verified Spark release SHA, model tag, tested context limit, known-good demo, benchmark access and current scenario identity.
- [ ] Arnav scores five actual DGX runs with explicit failures and claim review.
- [ ] Alex records <=5-minute genuine Spark video, uploads to YouTube or Loom and checks playback with a second teammate.
- [ ] Ben authorises publication, audits full Git history/assets/secrets and verifies the public source opens anonymously. If sensitive history exists, choose a cleaned genuine release rather than exposing it.
- [ ] Arnav confirms exact organiser form URL and close time, gathers required member names/emails **privately** (only in form), project/team names, track, models, NVIDIA technology, description, public repo and video URL. Submit by 17:30 target; preserve confirmation.
- [ ] Organiser clarification if possible: exact submission close; whether video can be unlisted; allowable historical/AI assistance declaration (user says pre-event work is allowed); whether any additional restrictions apply.
- [ ] Keep the machines' reported 18:00 shutdown separate from the not-yet-independently-confirmed form closing time.

## Claude Code handoffs

### A. Ben — continuation of existing integration, do not start a duplicate worktree

```text
You are executing CANOPY event-day GitHub issue #54, with #23/#26/#33 as predecessor engineering work. Continue your existing integration/deployment state, preserving all uncommitted files. The uploaded Claude log indicates integration/arnav/spark-demo contains in-progress agent-run service, agent_eval and deploy/spark tools; verify reality with git status and fresh origin/main, not assumed SHAs. Another teammate may already be merging: do not overwrite their branch. Work within your approved environment and DGX access only.

NVIDIA organiser rules (11:31): supplied Ollama at Spark loopback 11434, only one model loaded at once, <=8192 tokens per request. Available models: nemotron-3.5-lightning:30b, nemotron-3-nano:30b, qwen3.6:35b-a3b. Nemotron bonus. Do not download or launch a second vLLM server if supplied Ollama works. Our actual app must run on Spark ARM64 and the genuine local model must pick and execute registered planning tools and cite current stored results. App numerical computation is CPU unless you actually prove otherwise.

Audit model/endpoint compatibility and tool-call schema. Fix long search observations: prior laptop evaluation logged 11.5–12.4k prompt tokens for search tasks, exceeding 8192 cap. Apply bounded summarisation/structured observations while preserving authoritative original results, source identity, constraint checks and audit trail. Maintain deterministic non-model fallback and no human-approval bypass.

Run all required acceptance checks on Spark; preserve precise model/SHA/hardware/tool/evidence/timing receipts. Publish safe integrated code through reviewed path and provide Arnav a no-contention testing window and Alex a filmable demo path. Target working filmable demo by 15:00, freeze by 16:00, hardware down 18:00. No secrets or public model ports; no false claim that laptop runs prove Spark. At completion update #54, #23/#26/#33 with exact evidence, not just prose.
```

### B. Arnav — research, fixtures, script and form preparation only until Ben handoff

```text
You are supporting CANOPY event-day GitHub issues #55, #57 and #60. IMPORTANT USER RESTRICTION: do NOT run tests, benchmarks, models, code executions or performance measurements on Arnav's laptop or WSL. All future real evaluation happens exclusively on the DGX Spark after Ben has completed integration/testing and approved access. You may inspect code/docs via GitHub, prepare Markdown/question fixtures, write the form description/video narration, maintain a claim ledger and review official sources, WITHOUT running programs.

Read docs/EVENT_DAY_ISSUE_INDEX_2026-11-13.md and docs/EVENT_DAY_CONTENT_AND_CLAUDE_HANDOFFS_2026-11-13.md plus existing B11 runner and the current published agent contracts; if local source differs, report conflicts, do not delete Ben's changes. Freeze five inputs, including ambiguous and correct 'I don't know', with expected result rubric and metadata schema. Do not fake run IDs or measurements. Prepare research-backed impact, technical execution and feasibility story, with a safe, concise <=5-minute video narration for Alex.

At the approved Spark handoff ONLY: run exactly five genuine Nemotron model tests on Spark; record each actual model/tool/Result/citation and latency; report pass/fail to Ben and Alex. Any additional model comparisons are P1 and require Ben's quiet GPU window. Help submit required form after valid public GitHub and YouTube/Loom links are available. Update corresponding issues as work is genuinely completed.
```

### C. Alex — frontend, filmable trace, video and URL

```text
Own CANOPY event-day issues #56 and #58, plus previous UI issues #29/#32. Do not rewrite the application or duplicate Ben's agent integration. Inspect the currently integrated React UI/API types first and coordinate interface changes with Ben. Ship only demo-blocking UI improvements: traceable local agent selected tool, job/current result, evidence and limits; visible failure/timeout/stale state; readable planning controls and clear synthetic-source label. Preserve React/Three visual work already present.

Immediately draft storyboard, voiceover and graphics for <=5-minute video. Core judge criteria: impact, technical agentic AI/local DGX execution, and credible feasibility. Real Spark footage becomes available only after Ben's verified release; don't present laptop, scripted fixture or unvalidated Sheffield geographic assets as live measured Spark/real-site evidence. After Ben's handoff, record genuine workflow with Arnav-approved facts, edit captioned video, upload to YouTube or Loom, and independently test link playback before 17:00. Slides are optional production assets, not confirmed mandatory. Share exact URL for #60; record backup before Spark's reported 18:00 shutdown.
```

### D. Optional independent review prompt — no hardware access

```text
Perform a read-only release-claims review for CANOPY issues #57/#59/#60. Check draft public README, video description, submission form copy and source citations against the actual backend scope and all claims in the attached organiser guide. Produce a compact claims ledger classifying each statement as supported by official organiser rules, public Sheffield/Forestry evidence, authenticated DGX measurement, or unsupported. Flag invented data, incorrect currency conversion (pence vs pounds), unsupported cooling/carbon ROI, misleading device acceleration, exposed tokens/host information and non-public GitHub/video URLs. Do not execute tests, modify the deployment, change repository visibility or publish the form. Return precise required revisions and a pass/blocked list.
```

## 6. What is done vs outstanding after this preparation

**Prepared here:** public-source research synthesis, safe project description, timed video storyboard, five exact evaluation questions and scoring rubric, delegated issue-specific prompts and final form checklist. **Not done:** Ben's real Spark validation; five genuine model responses; live video; public repository; final submitted form. All future acceptance claims require observable evidence.
