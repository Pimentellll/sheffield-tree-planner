# Sheffield Tree Planner — development documentation

**Baseline:** 0.1 · 11 November 2026  
**Team:** Ben, Arnav and Alex  
**State:** integrated synthetic CPU backend and planning studio implemented; [BUILD](BUILD.md) contains current issue-level proof and remaining gates. The specification is not itself acceptance evidence.

## Start here

Build a site-based tree-planning application that can calculate a proposal, investigate a challenge and explain its evidence. The numerical tools own physics and feasibility; one local planning agent chooses useful investigations. This is a reusable product with a Sheffield demonstration, not a chatbot attached to a render.

These are the **living development documents**, replacing the research-era team plan as the place to edit implementation decisions. The comprehensive handoff remains background research, not a second specification. The canonical working copy is now this repository, [Pimentellll/sheffield-tree-planner](https://github.com/Pimentellll/sheffield-tree-planner), under `docs/`. Earlier Desktop/ZIP copies are historical snapshots, not parallel editable plans. Repository setup does not establish an implemented application, deployment or Spark run.

Read only what your task needs:

- [SPEC.md](SPEC.md): product boundary, requirements, architecture, agent behaviour and rationale. All three start here.
- [CONTRACTS.md](CONTRACTS.md): exact shared data meanings, operations, job states, errors and cache identity. Read before producer/consumer work.
- [NUMERICS.md](NUMERICS.md): shading equations, optimisation and modelling limits. Arnav's technical reference; Ben and Alex need the units/conventions.
- [BUILD.md](BUILD.md): ordered work items, proposed owners, dependencies, decisions and the next integration gate. **Only task-status home.**
- [Site desk audit](site-audit/STP-005-desk-audit.md): Alex’s sources, candidate coverage and pending asset/context controls; not an accepted site.
- [Recorded street-tree inventory](site-audit/source-inventory/README.md): source, rights and output schema for the #69 importer. No real sample has been acquired yet; a council record is not a verified current tree, species or planting permission.
- [Architecture design](ARCHITECTURE_DESIGN.md) and [audit](ARCHITECTURE_AUDIT.md): preserved design references, not new completion or owner-approval evidence.
- [UI reference](UI_DESIGN_REFERENCE.md) and [pre-implementation baseline](PRE_IMPLEMENTATION_READINESS.md): historical visual and analysis inputs; BUILD supersedes their old status and merge sequencing.
- [Product Vision v2](design/product-vision-v2/README.md): the newer visual direction as eight design artboards, with its [implementation brief](design/product-vision-v2/IMPLEMENTATION_HANDOFF.md) (an assignment brief, not a record of completed work). Design reference only; every figure and picture in it is an example, not a result.
- [VALIDATION.md](VALIDATION.md): test specifications, acceptance matrix, runtime evidence and demo/recovery runbook.
- [Reference runtime](REFERENCE_RUNTIME.md) and [physical runtime](PHYSICAL_RUNTIME.md): how to run the synthetic reference runtime and the opt-in local synthetic numerical runtime. Authored synthetic geometry only; no surveyed Sheffield geometry, human acceptance, model advantage or Spark execution is established.
- [DGX_SPARK.md](DGX_SPARK.md): event SSH/tunnels, pinned local-inference candidate, executable readiness diagnostic and full-application deployment gates. Prepared locally, not a claimed Spark run.
- [AGENTS.md](../AGENTS.md): project-specific boundaries for coding assistants, not personal agent configuration.
- [SOURCES.md](SOURCES.md): researched sources and the status of the advance-development report.
- [Agentic architecture and feature review](references/AGENTIC_FEATURE_REVIEW.md): comparable projects, source-backed design choices, captured team links and the expanded parallel-build target. Recommendations, not implementation proof; source maintenance remains in SOURCES.
- [Comprehensive research dossier](references/DEEP_RESEARCH_DOSSIER.md): the fourteen-part research synthesis, 170 annotated source records, concrete benchmark and B01–B12 recommendations. Cutoff 11 November 2026; research proposals, not accepted contract changes or application/Spark proof. Its source numbers are independent of SOURCES.md.
- [Research handoff](references/RESEARCH_HANDOFF.md): optional detailed background, alternatives and earlier independent reviews. Historical snapshot.

## Event-day science and claims

Prepared on 13 November 2026 for the NVIDIA Hack for Impact event. None of these documents is a test result or acceptance evidence; each states its own status.

- [Event-day execution board](EVENT_DAY_EXECUTION_2026-11-13.md): schedule, owners and organiser guidance for the day. Older schedule rows are historical or provisional where superseded, and issue status requires evidence.
- [Event-day issue index](EVENT_DAY_ISSUE_INDEX_2026-11-13.md): maps event-day tasks to GitHub issues and owners. An index, not a claim that every issue is implemented.
- [Content and Claude Code handoffs](EVENT_DAY_CONTENT_AND_CLAUDE_HANDOFFS_2026-11-13.md): preparation pack (research synthesis, video plan, delegation prompts) written without model tests. Its form copy (§2) and probe definitions (§4) are superseded by the brief and the protocol below.
- [Science package overview](event-day/science/README.md): what this folder holds and the findings that need team attention. Documentation prepared; nothing in the folder is a test result.
- [Five-case agent evaluation protocol](event-day/science/AGENT_EVALUATION_PROTOCOL.md), with the frozen prompts in [five_case_prompts.json](event-day/science/five_case_prompts.json): the NVIDIA-required model inputs and how to score them. Specified, not executed; runs only on the DGX Spark.
- [Scientific acceptance checklist](event-day/science/SCIENTIFIC_ACCEPTANCE.md): checks to work through on the Spark release. A row is `verified` only with an observed artefact on the release SHA.
- [Evidence and claims ledger](event-day/science/EVIDENCE_AND_CLAIMS_LEDGER.md): which statements the video, form, README and Q&A may make, may make only as plans, or must not make. It contains no CANOPY measured or computed result.
- [Judging and submission brief](event-day/science/JUDGING_AND_SUBMISSION_BRIEF.md): prepared form and video copy. Bracketed values are filled only from verified evidence.
- [Engineering fix plans](event-day/science/ENGINEERING_FIX_PLANS.md): FIX-1..4 for Ben from the science review. Plans only; nothing in it has been run.
- [Impact and feasibility research](event-day/science/IMPACT_AND_FEASIBILITY_RESEARCH.md): targeted research for judging, with each statement labelled source-supported, repository-observed or inference.

## Implementation proposals and audits

Proposals for review. BUILD and the GitHub issues remain the only status home; none of these documents assigns a writer or records completed work.

- [Nemotron agent runtime audit](implementation/NEMOTRON_AGENT_RUNTIME_AUDIT_20261113.md): agent runtime, agent-run API, worker recovery and release-boundary audit. Proposed design and test gates, not implemented or device-verified.
- [Agent evidence frontend handoff](implementation/AGENT_EVIDENCE_FRONTEND_HANDOFF_20261113.md): proposed agent-evidence UI, browser integration and acceptance for #74, consuming the agent-run API proposed for #73.
- [3D city and tree pipeline](implementation/3D_CITY_AND_TREE_PIPELINE.md): 3D city, tree inventory and scientific-scene specification. Implementation proposal for review, not a claim of real-site readiness.
- [3D product and agent UX](implementation/3D_AGENT_PRODUCT_UX.md): map-first product experience, agent investigation and evidence UI. Proposed implementation contract, not acceptance of real Sheffield geometry, model performance or environmental benefits.
- [3D implementation sequencing](implementation/3D_IMPLEMENTATION_TRACKER.md): proposed order and integration of the 3D and agent-UI PRs. Proposed work, not feature-completion evidence; despite the file name, not a tracker.

## Development before the event

Ben reports that the previous team developed for a week before its hackathon, and wants documentation followed by development before this event. **Plan for that, rather than waiting until the venue to write the product.** The report is useful precedent, not independently confirmed permission under this event's rules.

Keep two separate tracks:

1. **Engineering:** complete this specification, then begin portable local implementation and analytic tests against the working baseline. Synthetic test scenes and lawful inputs can unblock engineering while the real site is audited. Do not describe a synthetic scene as Sheffield.
2. **Entry eligibility:** confirm current rules, retain a dated prior-work record and disclose advance work as required. Unknown eligibility does not automatically ban local engineering; it does prevent claiming that advance-built code/assets are accepted entry material. If organisers impose a restriction, adapt the submitted work honestly.

Hardware access gates Spark proof, not CPU development. Dataset rights gate use/sharing of those assets, not every other module. External messages, repository creation/publication, spending and submission still need the relevant owner's approval.

## How to use this while building

1. Pick the next dependency-ready item in BUILD; name its human owner and actual writer.
2. Read SPEC plus the relevant contract, numerical and validation sections.
3. Implement the smallest complete behaviour, with its failure path and tests.
4. Record real commands/results and update that same work item. Unrun checks stay unrun.
5. Change a shared contract only with the affected producer and consumers; update docs and implementation together.

The first integrated gate is **baseline scene → one proposed tree → computed difference → UI**, including stale-result behaviour. It does not wait for a full optimiser or polished model explanation.

**Authority:** explicit team decisions override draft defaults; CONTRACTS owns wire meaning, NUMERICS owns mathematical meaning, BUILD owns task/decision state. After shared schemas exist, generated OpenAPI/types own serialization and these documents retain semantics. Record the transition; never maintain competing field definitions. Proposed roles and new defaults still require their owners' acknowledgement before parallel work.

- [Feature priorities](FEATURE_PRIORITIES.md): canonical F001–F035 catalogue, P0–P3 boundary, M0–M7 delivery order, ownership lanes, acceptance and risks. Read this before proposing scope; BUILD remains the only task-status home.
- [Three-agent execution PRD and issue specifications](AGENT_EXECUTION_PRD.md): STP-001–029 tasks, precise ownership, branch/PR workflow, dependencies, acceptance and agent-start instructions. Execution coordination only; does not replace BUILD, CONTRACTS or VALIDATION.

Priority reading: use FEATURE_PRIORITIES for delivery tiers and feature acceptance, SPEC for product requirements, CONTRACTS/NUMERICS for interface and mathematical meanings, BUILD for task state, and VALIDATION for evidence. The tiers do not replace requirements or relax hard constraints.
