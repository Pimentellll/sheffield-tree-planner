# CANOPY Sheffield — Integrated analysis and system architecture

**Design baseline:** 11 November 2026 · **Stage:** analysis/design, not implemented software · **Initial geography:** one Sheffield study site with a city-context entry point · **Source of authority:** [SPEC](SPEC.md), [CONTRACTS](CONTRACTS.md), [NUMERICS](NUMERICS.md), [FEATURE_PRIORITIES](FEATURE_PRIORITIES.md), [VALIDATION](VALIDATION.md) and [BUILD](BUILD.md).

**Purpose:** synthesise Arnav's product vision and inspected four-screen CANOPY design with Ben's [agentic review](references/AGENTIC_FEATURE_REVIEW.md), [research dossier](references/DEEP_RESEARCH_DOSSIER.md), the [UI export audit](UI_DESIGN_REFERENCE.md) and the merged [DGX Spark readiness guide](DGX_SPARK.md). It makes system-level design choices and exposes their trade-offs. It **does not** redefine existing wire fields, numerical formulas, job states, tool signatures, task status or an exact implementation directory tree. Alex owns implementation decomposition after affected-owner review.

**Decision status:** Arnav accepted the research-informed *product direction* (BUILD D13). This document is a proposed **integrated architecture baseline** for Ben/Arnav/Alex to acknowledge. Detailed contracts are still draft until their producer/consumers agree. No running application, accepted Sheffield site, field validation, complete UI, live Nemotron run or measured GPU acceleration is implied.

## 1. System problem, scope and success

### 1.1 Decision being supported

A site manager or council officer needs to decide: **for a specific site, target surfaces, time window, assumed tree profiles and finite planting budget, what model-feasible new-tree arrangement yields the greatest defensible additional direct shade, what alternatives are reasonable, and what missing information could change the choice?**

The application works *backwards from the objective and constraints* to site positions. It is a **preliminary decision-support and survey-prioritisation system**, not a construction, land-ownership or arboricultural approval system.

The broader business case includes urban heat exposure, canopy inequity, rainwater interception, drainage, air quality, carbon, ecological quality, capital and maintenance expenditure. These are **separate environmental-service hypotheses**, not quantities derivable from the first shade model. No unified ecological benefit or monetary ROI number is accepted without model-specific evidence.

### 1.2 Acceptance hierarchy

1. **Correctness:** coordinates, time, solar geometry, relative direct shade, cost units and known constraints are valid or reject explicitly.
2. **Decision integrity:** every recommended layout is evaluated and checked against the same accepted brief; unknown site suitability stays provisional.
3. **Inspectability:** a user can see the baseline, proposed layout, actual output, evidence tier, site revision and limitations.
4. **Adaptation:** a changed accepted input recomputes; an agent-selected concern can cause a meaningful controlled comparison and repair/no-change explanation.
5. **Local evidence:** the required local model actually executes registered tools; NVIDIA acceleration is claimed only with device records and equivalent-workload tests.
6. **Deployability:** portable CPU/manual path, one site contract, lawful data, reproducible setup and clear survey handoff.

**Counterfactual judge-facing target:** after a feasible proposal, challenge a planting strip, another location, winter sunlight or crown assumption; test original first when appropriate, run a genuinely new analysis, preserve all mandatory constraints, and show the measured comparison and justified disposition. One bounded case is a preferred **P1** differentiator; F013/B10 are **not** silently made P0.

### 1.3 Explicit non-goals for the first submission

- Reconstruct all Sheffield as a high-resolution ray-traceable model.
- Predict ambient °C cooling, pedestrian UTCI, AQI change, storm/flood damage avoided, household energy bills, carbon offsets or biodiversity units from a shade calculation.
- Treat historical tree points, parks polygons, heat maps or flood zones as planting permission.
- Prove global optimisation from a greedy heuristic; generate a speculative citywide return-on-investment figure.
- Run an unrestricted multi-agent framework, hosted-model fallback or runtime tools with shell/network privileges.
- Present static design mock numbers, SVG geography or prewritten agent traces as computed evidence.
- Implement every illustrated UI interaction before there is one real end-to-end slice.

## 2. Two spatial scales and the information hierarchy

**City context (screen 01):** a broad map of Sheffield for orientation and *conditional* prioritisation. It may show verified waterways, buildings, canopy inventories, heat-related context, flood-risk layers, air-quality monitoring, and tree-equity indicators **with their own sources, dates, accuracy and licences**. Where citywide values are unverified they remain visual illustrations/disabled. This city layer is **not a citywide numerical optimisation mesh**.

**Site planning (screens 02–04):** a bounded, georeferenced SiteBundle with surrounding occluder context, ground/target receivers, known planting and exclusion polygons, existing trees, profiles, candidate locations and explicit survey unknowns. Sun geometry and high-resolution candidate evaluation run **only over the active site and its necessary occlusion context**, not every Sheffield raster cell.

### Data-to-decision sequence

1. **Find** a legitimate study location and define who uses the shade (a specified path, seating area, courtyard or other receiver surface).
2. **Inspect** source coverage, age, licence, horizontal/vertical reference, building height and existing-vegetation ambiguity.
3. **Author** a versioned, locally registered site scene and semantic features; unresolved north/scale or essential geometry blocks real-site analysis.
4. **Declare** tree profiles, prices, candidates, known exclusion/spacing rules and provisional conditions.
5. **Create** an accepted scenario with target, time bins, objectives, budget, horizon and applicable winter rule.
6. **Evaluate** the unchanged baseline and proposed layout with identical receiver/time sampling.
7. **Search** feasible alternatives using the same evaluator and independent final constraint checks.
8. **Investigate** a challenge or sensitivity through exact registered tools; maintain accepted vs hypothetical authority.
9. **Present** compatible evidence, alternatives, unknowns and a human-reviewed proposal; export only permitted data.

