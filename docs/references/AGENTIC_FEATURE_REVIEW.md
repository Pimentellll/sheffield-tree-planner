# Tree-planning agent: competitive and architecture review

**Prepared:** 11 November 2026.  
**Status:** team research and proposed product expansion; publication authorised by Ben, but shared contract changes and implementation ownership still require agreement.  
**Research baseline inspected:** `859c73b3fdab5bad734b98b8ad481225bb6ad462`, branch `feat/dgx-spark-readiness`.  
**Publication base:** `64d2fccbc27cf772a44b75364525be2b1e5f6a40` on `main`, preserving Alex's LiDAR, planning-reference and environmental-data additions. The readiness branch and main are distinct; neither establishes a running planning application.
**Authority:** [SPEC](../SPEC.md), [CONTRACTS](../CONTRACTS.md), [VALIDATION](../VALIDATION.md) and [BUILD](../BUILD.md) remain canonical. This document is supporting research, not a second implementation plan.

## 1. Verdict

The existing direction is worth keeping, but “an AI agent optimises tree placement and explains shade” is not a convincing differentiation claim. Numerical tree optimisation, individual-tree shade attribution, natural-language environmental analysis and agent/tool loops already exist.

**Recommended sharper product:** a tree-planning investigator that proposes a layout, actively tests what could invalidate it, and either produces an evidence-backed repair or identifies the unresolved decision or field observation that prevents a defensible recommendation.

A useful pitch is:

> We do not just show where trees could provide shade. Our planning agent investigates whether a proposal survives realistic constraints and uncertain assumptions—and shows exactly why it changes its recommendation.

This is a proposed workflow advantage, not an established scientific novelty or measured product advantage. The important claim is observable adaptation grounded in computation, not agent count or the presence of chat.

Keep the first integration gate small, but do not confuse it with the finished ambition. Ben subsequently confirmed substantial Claude Max/GPT Pro development capacity across the team. Section 10 expands the recommended target to a complete evidence-backed planning workbench: real site import, evaluated trade-off alternatives, adaptive stress testing and repair, decision-sensitive survey questions, and a traceable proposal export. These capabilities build on the same validated system; they are not separate demos.

## 2. Evidence scope and limits

Primary project documentation, papers and public source code were inspected. Six repositories were pinned to commits and thirteen README/source files were cached. Products were not installed or benchmarked; papers were not experimentally reproduced. Commercial feature descriptions are vendor statements, not independently verified performance.

“Not evidenced” below means not established in the particular material inspected, not proof that a vendor or research group has never implemented it. Some comparators are research prototypes rather than production competitors. No claim of exhaustive market coverage or global originality is justified.

The local checkout contains documentation, Spark deployment preparation and `sheffield_readiness` diagnostics—not the proposed simulation application or product agent. This was verified with `git ls-files` and the current SPEC. No new scientific, model-inference or Spark runtime result was produced by this review.

## 3. Closest projects: what to take and what remains open

### 3.1 TreePlanter / UMEP: the numerical baseline we must respect

**Verified:** The TreePlanter paper describes tree-location optimisation using SOLWEIG and a greedy versus metaheuristic search comparison. The UMEP processing implementation exposes tree dimensions/count, vegetation transmissivity, planting-area constraints, greedy search and hill-climbing/restart controls. Its stated optimisation target is mean radiant temperature, which is not interchangeable with our geometric shade metric. [S1–S3]

**Take:** explicit candidate masks, valid planting-space restrictions, baseline comparisons and a real numerical optimiser. Our agent should use such a solver, not pretend the LLM is the optimiser.

**Opportunity:** the inspected workflow does not establish a conversational investigation that chooses a follow-up analysis, repairs a challenged proposal while retaining user intent, and prioritises unresolved evidence. That is a different interaction layer; it does not make TreePlanter obsolete.

**Avoid:** claiming tree-placement optimisation as original, or reporting TreePlanter's thermal-comfort meaning for our less ambitious shade evaluator.

### 3.2 Freiburg tree-placement research: learned simulation acceleration

**Verified:** *Climate-sensitive Urban Planning through Optimization of Tree Placements* supplies a research implementation that trains estimators of mean radiant temperature, vegetation sky-view factors and aggregated temperature outcomes, and supports random, greedy, genetic and iterated-local-search/hill-climbing options. The inspected `optimize.py` uses PyTorch/CUDA and explicit tree/temperature-generation parameters. [S4–S5]

