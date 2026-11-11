# Sheffield Tree Planner — development documentation

**Baseline:** 0.1 · 11 November 2026  
**Team:** Ben, Arnav and Alex  
**State:** implementation specification; application not implemented or verified by this documentation work.

## Start here

Build a site-based tree-planning application that can calculate a proposal, investigate a challenge and explain its evidence. The numerical tools own physics and feasibility; one local planning agent chooses useful investigations. This is a reusable product with a Sheffield demonstration, not a chatbot attached to a render.

These are the **living development documents**, replacing the research-era team plan as the place to edit implementation decisions. The comprehensive handoff remains background research, not a second specification. The canonical working copy is now this repository, [bbeennyy860-cyber/sheffield-tree-planner](https://github.com/bbeennyy860-cyber/sheffield-tree-planner), under `docs/`. Earlier Desktop/ZIP copies are historical snapshots, not parallel editable plans. Repository setup does not establish an implemented application, deployment or Spark run.

Read only what your task needs:

- [SPEC.md](SPEC.md): product boundary, requirements, architecture, agent behaviour and rationale. All three start here.
- [CONTRACTS.md](CONTRACTS.md): exact shared data meanings, operations, job states, errors and cache identity. Read before producer/consumer work.
- [NUMERICS.md](NUMERICS.md): shading equations, optimisation and modelling limits. Arnav's technical reference; Ben and Alex need the units/conventions.
- [BUILD.md](BUILD.md): ordered work items, proposed owners, dependencies, decisions and the next integration gate. **Only task-status home.**
- [VALIDATION.md](VALIDATION.md): test specifications, acceptance matrix, runtime evidence and demo/recovery runbook.
- [DGX_SPARK.md](DGX_SPARK.md): event SSH/tunnels, pinned local-inference candidate, executable readiness diagnostic and full-application deployment gates. Prepared locally, not a claimed Spark run.
- [AGENTS.md](../AGENTS.md): project-specific boundaries for coding assistants, not personal agent configuration.
- [SOURCES.md](SOURCES.md): researched sources and the status of the advance-development report.
- [Agentic architecture and feature review](references/AGENTIC_FEATURE_REVIEW.md): comparable projects, source-backed design choices, captured team links and the expanded parallel-build target. Recommendations, not implementation proof; source maintenance remains in SOURCES.
- [Comprehensive research dossier](references/DEEP_RESEARCH_DOSSIER.md): the fourteen-part research synthesis, 170 annotated source records, concrete benchmark and B01–B12 recommendations. Cutoff 11 November 2026; research proposals, not accepted contract changes or application/Spark proof. Its source numbers are independent of SOURCES.md.
- [UI design artifact handoff](UI_DESIGN_REFERENCE.md): Arnav's linked Claude design reference, access limitations and requirement-to-interface mapping; visual/content inspection and implementation verification remain Alex's follow-up.
- [Research handoff](references/RESEARCH_HANDOFF.md): optional detailed background, alternatives and earlier independent reviews. Historical snapshot.

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

Priority reading: use FEATURE_PRIORITIES for delivery tiers and feature acceptance, SPEC for product requirements, CONTRACTS/NUMERICS for interface and mathematical meanings, BUILD for task state, and VALIDATION for evidence. The tiers do not replace requirements or relax hard constraints.