### Site acceptance and fallback

Ben's dossier identified **Weston Park edge/path** as a geometry-audit candidate; **Manor Fields Park edge/path** as an operational alternative; **Peace Gardens/central block** as conditional. The exported UI illustrates **Kelham Island & Neepsend**, **not** an accepted site. There is **no currently accepted site**. B03 and its affected owners must choose a real primary and fallback after geometry, context, rights and target-definition checks. Alex must preserve the four-screen design while changing illustrative site names, numbers or art when necessary. A labelled synthetic site remains acceptable for numerical development but never earns a real Sheffield claim.

## 3. Logical architecture and ownership of truth

\`\`\`text
               Browser: CANOPY four-screen decision workbench
           map + target editor + budget + result/evidence panels
                          |
                   typed, versioned HTTP
                          v
            Single application API / domain boundary
    ┌──────────────────────────────────────────────────────┐
    │ Site registry + rights/readiness                     │
    │ Human-authorised scenario snapshots + revisions     │
    │ Async job scheduler + latest selection / stale guard│
    │ Validated domain tool dispatcher + evidence ledger  │
    └──────┬──────────────┬──────────────┬─────────────────┘
           |              |              |
           v              v              v
    Deterministic     Finite-candidate  One bounded
    numerical         placement search  Nemotron
    evaluator         + independent     investigator
    & reference       constraint check      |
           |              |                  v
           |              |              Local vLLM
           |              |              on DGX Spark
           └───────┬──────┘
                   v
          immutable results / provenance
                   |
                   v
            comparison + proposal
\`\`\`

**System-of-record separation:**
- **Backend:** site rights/readiness; persisted scenario acceptance; idempotency; job state; selection/currentness; tool permissions; result validation.
- **Geometry/evaluator:** ENU transforms, solar vector, occlusion and new-tree transmissions, metric meaning and numerical convergence.
- **Optimiser:** candidate traversal and search ranking under declared objectives; *independent validator* authorises a model-feasible candidate.
- **Model:** language-to-tool intent, which optional question to investigate next, interpretation of validated outputs; **never** physical values, scientific assumptions invented mid-run or accepted user approvals.
- **Browser:** interaction, visual state, alternative comparison, provenance and accessibility; cannot independently change metric meaning, scenario authority or job currentness.
- **Local file/SQLite store:** asset registry and versions, immutable snapshots/results, run/metric references, delivery records and audit metadata. A cache does not overwrite its source result.

**Architectural shape:** small modular monolith + separately served local inference endpoint, with domain boundaries enforced in one backend. No distributed event bus, microservice mesh, generic knowledge graph or arbitrary tool host in P0. React/Three.js and Python/FastAPI/Pydantic/SQLite remain candidates; lock exact versions based on smoke tests. Nothing in this design assumes the planned source modules already exist.

## 4. Canonical domain model and cross-component invariants

Use [CONTRACTS](CONTRACTS.md) **unchanged as semantic authority**. This section explains *why* its objects matter and what must not be lost in implementation.

| Domain concept | Principal purpose | Invariant |
| --- | --- | --- |
| **SiteBundle** | Versioned scene, geometry, rights, semantic layers, catalogue | Real/synthetic flag; explicit CRS, vertical datum, true-north transform; source fingerprints; missing survey conditions are not passes |
| **TreeProfile / state** | Assumed crown, trunk, transmission, age/horizon, price | A named age/leaf state is not silently substituted with mature foliage; cost scope/price date explicit |
| **Candidate location/profile pair** | Search's finite action surface | Same location admits at most one profile; exclusions and validated candidate catalogue never silently change |
| **Target receivers** | Define whose direct sun exposure matters | Position, normal, area basis, nonduplicated membership, weighted/unweighted interpretations |
| **ScenarioInput → Scenario** | Accepted brief and reproducible analysis identity | Human accepts consequential changes; model-created hypothetical remains separate; snapshot immutable |
| **Layout** | Exact proposed placement set | Existing scene remains baseline; placement coordinates are ENU metres, not lat/lon or SVG pixels |
| **Job + selection** | Async execution and latest displayable response | Selection keyed by scenario/revision/scope/view slot plus sequence; old results may complete to history but not become current |
| **Result / Metric** | Scientific and feasibility evidence | Run/scenario/case/layout ID, unit, quantity kind, input hash, source and limitations |
| **Delivery** | Distinguish new computation from reuse | Requesting job linked to original run/source; live, cached, recorded and fixture never conflated |
| **Proposal** | Human review and survey brief | Only verified/allowlisted evidence; no permissions, purchases or planting approval implied |

**Frames:** original geographic location uses latitude/longitude + known height datum. Imported British National Grid metres require tested projection, grid convergence/true-north handling and vertical reference to produce true ENU. The solar vector uses azimuth clockwise from **true north**, not map pixel up by accident. A viewer-only 4×4 transform must be invertible and checked using control points. Its scale and north are not inferred from an illustration.

**Time:** UTC instants are authoritative; \`Europe/London\` is display/edit interpretation with DST disambiguation. Time-bin midpoints and represented duration, not just slider positions, define numerical totals. Comparing two results with different dates, horizons or receivers must show the changes explicitly; the UI cannot subtract them as if identical.

**Units:** GBP as integer pence; distances in m; surfaces in m²; geometric additional shade in m²·h. Partial transmission produces *blocking-equivalent* m²·h, and objective-weighted results produce a different weighted utility token. Direct incident energy requires compatible DNI, orientation and kWh conversion. Temperature, AQI, runoff and economic benefit have **no substitute unit derived from shade**.

**Incomplete semantics:** empty polygons mean none supplied, not surveyed absence; a provisional candidate is not legally plantable; \`null\`/absent metrics are not zero. The implementation must preserve the distinct outcomes described in CONTRACTS, including valid zero planting, target miss, unknown readiness, error and proven finite-model infeasibility.

## 5. Source, site scene and geospatial processing design

### 5.1 Evidence-bearing source register

Every source used in the active SiteBundle needs: exact provider and URL, source type, declared survey/capture date **versus** catalogue update date, resolution, CRS and vertical datum, schema/semantics, licence and attribution, permitted local/team/display/export uses, checksum, acquisition record, preprocessing transform and any known missing coverage. Rights are per **asset/use**, not globally “open” simply because an endpoint returns GeoJSON.

**Most actionable candidates:** Environment Agency DTM/DSM and survey indices; OS OpenMap Local building outlines; inspected Sheffield council street-tree and community-forestry services; carefully licensed OSM paths/buildings; pvlib solar position; PVGIS irradiance for optional direct energy. Historic planting areas are not vacant land; “School Localities” are not school estates; SuDS regions are guidance, not a mapped underground drainage network. Council features may expose different restrictive terms. See SOURCES and the dossier's actual REST/schema checks.

### 5.2 Acquisition to simulation scene

\`\`\`text
Source inventory + rights
   → bounded site/context crop
   → CRS/datum normalization + control-point checks
   → terrain surface + buildings/existing trees with confidence/evidence tags
   → explicit target receiver surfaces + candidate/exclusion masks
   → local true-ENU origin + analysis/viewer transform verification
   → versioned SiteBundle and immutable candidate catalogue
   → site readiness decision + reproducible asset manifest
\`\`\`

**DTM** provides bare-ground height; **DSM** includes surfaces such as buildings and vegetation. The height difference is **not automatically a building mesh or classified crown profile**. Source acquisition in March 2021 or another leaf state changes existing canopy reliability; do not imply current crown accuracy without evidence. A footprint alone cannot supply measured height. Treat missing buildings or vegetation outside the cropped site but within possible shadow reach as a **horizon/context limitation**.

**Receivers and population:** do not optimise for arbitrary shaded raster area because it looks dramatic. Use explicitly declared ground/seat/route receivers and target weights, optionally partitioned into nonoverlapping zones. Weighting a footpath requires a declared planning priority or measured footfall; a “busy route” inferred from a picture is not observed footfall. Unweighted shade remains mandatory.

**Plantability:** enforce only known geometry and model rules. Unknown utilities, private title, roots/soil volume, heritage, access, buried services, approvals and long-term arboricultural suitability are **survey requirements**. Geometry-derived candidate points provide *modelled opportunity*, not a permit.

### 5.3 Site data quality gate

Accept a claimed real site for a specific purpose only when:
- a reviewed provenance/rights manifest exists and each public display/export decision is independently permitted;
- the local transform, scale, north, vertical alignment, control points and area are checked;
- enough surrounding context is modelled or missing obstructions are clearly marked;
- existing vegetation/building occluders are not double-counted;
- receiving surfaces and planting masks have declared meaning;
- candidate/profile assumptions are transparent;
- output is described as *model-feasible/provisional*, not professionally approved.

Failure rejects a real-site numerical claim without blocking synthetic analytic testing on the same solver.

## 6. Physical simulation: direct shade, not a surrogate for all climate outcomes

### 6.1 Baseline mathematical contract

For receiver/time sample u, define baseline direct transmission \`b_u∈[0,1]\`, candidate-tree transmission \`t_uj∈[0,1]\`, receiver area \`a_u\`, represented time \`Δt_u\`, nonnegative site priority \`w_u\`, and valid direct-illumination indicator \`f_u\`. Then

\`\`\`math
T_u(S) = b_u · ∏_{j∈S} t_uj
Δ_u(S) = b_u − T_u(S)
F(S) = Σ_u a_u · Δt_u · w_u · f_u · Δ_u(S)
\`\`\`

For **opaque** profiles and unit weight, F is additional direct-shaded **m²·h** on declared receivers; it accounts for existing shadows and union of candidate shadows. For partial transmission, label blocking-equivalent m²·h; weighted values are a policy utility, **not physical shaded area**. Morning versus afternoon, summer versus winter and maturity all require separate explicitly stated evaluation cases. The formula is the same as NUMERICS; any numerical revision must be reviewed there with affected owners.

### 6.2 Geometry and calculation responsibility

- Established solar-position algorithm (e.g. pvlib SPA) produces zenith/elevation and true-north azimuth from geographic coordinates and UTC; reject ambiguous local dates and invalid low-sun cases according to a declared policy.
- Trace from each receiver toward the sun, considering static terrain/buildings/existing vegetation and new proposed analytic trunk/crown. Start with axis-aligned opaque ellipsoids; do not conflate displayed foliage mesh with physical ray representation.
- Correct ray-offset/self-intersection, tangent/inside/near-horizon and non-front-facing surfaces; record sample size and time bins.
- Static occluders and existing trees belong in *one* baseline model. New-tree masks are evaluated against that same baseline; rays through an already opaque obstacle add no benefit.
- Independent analytic reference/CPU path is the oracle; optional parallel kernels only accelerate a **validated equivalent** model. A GPU that produces a fast different answer is not accepted.
- Optional fixed-crossing/young/leaf states must be explicitly activated with V02/V07 tests; path-length/LAI extinction coefficients require independent biological/optical evidence.

### 6.3 Numerical errors and model limitations

Keep separate:
1. **Numerical approximation:** spatial sampling, time-bin quadrature, floating precision, tolerance and ray/BVH errors.
2. **Input uncertainty:** DSM date, building height, crown dimensions, weather, cost and planting masks.
3. **Model inadequacy:** opaque crowns, omitted diffuse/longwave radiation, neglected wind/evapotranspiration, simplified leaf optics.

Finer spatial grids improve (1); they cannot fix (2) or (3). Report meaningful sensitivity to each category without inventing statistical confidence intervals or creating false precision.

### 6.4 Benefit and scientific claim ladder

| Status | Quantity | Required evidence before display as result |
| --- | --- | --- |
| **P0 after implementation** | Additional direct geometric shade m²·h | Same-scene baseline, evaluated layout, receivers/time/crown assumptions, numerical tests |
| **P0 after implementation** | Upfront planting cost, budget, tree count | Source/assumed cost table, accepted profile revision, integer-pence totals, validated model constraints |
| **P1 conditional** | Winter sunlight loss; young/mature comparison | Separate seasonal/profile cases, validated geometry and hard checks |
| **P2 conditional** | Direct incident solar-energy change (kWh) | Matched DNI, sun/receiver projection, weather source and consistency tests |
| **Separate environmental module** | Thermal comfort / MRT / UTCI / air temperature | Radiation + meteorology + physiological/urban climate model, calibration/reference checks as relevant |
| **Separate environmental module** | Rain interception, infiltration, runoff, flood damages | Canopy/rain/soil/drainage/catchment model, event data, distinct financial appraisal if monetised |
| **Separate environmental module** | Pollutant removal vs human AQI/exposure | Concentrations, deposition/dispersion and exposure model; cannot convert removed kg directly to AQI |
| **Separate environmental module** | Carbon, biodiversity, energy, long-term £ benefits | Domain-specific inventory, time horizon, biological/building model, valuation/counterfactual, independent validation |

**Evidence words:** “MODELLED” means a real traceable method/run; “INDICATIVE” means a documented heuristic/proxy not a physical outcome; “NOT QUANTIFIED” means no numerical claim; “EST.” means costs based on stated assumptions; “DEMO/ILLUSTRATIVE” means authored example, never live results. Data quality/professional survey status appears independently.

## 7. Optimisation, alternative layouts and resource allocation

### 7.1 Decision variables

A finite catalogue of allowed location/profile pairs forms binary decision variables. Each has a modelled cost and compatible geometry/state. P0 objective is **maximise declared useful shade under an upfront budget**, with an optional supported **minimum cost to reach a shade target** mode using the existing contract. The solver is not an agent: it produces reproducible candidate layouts and method metadata under user-accepted constraints.

Hard constraints are not objective weights: budget, one profile/location, pinned trees, exclusions, required spacing/clearance, valid target/receiver sets, and declared winter loss if selected. A higher shade weight cannot purchase permission to violate a root-clearance limit. Unknown soil/utilities remain provisional checks, not synthetic pass booleans.

### 7.2 Solver strategy and validity

1. Construct a **competent reference** (e.g., seeded feasible heuristic, not knowingly poor random points).
2. Use marginal-gain greedy on the actual union/transmission objective with deterministic tie-breaks and cost awareness; then feasible add/remove/swap or local relocation improvement.
3. Independently rerun feasibility on every selected candidate; preserve pinned choices and all active hard cases.
4. For tiny instances, exact enumeration or appropriate solver checks objective/feasible result and distinguishes heuristic miss from proof of finite-model infeasibility.
5. Report **best evaluated layout**, spend, tree count, baseline improvement, comparison against reference, and target/limitations; no unconditional optimality guarantee.

**Research pitfall:** basic nonnegative direct-coverage has a monotone diminishing-returns structure with fixed independent transmissions. The classical cardinality greedy bound **does not automatically survive variable prices, pairwise conflicts, winter constraints, robust min-of-scenarios or arbitrary policy scores**. In particular, an exact winter OR-coverage variable needs sufficient lower-bound linkage when winter loss is penalised or bounded; otherwise the solver can falsely report zero winter loss. The independent validator must catch it. See Ben's dossier section 6.5.

### 7.3 Multiple objectives and the UI's “Balanced” label

The supplied Studio shows *Heat/Shade 45%, Equity 25%, Flood/Stormwater 15%, Air quality 15%*, with a £75,000 budget and a “Balanced” option. These are **design-demo values**, not a validated four-metric objective or evidence that 1,260 Sheffield sites have been screened.

**Design decision:** never present a weighted multidomain result until each constituent model/proxy has an approved quantity, data provenance and interpretation. In P0, show the supported shade-first objective, actual budget and hard constraints. Other tabs may be disabled or clearly labelled *context/indicative/not yet optimisable*. A user selecting “Balanced” may be offered an explicit supported interpretation (e.g., shade with user-entered target weights and a separate winter check) **only when that mapping is approved and disclosed**; do not silently treat invented flood/AQI scores as equivalent to shade.

Future F021 can add separately validated objectives, Pareto alternatives or an explicitly justified preference function. Maintain individual outcomes and uncertainty beside any composite; don't sum m²·h, kg, AQI, flood pounds and a heuristic equity rank without documented normalisation, stakeholder values and safeguards. Prefer real alternatives with visible trade-offs over one opaque “greenest” score.

### 7.4 Time and value

A mature-tree image is not year-zero benefit. Declare establishment and target horizons, separate leaf-on/off assumptions, maintain explicit budget basis (initially upfront), and do not call stock carbon/storage an annual flow. Costs may be capital, establishment or long-term estimates with versioned price scope, but **do not add an undiscounted 25-year estimate into an upfront budget**. Multi-period investment appraisal and monetary benefit models are separate future decisions.

## 8. Agentic planning: bounded adaptive evidence investigation

### 8.1 Distinctive role and falsifiable hypothesis

The agent's useful role is to decide *what supported calculation to request next* for a particular planning question, not to invent the answer or execute arbitrary commands. Ben's research found close prior art (TreePlanter, Freiburg optimiser, Infrared.city/other agent workflows). Our differentiator is the specific *auditable, local, constraint-respecting decision challenge and survey-awareness*, **not** “first AI tree optimiser”.

**Hypothesis to test:** on unfamiliar supported questions, a local adaptive agent reduces unnecessary operator work or selects more consequential comparisons than a competent manual UI and fixed workflow **without worsening numerical correctness, constraint fidelity, latency or unsupported claims**. If evidence contradicts it, keep the manual/fixed product primary and narrow agent messaging.

### 8.2 One investigator, registered tools and explicit policy

Only these existing operations are authorised as the model-facing domain surface when implemented:

- \`inspect_site\`
- \`prepare_scenario\`
- \`evaluate_layout\`
- \`search_layouts\`
- \`compare_locations\`
- \`compare_scenarios\` (fixed_layout/redesign)
- \`prepare_proposal\`

Do not assume a prototype \`sensitivity_sweep\` method exists: the UI's static example names it, but it is absent from CONTRACTS. Until a reviewed contract amendment, express supported sensitivity through labelled hypothetical scenarios and \`compare_scenarios\`. “Register tool” does not mean giving Nemotron raw shell, SQL, arbitrary network, filesystem, imports or SSH.

Backend validates schema, identity, permissions, scenario scope, results, budget and hard constraints. Tool observations are signed by result/run identity in the application record, not generated by the LLM.

### 8.3 State machine and transition integrity

\`\`\`text
Human brief / accepted scenario
       ↓
validate site + target + known constraints  ──missing→ specific clarification
       ↓
inspect existing current results / start job
       ↓
job queued → running → completed / failed / cancelled
       ↓                                  └→ truthful failure / bounded recovery
observe validated result + provenance
       ↓
choose informative next action (or stop)
       ├─ location challenge → controlled compare_locations
       ├─ assumption concern → fixed_layout compare_scenarios
       ├─ accepted new constraint → search_layouts on new human revision
       ├─ no material change → retain plan + explain tested stability
       ├─ meaningful degradation → optionally redesign and recheck
       └─ missing fact / unsupported model → survey question / abstain
       ↓
claim validation → evidence trace → final answer / proposal draft
\`\`\`

**First test, then redesign:** when investigating the effect of a crown/strip/time assumption, apply the change to the *same fixed layout* before permitting a revised search. Otherwise the agent might conflate the assumption's effect with a new optimisation result. If the layout is unchanged under tested alternatives, that is a legitimate outcome; do not script a dramatic reversal.

**Accepted vs hypothetical:** the model can prepare a hypothetical version within the accepted task's allowed investigation scope; only a human can approve changing the active budget, exclusions, target or objective. An impossible or contradictory request triggers clarification or a validated no-target response, never silent relaxation. A previously failed or superseded job is not an observation of the current scenario.

**Sufficient evidence and stopping:** stop when the requested question is answered by supported evidence; when no meaningful distinct operation remains; if all important results are stale or unavailable; after explicit cancellation/deadline; or when a material human decision is needed. Do not substitute the model's “done” statement for a validated backend terminal result. Preserve compact reason-for-action and actual tool IDs, not private raw chain-of-thought.

### 8.4 Decision-sensitive surveys and permissions

Where alternate plausible assumptions (e.g., one planting strip available vs prohibited, or smaller crown at target year) cause a **genuine ranking or feasibility reversal**, present the specific site fact whose survey could change the recommendation. Report tested discrete cases and costs; do not call it formal probability-based Value of Information or a risk percentage without probability/observation/utility inputs. Do not claim the system verified underground utilities, consent or ownership.

### 8.5 Tool/security and interpretation boundary

- Imported feature names, source metadata, model card text and user-provided descriptions are **untrusted content**; only verified prompt templates and the domain dispatcher define policy.
- Limit tool schemas to implemented operations; reject malformed IDs/arguments and unsupported temperature/flood requests explicitly.
- Protect private inputs and source rights; no opportunistic third-party uploads, cloud model services or implicit data redistribution.
- Store hashes, source metadata, validated tool actions, results, model/runtime revisions and claim citations, with secret redaction. Never invent “20 agent runs”/“6.1 seconds” because the mock Comparison page displays them.
- Keep manual/fixed modes fully capable; do not deliberately cripple them to make the agent look better.

## 9. CANOPY four-screen information architecture

The exported HTML design is a **visual prototype**, not an implemented application. Use [UI_DESIGN_REFERENCE](UI_DESIGN_REFERENCE.md) for inspected exact colours/fonts, screen elements, source hashes and examples. Do not vendor the exported support.js/illustration as a production GIS engine.

| Screen | Decision purpose | Authoritative data and gating |
| --- | --- | --- |
| **01 City Overview** | Select a location and understand context | Citywide context is optional/indicative unless sourced; selected site has actual SiteBundle/rights/readiness. Kelham is an illustrative design placeholder |
| **02 Optimisation Studio (flagship)** | Set accepted target/budget, edit planting constraints, run one real evaluation/search, inspect ranked positions | Typed scenario, job currentness/selection, actual shade/cost/results; mock “Generate” clearing stale is replaced with computation |
| **03 Scenario Comparison** | Compare A/B feasible options, the exact changed inputs, growth/winter cases, and an agent-selected challenge | Compatible immutable scenario/run IDs, explicit case/horizon and provenance; Plan A/B metrics are never authored static values |
| **04 Impact & Investment Report** | Show an actionable preliminary council/survey decision, itemised costs, numerical benefits, source/data limitations | Rights-filtered proposal from validated results; unsupported AQI, flood savings, carbon/energy remain “Not quantified” |

**Navigation principle:** site identity and accepted scenario carry through screens. Comparison or report cannot display sample values from a different site/revision. The City Overview is **not** a P0 prerequisite for site shade evaluation; Alex should preserve its visual shell but prioritise Studio→real job→result.

**View modes:** 2D/3D camera, side-by-side/swipe/difference, time scrubber, year 0/5/10/20/30 and generated report buttons should be operational **only when their underlying transformation, separate evaluation case or action has been implemented/tested**. Nonfunctional controls must be disabled, annotated or hidden—not silently pretend to work. UI animation/illustration can aid understanding but never populate analytical KPI values.

**State truth:** unsubmitted edit immediately dims the last result and labels it stale; backend latest selection determines whether a job can be displayed as current. Show queued/running/provisional/zero/target-miss/failed/cancelled/superseded/cached/recorded/fixture outcomes accurately. The **requesting delivery** plus immutable result determines currentness, not a single client-side Boolean.

**Accessibility:** keyboard/form alternatives to drag editing, legible type at actual viewport sizes, semantic labels/icons independent of colour, consistent metric units, contrast, clear error recovery. Original fixed 1600×1000 design is not itself a mobile-responsive implementation.

## 10. DGX Spark: system deployment and compute-allocation design

### 10.1 Deployment boundary

The submitted product should remain useful on a portable CPU/manual development environment and run the **local model** on an authorised DGX Spark for B09/V08 proof. The accepted [DGX_SPARK](DGX_SPARK.md) guide documents an intended final single-machine service (application backend, approved assets/jobs, deterministic workers, local vLLM model), with laptop browser over authenticated loopback SSH tunnels. During development an API on a laptop may call Spark inference through a tunnel; that is **remote-local inference**, not proof the whole application ran on Spark.

\`\`\`text
Team laptop browser/React/WebGL
       │ approved SSH tunnel → Spark loopback application API
       ▼
DGX Spark: Python application + allowed local static assets
       ├─ site registry / rights / scenario + SQLite job store
       ├─ CPU reference evaluator and finite search
       │     └─ optional *verified* CUDA batched calculation
       ├─ deterministic tool dispatcher + agent state
       └─ loopback OpenAI-compatible vLLM HTTP service
                     └─ pinned local Nemotron weights
\`\`\`

**No public inference URL, unauthorised Docker changes, external production cloud, model-side network or source assets sent to an unapproved API.** Rendering a 3D map in a browser uses the browser GPU, not Spark's CUDA; do not claim otherwise.

### 10.2 Hardware reality and memory

NVIDIA's [DGX Spark hardware specification](https://docs.nvidia.com/dgx/dgx-spark/hardware.html) describes a Grace–Blackwell GB10 device, 20-core Arm CPU, Blackwell GPU and **128 GB unified LPDDR5X memory** for the reference DGX Spark. Related product families can have different capacities: inspect the **assigned physical unit**, OS, driver, disk, RAM and access permissions before choosing the serving profile. The memory is shared by CPU, GPU, model weights, KV/SSM cache, worker buffers, the OS, browser-independent application and concurrent processes; it is **not 128 GB of dedicated free VRAM**.

The merged B09 guide pins one first candidate: \`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16\`, an exact model revision, an Arm-compatible vLLM image/digest and tool parser. Its inspected weight files total about **63.16 decimal GB (~58.82 GiB)** before runtime caches/buffers. The ~3B active parameter count does not reduce the resident 30B weight footprint. The proposed context, sequence count and GPU utilisation are **test settings**, not measured feasibility. The 30B BF16 recipe is **not a default for a 64 GB configuration**.

**Conditional fallback:** use an approved/preloaded local service if present and genuinely compatible; else try the pinned 30B recipe only on a sufficient authorised unit. On memory/latency/tool reliability failure, test a **specific validated smaller checkpoint/runtime/parser combination** (4B and 9B-v2 are different requirements, not drop-in replacements). Choose based on observed task completion, tool-call validity, turnaround and memory, not parameter count or marketing. No hosted-model substitution can count as local Nemotron.

### 10.3 Work placement, contention and latency

| Component | Initial compute owner | Upgrade path and caveat |
| --- | --- | --- |
| Source acquisition/CRS/rights, geometry preprocessing | CPU / offline approved pipeline | GPU not necessary until profiling shows an actual bottleneck |
| Solar position, analytic ray/trunk/crown reference | CPU | Keep as correctness oracle |
| Static building/terrain visibility | CPU mesh/BVH / appropriate precomputation | Do not install OptiX before measuring value and driver support |
| Candidate × receiver × time transmissions | CPU vectorisation + cache | Chunked CuPy or Warp on target ARM64/CUDA **after** parity tests; Warp GPU ray query does not by itself establish RT-core use |
| Feasible search / local improvement | CPU controller over cached masks | GPU may help independent numerical kernels; final constraints validated on CPU/domain authority |
| Nemotron inference | Blackwell GPU via pinned local serving stack | Exact model/parser/quantisation with real structured-tool/observation tests |
| Map/3D camera/UI | User's browser GPU | Independent of Spark numerical-acceleration claim |

Prioritise **reusable opaque candidate visibility bitmasks** before a sophisticated GPU rewrite: fixed geometry/receiver/time inputs can be precomputed and recombined quickly for different layouts. Invalidate masks on geometry, crown/time or receiver changes; budget-only changes may reuse masks but still require new budget/constraint/search results. See CONTRACTS' distinct full-run and mask cache keys.

**Scheduling design:** one inference service, controlled numerical-worker concurrency, deterministic jobs with cancellation/deadlines and bounded result sizes. Local inference and numerical GPU work may compete for unified RAM and compute. Prevent concurrent heavy search from starving model responsiveness where possible; benchmark sequential and colocated paths. Do not promise an exact UI latency before real workload measurements.

**Useful measurement decomposition:** source load; geometry/mesh setup; baseline mask creation; candidate mask generation; search runtime; backend job queue; model load/TTFT/tool selection; scheduler waiting; returned observation; end-to-end response; peak CPU/GPU unified memory. Record cold and warm paths; distinguish first-time JIT compilation and cache hits. A speedup requires identical sample grids/precision, work and outcomes on actual CPU/GPU, with transfer/compile accounted for as relevant. NVIDIA RT cores are hardware capability, not a demonstrated execution path.

### 10.4 Access, deployment and failure

- Follow the merged DGX Spark guide's authorised SSH, host-key validation, read-only preflight, ARM64/container checks, model licence and weights integrity verification. Do not infer local Docker rights or network permission.
- The browser calls the domain API only; backend connects to private model endpoint; model receives **summaries and tool schemas**, never full sensitive meshes, environment secrets or arbitrary filesystem access.
- The agent issues a tool call; the backend validates and starts a durable job; a non-model scheduler polls/waits and delivers the **actual terminal observation**. Do not leave model generation open waiting for a long ray-trace job.
- A crash during a job makes it failed/interrupted, not silently complete; an old job can finish into history without overwriting a newer revision.
- If inference fails, manual/fixed planning still works but the local-agent acceptance remains unmet. If CUDA fails, CPU reference remains with GPU claims withdrawn. A recorded/fixture run must remain visibly labelled and cannot be advertised as live.
- Preserve a known-good app/data/model/driver manifest and a lawful offline fallback. A clean demo on the assigned device and actual model-selected domain tools are still required.

## 11. Data protection, security, rights and audit

**Trust boundaries:** the browser/user can propose changes; backend validates. The model can suggest allowed operations; dispatcher enforces authority. Imported GIS attributes, vendor pages, notes and prompt-like source text are **data** and never higher-priority instructions. Output fields are versioned; SQL and files are not model tools.

**Persistence:** keep immutable accepted/hypothetical scenarios, site/profile/candidate fingerprints, run/metric IDs, latest selection, tool arguments, relevant short observation summaries, versions/timing, source licence and failure state. Default logs must redact secrets and avoid unrestricted raw user/site text. Generate a replay/evidence pack from allowlisted items; rights-unknown images/meshes cannot be exported because a plan looks attractive.

**Professional/operational limits:** no automatic planting permission, cost commitment, procurement, council publication, landowner contact or unverified utility clearance. A report is a local proposal and survey brief. Record the actual input source and review date. Protect against invalid path/symlink imports and external asset URLs as CONTRACTS specifies.

**Provenance integrity:** when visual data and physically analysed geometry differ, show the limitation and reject a false metric-map correspondence; do not fill uncertain geometry from a decorative mesh. A model statement citing a metric must resolve to the current allowed run/case/unit; a stale or missing metric fails claim validation. Do not present speculative cost savings because the research literature found average urban-tree benefits elsewhere.

## 12. Operational states and cross-cutting failure architecture

| Failure or mismatch | Safe system outcome |
| --- | --- |
| Unknown site scale/north/vertical datum | Block real numerical site claim; use verified synthetic scene if appropriate |
| Missing licence or redistribution grant | Restrict use/export of affected asset; keep unrelated permitted tools usable |
| Invalid target/overlap or unsupported tree state | Schema/readiness failure, not silent defaults |
| No sun, existing building shade, or zero extra benefit | Valid computed zero with clearly stated dates/receivers |
| No feasible new candidate under known rules | Distinguish empty feasible layout, no eligible candidate and target miss |
| Heuristic cannot meet target | Report search completed without target; do not claim mathematical impossibility |
| Uncertain utility/land title/soil | Provisional survey requirement, not “passed” |
| Accepted scenario change while old job runs | New selection/revision; old result historical, never current |
| Failed/cancelled/newer superseding job | No reactivation of older selected completed result |
| Tool/model parser failure | Structured error and manual fallback; local-agent proof incomplete |
| Unsupported future impact metric | “Not quantified / model unavailable” instead of zero or invented £ |
| GPU or container incompatibility | CPU numerical reference or approved model alternative, withdrawn acceleration claims |
| Demonstration loses live model | Show truthful limitation; cached/recorded paths labelled with original input/run |
| Ineligible prior code or unauthorised data use | Do not represent as valid competition submission until organiser/source terms resolved |

## 13. Validation and falsification strategy

**Evidence levels:**
- **Design/reference:** paper, product page, source code review, metadata or this specification; *not* a running project.
- **Arithmetic/analytical:** known sun, ray, overlap and budget examples under stated synthetic geometry.
- **Implemented deterministic:** versioned CPU result, tested constraints, comparison and stale-state concurrency.
- **Hardware execution:** actual Spark model/tool observation, device/runtime identifiers, CPU/GPU parity and latency.
- **Site-scoped model:** lawful Sheffield SiteBundle with verified transforms/context and sampled uncertainties.
- **External physical validation:** observations/reference-model agreement and professional review; required for stronger physical/outcome claims.

### Minimum release evidence

| Hypothesis/claim | Disconfirming test / proof | Mapping |
| --- | --- | --- |
| Shadow geometry is correct | Analytic directional/ellipsoid/box/tangent, night and already-shaded cases | B02/B04, V02/V04 |
| Optimiser respects feasibility | Exact tiny cases, overlap, cost, pinned/exclusion/winter checks, independent validator | B06/B07, V04/V06/V07 |
| Results remain current | Delayed prior job; new accepted revision/slot; cached delivery; restart/cancel | B01/B05, V05 |
| Site is really Sheffield | Rights+CRS/true north+vertical datum+context/scene render match | B03/B08, V03 |
| Nemotron genuinely acts | Fresh model-selected registered tool call, actual observation, supported result citation | B09/B10, V08/V09 |
| Agent adds value | Held-out same-tools manual vs fixed vs model comparisons; all failures retained | B11, V11 |
| CUDA improves this workload | Equal-workload CPU/GPU correctness, cold/warm and shared-memory contention | B02/B09, V02/V08 |
| Proposal can be trusted as preliminary | Repeated current-run evidence, correct limits, safe source licences/export | B12, V10/V12 |

The research dossier proposes a twelve-case agent suite and comparison against manual/fixed and different local model sizes. Use exactly the same evaluator, site, constraints and tools for that comparison; avoid grading fluent narration or comparing to a deliberately weak manual baseline. Test prompt injection without preventing normal legitimate work. All metrics and hardware claims are conditional on actual execution.

## 14. Long-term extensibility without premature coupling

Keep each future service isolated behind a **typed, evidence-gated environmental module** with its own independent input manifest, units, horizon, counterfactual, calculation method, uncertainty, validation and source rights. Such modules may supply comparative *separate metrics* and only participate in preference optimisation after explicit acceptance. The core site/proposal/run provenance contract should remain reusable.

Possible modules, in order of decision value and data availability rather than marketing appeal:

1. Better crown phenology/growth profiles, winter and horizon cases.
2. Weather-based direct irradiance change and matched SOLWEIG/UMEP radiant reference.
3. One locally scoped rain/interception/infiltration or building-overheating pilot with suitable measurements.
4. Urban forest carbon/pollution inventory estimates with appropriate modelling and source assumptions.
5. Verified equity/need prioritisation, multiple sites, long-term maintenance and Green Book public appraisal.
6. Production consent/asset-management integration only with actual authority, ongoing update arrangements and privacy/security review.

**Architecture scaling unit = SiteBundle + reusable evaluator + validated module**, not “a giant Sheffield mesh”. Multiple sites/cities need verified ingestion, comparable contracts and coordinate transformations, not automatically one seamless high-resolution scene.

## 15. Alternatives, trade-offs and decisions requiring sign-off

| Decision | Recommended direction | Alternative and why not preferred yet | Acceptance authority |
| --- | --- | --- | --- |
| Scientific core | Direct shade + upfront constraints, honest units | Full MRT/UTCI/hydrology requires data/model validation; cannot be inferred from mesh | Arnav science; Ben API; Alex metric presentation |
| Scene scale | One validated study site + contextual city overview | Whole-city metre-scale ray tracing adds data/licensing/compute risk | B03 site owners + team |
| Search | Feasible greedy/local improvement + exact tiny cases | Trained thermal surrogate or complex MIP is not necessary until performance/quality evidence | Arnav + Ben |
| Agent | One bounded local investigator, deterministic tool authority | Multi-agent persona theatre adds complexity without demonstrated benefit | Ben + Arnav + Alex |
| UI objective presets | Supported shade-first objective and clearly labelled indicative secondary context | Four weighted environmental benefits not yet measured or normalised | Team product/science decision |
| DGX deployment | Single local inference service + portable app + CPU reference; optional measured GPU acceleration | Cloud model or unverified CUDA/RT-core claim violates evidence/locally-run narrative | Ben + device owner |
| Geometry source | Rights-audited EA/OS/council data, true ENU, known survey gaps | Scraped 3D tiles or decorative SVG cannot establish legal/physical site | B03 owners |
| Evidence/survey | Traceable proposal, local controlled comparisons, provisional professional checks | Automatic planting approval or financial ROI is unsupported | Human decision owner |
| Research adoption | Accept product-direction improvements; preserve core contracts until reviewed | Silently replacing fields based on a large research appendix causes incompatible implementations | All affected producers/consumers |
| Feature gate | M2 first, then P0 end-to-end; one P1 agent challenge preferred | Promoting all P1 features to P0 raises integration risk | All three |

**Open team decisions (must be recorded in BUILD, not a second tracker):**
1. Which specific primary/fallback real site, receiver, target time/horizon and user decision will form the demo?
2. What is the accepted contract revision and confirmation of numerical units/north/vertical frame by Ben/Arnav/Alex?
3. Which single controlled concern should the judge be able to pose, and what result counts as a correct answer *even if there is no ranking reversal*?
4. What exact P0 UI objective/preset wording replaces unsupported Balanced/Flood/AQI optimisation?
5. Which Nemotron checkpoint/runtime/profile actually passes on the assigned Spark, and what is the fallback?
6. Which sources/art assets may be locally used, displayed and exported?
7. What are the confirmed event eligibility, AI-assistance, advance-code, demo and submission rules?
8. When do all three owners acknowledge implementation lanes and approve the changes affecting their consumers?

## 16. Analysis/design completeness boundary

This document specifies **system responsibilities, model authority, data meaning, scientific/agentic behaviour, runtime placement, interactions, failure modes, validation and extension rules**. It deliberately does **not** provide exact source file trees, dependencies pinned before smoke, endpoint implementation pseudocode, database migrations, JSX/component state machines, Git task packets, CI script changes or ownership of individual implementation files. Those are Alex's implementation-level handoff, derived from BUILD B01–B12 after team decisions.

Before parallel coding, each work packet must be scoped to an already agreed contract and a real testable milestone. The design-to-implementation acceptance gate is satisfied by **acknowledgement of the relevant meaning and owner**, not by reading this document alone.