**Take:** separate the expensive evaluator from the search mechanism; retain an independently checkable reference. A validated surrogate could eventually make larger scenario searches practical.

**Opportunity:** the inspected material is numerical research, not a stakeholder-facing agent that manages constraints, uncertainty and proposal revisions.

**Avoid now:** training a thermal surrogate merely to add an NVIDIA/ML component. Data coverage, transfer to our site and error validation are additional research tasks. No speed or accuracy claim transfers automatically to our application.

### 3.3 Cornell Tree Folio: useful shade, not simply more canopy

**Verified:** Cornell describes extracting individual tree models from LiDAR and simulating their shading interactions with neighbouring buildings. Its overview connects shade quality to street orientation, building heights and local vulnerability, and contrasts neighbourhoods with similar tree counts but different shade provision. The dashboard uses Deck.gl and Mapbox. [S6–S7]

**Take:** marginal useful shade rather than total canopy coverage; per-place and per-time outcomes; a map that makes redundant shade visible. Optional leave-one-out evaluation could explain how much each proposed tree contributes to the whole layout without double-counting overlap.

**Opportunity:** the inspected project overview does not establish our proposed adaptive stress-test → controlled repair → unresolved-evidence workflow.

**Avoid:** calling shade equity a new idea, or inferring vulnerability from appearance. Any equity layer requires legitimate data, explicit policy choices and clear spatial resolution. One weighted total can conceal who receives little benefit.

### 3.4 ShadePlan / urban-cooling: very close agentic prior art

**Verified:** Its README describes satellite/Landsat heat analysis, planting-priority mapping, interactive Leaflet maps and Google ADK. The inspected agent module registers one `Agent` with analysis, report and shade-simulation tools. This is narrower than the README's broad multi-agent description. Conversely, the README labels shade modelling as future work, while the inspected source already contains `simulate_shade` and registers it. This is why the implementation was checked rather than relying on the feature list. [S8–S10]

The inspected shade code is a lightweight geographic-grid approximation: it traces shadow paths from building footprint centres and tree positions using height and sun direction, spreads tree marks according to canopy radius, and returns coverage percentages. It uses a degree-based grid and fixed approximate metre-to-degree factors; the default grid comment is roughly 50 metres. This is materially different from validated three-dimensional target-level ray occlusion. It establishes a code path, not physical accuracy or a running deployment.

**Take:** geographic output, typed domain tools and visible artefacts are more useful than a long chat answer.

**Opportunity:** the inspected shade path does not establish a budget-feasible layout optimiser, the incremental shade of a proposal relative to existing conditions on a defined target, or a complete stress-tested repair loop with invariant checks. These are concrete things our application can demonstrate, rather than claiming to be the first environmental agent.

**Avoid:** treating satellite land-surface temperature as pedestrian air temperature; calling total shadow area additional useful shade; assuming a multi-agent README means multiple runtime agents; or claiming the source was executed during this review.

### 3.5 NeMo-Ray: useful agent/tool mechanics, not a design to copy wholesale

**Verified:** The inspected agent uses a task-specific system prompt, parses model-selected actions, invokes a tool registry, appends observations and emits streaming tool/map/final events. Its network-infill policy explicitly calls coverage analysis → cuOpt candidate search → site validation; on failed validation it excludes that candidate and searches again. Other tools simulate outages, move masts, deploy a Cell-on-Wheels and check Starlink. This already demonstrates a propose → test → replan architecture in another domain, so that loop itself is not our novelty. [S11–S13]

The inspected `run_agent` returns a model final message directly. Its loop also has a fixed step exit that returns the last result; its emitted tool event says `success` after receiving a ToolResult without that boundary itself interpreting domain failure. Other layers may validate more: this is a specific boundary observation, not an audit of the entire project.

**Take:** a small domain registry, model → tool → observation iteration, explicit reject-and-retry logic, observation-linked map updates, and a distinction between a hypothetical simulation and an operator-authorised action.

**Improve our boundary:** completion must be decided by validated result/state, not the model's choice to say “done”; failed analyses and incomplete investigations must remain failures/incomplete. Preserve our existing immutable scenario references and deterministic validator. Copying an agent loop is not the novel product contribution.

### 3.6 UrbanTreeAgent and TreeShadeMapper: perception is a separate layer

**UrbanTreeAgent verified:** this repository is an engineering implementation inspired by an architecture document, not a reproduction of the original paper's models or benchmarks. It separates Central Monitor, Planner, ToolsGraph, Executor and Integrator. The default planner is keyword-driven/deterministic, builds dependency-ordered image-processing tasks and adjusts parameters after reported failures; the pipeline reviews plans, execution requests and final results and can replan. Its default tools include segmentation, tree counting and explicitly heuristic species-like classification. Thus review/replanning is already present, but it is not a live-LLM planting optimiser. [S14–S16]

**TreeShadeMapper verified:** the README documents panoramic-image semantic segmentation and binarisation to estimate canopy transmittance, sky-view factor and solar irradiance; it also describes sunlight-aware walking-route evaluation as a potential use case. Its input requirements and licensing differ from our proposed site-mesh planner. Its scientific validity was not reproduced here. [S17]

**Take:** separate observation/perception from physical evaluation and planning. Make uncertain crown structure or transmission an explicit model input rather than asking an LLM to invent it. A future site-observation workflow could inform which assumptions need revisiting.

**Avoid now:** appending street-view vision models to the demo before the basic site/evaluator works. Neither source establishes arbitrary photographic crown dimensions or planting feasibility for our site.

### 3.7 Autodesk Forma and Snaptrude: the quality bar for design workflow

**Forma verified in vendor documentation:** the published microclimate workflow combines sun, daylight and wind analyses with local weather to estimate perceived temperature using UTCI; a newer tool overview confirms the broader analysis/design interface. Do not infer the exact current availability or performance of every historical feature without product access. [S18–S19]

**Snaptrude vendor claims:** Analyze Site reads solar exposure, wind, available topography, access and visible constraints; Buildable Envelope translates supplied zoning parameters into a three-dimensional envelope and updates it when parameters change. The vendor stresses that human local knowledge remains important. That is a direct counterexample to a broad “AI site analysis is new” pitch. The underlying physics and agent implementation were not available for source inspection here. [S20]

**Take:** map-first interaction, linked alternatives, clear visual explanations and export that supports an actual design conversation. Show changed inputs and outcomes beside each other.

**Opportunity:** the inspected pages do not establish our exact tree-budget/constraint-repair and uncertainty-led investigation workflow. Do not say these platforms lack it categorically.

### 3.8 i-Tree Design: lifecycle value is already an established product concept

**Verified:** i-Tree Design takes location, species, size and condition, and can use building footprints to estimate relevant tree benefits. It describes current-year, forecast-year and cumulative benefits, including greenhouse gases, air quality, stormwater and building-energy effects. Its FAQ explicitly notes that a tree blocking winter sun can cause negative annual building-energy savings; summer benefit is not automatically net annual benefit. [S21–S22]

**Take:** establishment versus mature-tree views, explicit inputs and a useful proposal/report. A future phased investment product should consider when benefits arrive rather than displaying only an attractive mature canopy.

**Avoid:** attaching carbon, energy, money or stormwater figures to our output without their own supported models, geographic applicability and validation. These are not free extra dashboard cards.

## 4. What genuinely improves our existing architecture

The current SPEC already contains counterfactual relocation, scenario sensitivity, hypothetical revisions, deterministic validation, immature/mature cases and an agent-value comparison. Those are not new findings from this review.

The proposed improvement is to turn separate analysis tools into a **decision-directed investigation** with an explicit reason for its next action and a verifiable end condition.

### A. First: stress-test and repair the proposal

1. **Accepted brief:** targets, time windows, budget, pins and priorities have explicit meanings. The backend owns hard limits; model text is not approval.
2. **Initial plan:** deterministic search returns evaluated alternatives, with actual cost and known constraint results.
3. **Specific concern:** the agent identifies an evidenced issue or user challenge, such as a proposal depending on a strip whose availability is unresolved, or benefits being concentrated in a mature-crown assumption.
4. **Controlled test first:** use `prepare_scenario` and `compare_scenarios(..., mode=fixed_layout)` to test the existing plan under the named change. Do not redesign first and conceal why the original failed.
5. **Read the result:** distinguish hard failure, missed target, modest degradation, no meaningful change, unsupported modelling and missing information. A lower score is not automatically a failed plan.
6. **Repair when justified:** search under the relevant constraints, retaining all pins and non-negotiables. Keep alternative assumptions hypothetical unless the human accepts them. Initially, reuse `search_layouts` and expose the exact edit list; do not build a new optimiser API just for the name “repair.”
7. **Recheck the repair:** evaluate it under every agreed relevant case, including the original baseline. Avoid curing one scenario by silently breaking another. Prefer fewer changes among actually evaluated satisfactory alternatives; do not claim globally minimal edits without proof.
8. **Finish honestly:** report a candidate satisfactory for the tested cases, a real trade-off needing human choice, missing evidence, unsupported computation, or an unsuccessful search. Never silently relax budget, overwrite the accepted plan or present failure as successful planting advice.

Mandatory numerical and constraint checks always run regardless of agent preference. The model chooses optional investigations; it does not choose which safety checks to skip. If the finite set of meaningful supported investigations is exhausted or actions repeat without new evidence, return the unresolved state—not an invented answer. Tool deadlines/cancellation remain distinct from a completed search.

**What changes architecturally:** add an explicit investigation record referencing the existing immutable objects: question, reason, assumption/change set, tool request, resulting run IDs, disposition and unresolved next decision. This can be a small structured record, not a new database service, knowledge graph or multi-agent framework.

### B. Then: identify the observation that would change the decision

The ambitious follow-on is not “ask for more data.” It is:

> The preferred layout changes depending on whether this planting strip is available; the other tested uncertainty did not change the recommendation. Establish this site's permission/boundary condition before choosing between these alternatives.

That finding requires actual alternative evaluations and a stated range or discrete cases. It can prioritise a survey or clarification because it changes the choice. It is **not** a probability of correctness or formal expected value of information without calibrated distributions and costs.

This is stronger than a generic missing-data checklist, and stronger than a sensitivity plot that leaves the user to determine what to do next. It depends on correct site data, meaningful uncertainty ranges, useful alternatives and competent search. Include it in the expanded build target once the controlled-comparison slice works; do not pretend its dependencies disappear with more coding capacity.

### C. Keep lifecycle and multi-site investment as later product depth

Early versus mature benefit, maintenance and phased investment are real planning questions. The long-term product could compare which interventions to fund now and which information to collect before later phases. Do not introduce unvalidated growth/survival economics, shade sails, irrigation, multiple sites or a city-scale digital twin into the first hackathon vertical slice just to sound ambitious.

## 5. The proposed demo

Start from a credible site and accepted brief. The interface shows a real evaluated plan, per-target outcomes and the actual modelled assumptions.

A teammate or judge introduces a supported challenge: a planting strip may be unavailable, a time window changes, or a proposal should be evaluated with smaller crowns.

The agent chooses the appropriate operation, runs a fixed-layout comparison, explains the evidence, and either invokes search for a revised candidate or correctly leaves the plan unchanged. The UI shows original versus revised layout, changed inputs, constraint results, actual tool/run references and what still needs a human decision.

Do not guarantee that a particular challenge produces a dramatic reversal. An unchanged recommendation can be the correct result. Unsupported requests should be rejected honestly rather than answered with a scripted story.

The distinctive screen is **proposal → tested concern → evidence → revised recommendation or unresolved decision**, not a scrolling conversation.

## 6. How we prove the agent deserves to exist

The strongest alternative is a good dashboard with a deterministic optimiser, automatic mandatory checks, sensible scenario presets and a comparison panel. It can reproduce many of the same computations. We must not handicap that baseline.

Use the same data, tools, mandatory validations and outcome criteria for:

- manual structured controls;
- a competent fixed workflow with preset stress checks;
- the adaptive agent.

Prepare held-out requests before examining the comparative results. Include a routine task, a relocation rather than redesign, a newly accepted exclusion, an immature-crown concern, an ambiguity requiring clarification, an impossible target, and a failed tool call. Record correct completion, extra human actions/corrections, useful investigations, unsupported claims and full elapsed time. Failed runs count.

If the fixed flow is equally useful and more reliable, keep it as the primary interface and narrow the agent claim. If the agent helps users choose and execute the right analysis for unfamiliar questions with fewer corrections while preserving correctness, that supports its role. No evaluation has yet established either outcome.

## 7. Reuse, implementation and decision gate

Borrow architecture and interaction patterns first; do not import entire projects indiscriminately. GitHub metadata identifies Apache-2.0 for NeMo-Ray, MIT for the Freiburg repository, GPL-3.0 for UMEP and CC-BY-SA-4.0 for TreeShadeMapper. ShadePlan's README states MIT, but its inspected repository metadata did not identify a licence; UrbanTreeAgent's metadata likewise did not identify one. Treat the latter as unresolved, not permission to copy. This is preliminary licence discovery, not a file-by-file legal clearance; check actual files, assets and dependencies before copying/distributing code.

**Recommended team choice:** retain the tree-planning scope and single local agent, make stress-test → controlled repair-or-explain the centre of the demo, and build towards the expanded decision workbench in section 10. Decision-sensitive survey prioritisation is a target capability after its numerical dependencies, not a reason to block the first working path.

**Proposed responsibility split, not assigned work:** numerical owner validates comparisons/search and case semantics; interaction owner makes differences and evidence visible; integration owner implements the structured agent loop and tests. Existing team ownership must be acknowledged, not inferred from this document.

**Next action:** Ben, Alex and Arnav choose the first supported concern and what constitutes an acceptable outcome. Then revise the relevant R04/R05/R07 interpretation, B07/B10/B11 work and V07/V09/V11 tests together. B01–B05 foundations still precede a credible full agent demo.

Ben has authorised publishing this Markdown research to the existing private repository. That does not approve a merge, deployment, changed source licence, runtime access, spending or unacknowledged teammate assignments. Alex is explicitly collecting the sources; preserve his canonical SOURCES work rather than creating a second source-maintenance lane.

## 8. Source ledger

Pinned links preserve what was inspected. Public documentation may change. Retrieval/inspection date: 11 November 2026.

- **S1 — TreePlanter paper:** https://gmd.copernicus.org/articles/15/1107/2022/
- **S2 — UMEP TreePlanter tutorial:** https://umep-docs.readthedocs.io/projects/tutorial/en/latest/Tutorials/IntroductionToTreePlanter.html
- **S3 — UMEP processing implementation:** https://github.com/UMEP-dev/UMEP-processing/blob/a7798db1698c29fa5ba667e082e7ad564c20e8e8/postprocessor/treeplanter_algorithm.py
- **S4 — Freiburg research README:** https://github.com/lmb-freiburg/tree-planting/blob/a997b89c250c86656a70deef0f54ca07fca4cedd/README.md
- **S5 — Freiburg optimisation implementation:** https://github.com/lmb-freiburg/tree-planting/blob/a997b89c250c86656a70deef0f54ca07fca4cedd/optimize.py
- **S6 — Cornell Tree Folio project:** https://labs.aap.cornell.edu/daslab/projects/treefolio
- **S7 — Tree Folio dashboard:** https://www.treefolio.org/
- **S8 — ShadePlan README:** https://github.com/gitrlawton/urban-cooling/blob/ccb08c0cef2dcc5cae88cda550e9924b0e773a66/README.md
- **S9 — ShadePlan agent registration:** https://github.com/gitrlawton/urban-cooling/blob/ccb08c0cef2dcc5cae88cda550e9924b0e773a66/backend/agents/urban_cooling_analyst.py
- **S10 — ShadePlan shade computation:** https://github.com/gitrlawton/urban-cooling/blob/ccb08c0cef2dcc5cae88cda550e9924b0e773a66/backend/tools/shade_simulation.py
- **S11 — NeMo-Ray README:** https://github.com/Harrishayy/NeMo-Ray/blob/6b3dfdc06ffe9b846eca864fb87257151ed0f337/README.md
- **S12 — NeMo-Ray agent loop:** https://github.com/Harrishayy/NeMo-Ray/blob/6b3dfdc06ffe9b846eca864fb87257151ed0f337/agent/nemoray_modelling/agent.py
- **S13 — NeMo-Ray tools:** https://github.com/Harrishayy/NeMo-Ray/blob/6b3dfdc06ffe9b846eca864fb87257151ed0f337/agent/nemoray_modelling/tools.py
- **S14 — UrbanTreeAgent README:** https://github.com/MerryBai/UrbanTreeAgent/blob/97575309be274b563063e809623cbee7d42e2d86/README.md
- **S15 — UrbanTreeAgent planner:** https://github.com/MerryBai/UrbanTreeAgent/blob/97575309be274b563063e809623cbee7d42e2d86/urban_tree_agent/components/planner.py
- **S16 — UrbanTreeAgent pipeline:** https://github.com/MerryBai/UrbanTreeAgent/blob/97575309be274b563063e809623cbee7d42e2d86/urban_tree_agent/services/pipeline.py
- **S17 — TreeShadeMapper README:** https://github.com/kunifujiwara/TreeShadeMapper/blob/5b612c55dc4df7141a6b832f2f20603cc693f951/README.md
- **S18 — Forma microclimate feature description:** https://blogs.autodesk.com/forma/2023/05/08/updated-microclimate-analysis-allows-intuitive-insights-perceived-temperature/
- **S19 — Forma tool overview:** https://blogs.autodesk.com/forma/2026/08/28/forma-site-design-tools-overview/
- **S20 — Snaptrude site-analysis agents, vendor article:** https://www.snaptrude.com/blog/ai-site-analysis-agents-architecture
- **S21 — i-Tree Design description:** https://design.itreetools.org/treecalculator/calc_map/map_index.cfm
- **S22 — i-Tree Design/Planting FAQ and model limitations:** https://www.itreetools.org/faqs_home/i-tree_design_planting

The pinned links above preserve the source identity for this review. Source snapshots and private capture material are not repository dependencies and are not included in this publication. The canonical source register remains [SOURCES.md](../SOURCES.md).


## 9. Team discussion and shared links

### Capture scope and privacy

This section records a **partial project-focused capture** of public links shared on 11 November 2026. Ben directed use of the captured links and asked that the remaining messages be skipped. It is not an archive or complete account of the conversation.

Ten distinct literal URLs represent nine project resources because TreePlanter appeared both with and without a tracking query. Source entries preserve the captured path/viewport/query where present; repeated earlier references are team corroboration, not newly discovered works. Only relevant public links and project context are included. Private transcripts, phone numbers, screenshots, unrelated links and personal logistics are excluded.

### Captured project resources and implications

1. **TreePlanter — numerical prior art.** Shared: https://gmd.copernicus.org/articles/15/1107/2022/?utm_source=chatgpt.com and the clean version in S1. Already covered in section 3.1. Use it to define a credible numerical baseline; do not claim tree-location optimisation as new.

2. **Climate-sensitive Urban Planning through Optimization of Tree Placements — research paper.** Shared: https://arxiv.org/pdf/2310.05691 . The corresponding Freiburg implementation is covered in section 3.2. Use its methods as research/reference options; a neural surrogate needs its own training-domain and error validation before adoption.

3. **Autodesk Forma — product workflow reference.** Shared: https://blogs.autodesk.com/forma/2026/08/28/forma-site-design-tools-overview/ . Covered in section 3.7. Borrow linked design alternatives and clear analysis surfaces, not unsupported thermal claims.

4. **Environment Agency / Defra Survey — candidate geometry source.** Shared: https://environment.data.gov.uk/survey . Alex has already added a substantive desk audit to [SOURCES](../SOURCES.md#candidate-site-geometry-source-environment-agency-lidar-11-november-2026-desk-audit) and B03 on main. Treat those as the source-of-truth assessment. A site-sized DTM/DSM pilot is a promising route, but source age, CRS/datum, alignment, semantic classification, rights and viewer/solver parity still need proof. Do not duplicate canopy into both a static DSM obstruction and a proposed/existing tree model.

5. **TreePlotter Projects — project delivery and equity workflow.** Shared: https://planitgeo.com/library/treeplotter-projects/?utm_source=chatgpt.com . The vendor describes integrated tree inventory, canopy analysis, local canopy goals, priority areas, equity information and progress tracking. **Take:** structured proposal objectives and a coherent project record rather than an isolated map. **Boundary:** project management and equity-focused investment are already established product features. Our narrower opportunity is a transparent, numerically evaluated investigation and repair workflow; lack of such a workflow was not proven across the vendor's full product.

6. **Tree Equity Score UK — strategic prioritisation.** Shared: https://uk.treeequityscore.org/?utm_source=chatgpt.com . The official site describes a score combining canopy, income, health, employment, age, heat and air pollution to identify places needing investment. **Take:** optionally use legitimate area-level context to explain why a site deserves attention, then use our detailed evaluator for what to plant there. **Boundary:** an area score is not per-tree benefit, person-level vulnerability, soil/utility data or planting permission. Do not silently multiply it into the physical shade metric; Alex should check reuse terms and spatial resolution before any integration.

7. **ShadeMap — spatial/time interaction reference.** Shared: https://shademap.app/@47.608,-122.339,6z,1794418525924t,0b,0p,0m . Its [landing page](https://shademap.app/) advertises building/tree/terrain shadows, sun-path/exposure studies and accumulated shade maps. **Take:** responsive time navigation and accumulated shade views. **Boundary:** the supplied URL is a saved map state, not a verified Sheffield site asset or source of planting constraints. The advertised features were inspected; this review did not validate its numerical accuracy or the particular saved viewport.

8. **Infrared City — a stronger physical-modelling comparison.** Shared: https://infrared.city/learn/advanced-thermal-comfort?utm_source=chatgpt.com . The vendor describes direct/diffuse radiation, sky view, reflected sunlight, material heat storage, transmissive crowns, irrigation/evaporation and local wind, producing UTCI and seasonal comfort statistics. It also reports validation and multiple delivery interfaces; those are vendor statements, not measurements reproduced here. **Take:** an explicit model-capability panel and distinction between shade, radiant load, air temperature and thermal comfort. **Strategic implication:** do not try to beat a full thermal engine by relabelling ray shadows as cooling. Our first scientific contract remains shade-based. A richer thermal adapter/reference comparison is a separately validated extension, not a dashboard label or an automatic new paid dependency.

9. **OS Open Zoomstack — basemap/context candidate.** Shared: https://www.ordnancesurvey.co.uk/products/os-open-zoomstack . The publisher describes a Great Britain vector basemap in GeoPackage/vector-tile formats, with national-to-street context and customisable styling. **Take:** potentially use it for orientation and contextual display if its terms and formats suit the chosen stack. **Boundary:** a basemap is not a detailed three-dimensional crown/roof survey and does not establish plantability. Keep it distinct from terrain/elevation inputs.

The five newly examined product/data landing pages above were read directly for this update. Their advertised functions are not application compatibility, source-reuse permission, independent performance validation or a reason to expand the runtime tool permissions.

### Source ownership

**Alex owns ongoing source collection, as confirmed by Ben.** This document records the reviewed implications of captured references. [SOURCES.md](../SOURCES.md) remains the maintained source register; B03 remains the site/rights gate. Source collection is not automatically acceptance of a dataset or modelling choice. Avoid two people editing SOURCES or the same asset manifest concurrently. Existing source entries and Alex's LiDAR commits are preserved unchanged by this publication. Alex has also added a [planning/mapping reference shortlist](../SOURCES.md#user-supplied-reference-shortlist-11-november-2026) and [traffic, flood, drainage and water candidates](../SOURCES.md#sheffield-traffic-flood-and-water-dataset-discovery-11-november-2026). Those entries are a useful extension of the site-context evidence, not independent verification by this review. Start with an attributed, rights-cleared contextual overlay if useful to the selected site. Activating it as a hard planting constraint or calculating CO2, flooding or irrigation benefits requires a separately accepted meaning and validated model; dataset availability alone does not justify a new benefit claim.

## 10. Expanded target with the team's development capacity

### What changes

Ben reports that each teammate has substantial Claude Max/GPT Pro development capacity and invited a more ambitious plan. Use that capacity for parallel implementation, stronger tests, rapid integration and independent review—not to enlarge the runtime agent population or create unrelated infrastructure. These subscriptions support development; they do not prove entitlement to cloud API use, deployment of those proprietary models on Spark, shared accounts, or unlimited throughput.

**Recommended end-state for this build:** a local, evidence-backed tree-planning workbench in which a user can select a rights-cleared site, express goals, compare evaluated alternatives, challenge assumptions, receive a checked repair or a decision-sensitive survey question, and export a traceable proposal. Aim for the complete behaviour below, in dependency order. G1 remains the first integration proof, not the ambition ceiling.

### Product capabilities to pursue

- **A usable real-site workspace:** import the audited site bundle, display terrain/buildings/existing trees, and let the user edit targets, exclusions, budget and pinned placements. Viewer and solver must agree about position, units and north; unsupported real-world conditions stay visible.
- **Evaluated alternatives rather than one opaque answer:** expose cost, useful shade by target/time, winter effects and early/mature cases for actual evaluated layouts. Show trade-offs; call a frontier “best evaluated alternatives,” not a globally proven Pareto frontier without the required search proof.
- **Adaptive stress testing and repair:** the agent uses supported observations to select an investigation, compares the original layout before redesigning, proposes changes while retaining protected constraints, and checks the repaired candidate across the agreed cases. Display reasons, changed inputs and result IDs beside the map.
- **Decision-sensitive information requests:** evaluate meaningful alternative assumptions and identify which unresolved site fact changes the recommendation. Return a concrete survey/clarification question and affected alternatives. Do not invent probabilities, utilities data, biological growth curves or a formal value-of-information calculation.
- **A decision-ready proposal:** save a local summary of chosen/rejected alternatives, the reasons for changes, actual costs/units, modelled horizons, test cases, provenance and unresolved professional checks. Export only rights-permitted fields/assets. An export is not planting approval, publication or a purchase.
- **A reproducible local runtime and recovery path:** exercise the same application manually and with the local open model; preserve progress, cancellation, current-revision identity and live/cached/recorded distinctions. On Spark, measure actual coexistence, correctness and latency before claiming acceleration or readiness.

### Parallel lanes using the existing build plan

These are responsibility proposals except Alex's confirmed source collection. The existing BUILD items remain the only work-status records; do not create a second task board here.

- **Contract/integration lane — proposed Ben, B01/B04/B06:** own shared schemas, immutable jobs/results, dispatcher and cache identity. Publish stable types and real evaluator-generated fixtures for downstream consumers; one writer owns shared contracts, lockfiles and generated interfaces.
- **Numerical lane — proposed Arnav, B02/B04/B06/B07:** build analytic tests, trusted reference evaluation, candidate constraints/search and controlled comparisons. Separate calculation from optimisation so test/search/UI work can proceed against a stable interface.
- **Site/source lane — Alex source collection, B03 with Arnav's physical checks:** curate public sources and rights, pilot the chosen DTM/DSM crop, inspect semantic and temporal limitations and produce the reviewed SiteBundle. Synthetic work continues in parallel without being presented as a real site.
- **Interaction lane — proposed Alex, B05/B08:** build target/keepout/pin editing, maps and comparison/evidence panels against the acknowledged contract. Include stale, zero-gain, failure, incomplete and cached states—not only the successful screenshot. If Alex accepts the UI lane, he can delegate separable work; final ownership and review responsibility must first be recorded in BUILD. Only his source-collection role is currently confirmed.
- **Agent/runtime lane — proposed Ben, B09/B10:** implement the local-model adapter and investigation state, select real tools from their observations, enforce claims/permission boundaries, and prove the failure path. Laptop adapter tests do not certify Spark execution.
- **Independent validation/integration lane — shared, B11/B12:** use a reviewer other than the author for a changed interface or scoring rule. Exercise held-out challenges, human/fixed-flow/agent comparisons, clean installation and the final replay/recovery path. Review actual code and outputs, not another model's completion statement.

Use isolated worktrees or clones and bounded ownership for parallel writers. Assistants can own implementation and tests within a lane; teammates need not become typing bottlenecks. The human owner remains accountable for scientific assumptions, source rights, accepted priorities and external actions. Capacity is useful only if the lanes integrate into one product.

### Integration order and proof

1. **Foundation/G1:** acknowledged types → analytic reference → baseline/one-tree evaluation → real UI result, including an edit that makes an old result stale. Source audit and early model-adapter work can proceed alongside this.
2. **Decision tools/G2:** multi-tree overlap and feasibility → competent search → real-site transform proof → controlled relocation, fixed-layout scenarios, winter/early/mature cases and correctly labelled trade-off comparisons.
3. **Investigation/G3:** actual local model → relevant optional test → observed outcome → repair-or-explain. Add the decision-sensitive information branch once the scenario results support it. A fixed script is not a substitute for model-selected tool behaviour.
4. **Complete workbench/G4:** proposal/export, reproducible local environment, held-out same-tools comparison, recovery and source/model/device disclosure. Record the actual result and failures; do not assume the agent wins.

Extra GPU capacity should first accelerate independently verified batches or reuse safe immutable computations. A trained thermal surrogate, city-wide automatic ingestion, maintenance system, multi-agent debate or full microclimate solver remains a separate extension unless evidence shows it is needed for the stated workflow. Do not trade the complete coherent workbench for many disconnected features.

### Decisions needed before implementation changes

Agree the first real site/fallback, the source/rights evidence, the supported concern cases and what outcome is acceptable. Confirm the owners and shared contract revision. Reconcile new meanings with CONTRACTS, NUMERICS and VALIDATION before changing their consumers. This expanded recommendation does not silently relax eligibility, access, spending, scientific or deployment gates, and does not claim that all target capabilities are already built.
