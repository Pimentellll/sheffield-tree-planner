# CANOPY Sheffield — 3D product experience, agent investigation and evidence UI implementation specification

**State:** proposed implementation contract, **not** acceptance of real Sheffield geometry, agent/model performance or environmental benefits. Date: 13 November 2026.  
**Review roles (not writer assignments):** Alex frontend/UI; Ben agent/API/revision plumbing; Arnav semantics/claims/visual-to-numerical parity. Live issue assignment governs; this document assigns no writer (§10).  
**Read with:** [BUILD](../BUILD.md), [UI_DESIGN_REFERENCE](../UI_DESIGN_REFERENCE.md), [SPEC](../SPEC.md), [CONTRACTS](../CONTRACTS.md), [FEATURE_PRIORITIES](../FEATURE_PRIORITIES.md), [NUMERICS](../NUMERICS.md), [VALIDATION](../VALIDATION.md), and the 3D city/tree pipeline proposal in [PR #66](https://github.com/Pimentellll/sheffield-tree-planner/pull/66) (lands as `docs/implementation/3D_CITY_AND_TREE_PIPELINE.md`; switch this to a relative link once #66 merges).

## 1. Objective and design audit

Primary task: **explore a geospatial 3D scene → select a source-linked tree/site → work on a bounded scenario → use deterministic tools (manually or with a bounded agent) → inspect trustworthy evidence → compare → prepare a review pack**.

Preserve CANOPY's forest/ivory visual identity, but make the spatial view the dominant canvas. For layout and visual direction, the newer reference is Product Vision v2 (`docs/design/product-vision-v2/`, draft [PR #78](https://github.com/Pimentellll/sheffield-tree-planner/pull/78)); where it differs on layout, it governs and this document supplies only the evidence, state and claim rules. The historical Claude artboards are visual proposals, not running GIS data or validated results. The current local Three.js Studio is an engineering representation, not a city-scale digital twin.

### Explicit UX flaws to correct

| Finding | Impact | Implementation requirement |
| --- | --- | --- |
| Permanent dense panels shrink the map | Hard to navigate and see proposed geometry | Spatial canvas receives primary space; collapsible context inspector/controls and persistent compact navigation |
| City overview artboards imply data-backed heat/flood/AQI/equity | Unsupported environmental claims | Only permitted source context; no calculated physical benefit without corresponding validated engine |
| Original 'Generate' only reset local stale state | Fake solver affordance | Submit real typed job to backend, show queued/running/terminal delivery and selected run identity |
| Original weights/constraints are illustrative | Invalid multi-objective and waived hard constraints | Only the two contract objectives, `maximise_shade_under_budget` and `minimise_cost_for_target` (CONTRACTS §4); disabled future selectors; hard rules enforced server-side; unaccepted edits remain draft |
| Agent card was static sample text | Unverifiable 'AI value' | Actual registered tool selection, bounded observations, references, provenance and human approval |
| Flat geospatial illustration used as reference | False map/metric parity | Geographic layers and scientific assets explicitly separated; real UI never depicts decorative mesh as accepted solver geometry |
| Selected tree has unclear evidence class | Users mistake detected canopy for verified trees | Persistent tree status and source identity from the proposed `evidence_class` (`recorded_location`, `detected_crown`, `field_verified`) and `match_status` fields defined once in PR #66 §3.2 (§3) |
| Old results look current after editing | User may adopt invalid plan | Explicit dirty → stale, late-results guard, immutable revision/run links and selectable run history |
| Time sliders imply changing results | Visual state confused with computed season/case | Mark camera/sun preview separate from evaluated case, require new run or show verified stored result |
| Widgets too numerous | Users cannot find main task | Progressive disclosure; primary metric hierarchy; detailed provenance in inspector/drawer |

## 2. Information architecture

Four top-level destinations with a persistent selected-site context:
1. **City Explorer** — Sheffield geographic orientation; browse a source-backed 3D scene, identify/inspect trees, select a site. This is an optional module, not a dependency for the synthetic P0 solver. Its first slice is the single-site Weston Park visual pilot (UX3D-02); citywide browsing/LOD maps to F024 (P2) and F025/F033 (P3) and needs explicit assignment plus a method/data/rights/validation plan before implementation (AGENTS.md).
2. **Planting Studio** — site-scale accepted scenario, 3D scene, candidate/tree selection, budget/constraints, actual evaluate/search jobs and result evidence.
3. **Compare** — equal-case/controlled difference of immutable layouts/scenarios, with side-by-side scene overlays, metric instance identities, constraints and traceable changed inputs.
4. **Review pack** — source/rights-aware proposal record with numeric evidence, limitations and requirements for further survey/approval.

Context tools (not extra pages unless design tests justify): layer manager; tree inspector; site readiness/provenance; candidate inspector; scenario controls; run history; agent investigation; constraint/assumption detail. Preserve selected feature and geography when switching City Explorer → Studio, but show a **visual-only** readiness notice if no accepted SiteBundle exists.

### Spatial canvas layout

**Desktop (primary):** restrained top bar with CANOPY/site/scope and state; compact navigation rail; ≥60% viewport width ideally reserved for active map in standard exploratory state; right inspector opens on selection; left scenario controls are collapsible; result strip summarises 2–4 key quantities; agent opens as a contextual investigation drawer without permanently covering the central scene. Avoid multiple full-height competing sidebars.

**Tablet:** retain map-first controls, bottom sheet for selection/evidence, collapsible parameter drawer.

**Mobile:** browse, identify trees, read evidence and follow a result; do not pretend full planting optimisation workspace is practical without explicit responsive design/validation.

**2D/3D camera:** visual camera mode, not alternative physics. North/scale compass, tilt, reset and feature recenter have actual handlers; accessible keyboard alternative and object list support selection without 3D raycasting. Camera state must not change evaluated outcomes.

## 3. Data-driven tree selection and semantic symbology

Appearance and backing data must match. Tree tokens are the proposal defined once in PR #66 §3.2 and are cited here, not redefined: `evidence_class` ∈ {`recorded_location`, `detected_crown`, `field_verified`} and an orthogonal `match_status` ∈ {`recorded_only`, `detected_only`, `matched`, `ambiguous`, `conflicting`, `not_assessed`}. "Inferred crown" is display text for `detected_crown` only. An unknown elevated object is a scene-semantic class (terrain/building/vegetation/unknown), never a `TreeFeature`. Colours are the [UI_DESIGN_REFERENCE](../UI_DESIGN_REFERENCE.md) tokens (§8).

| Object | Visual treatment | Inspector status |
| --- | --- | --- |
| Recorded existing tree (`evidence_class=recorded_location`) | Canopy green (`#527A55`) point + distinctive solid marker; no crown unless a matched crown exists | Source layer; source record ID (e.g. ArcGIS `objectid`, labelled a service record ID, not a field-verified tree ID); retrieval time; source file SHA-256; capture/survey date **Not recorded by source** unless the source supplies it, never back-filled from catalogue/publisher update dates; field verification unknown unless evidenced |
| Inferred crown (`evidence_class=detected_crown`) | Desaturated canopy-green textured crown with dashed perimeter | Inferred geometry; method, confidence/limits; approximate shape/height |
| Field-verified tree (`evidence_class=field_verified`) | Canopy green solid marker + check badge (shape, not colour, distinguishes it from a recorded point) | Verifier, date and method of the field record |
| Match status (every `match_status` value) | Inspector-only: no separate map symbol, so the map never implies a clean match | Text badge plus linked record/crown IDs; `ambiguous`/`conflicting` list the competing candidates; `not_assessed` says so explicitly |
| Unknown elevated object (scene-semantic class `unknown`, not a tree) | Neutral stipple/outline | Unknown vegetation/building classification; no tree identity, `evidence_class` or `match_status` |
| Proposed tree | Lime (`#B7E879`) crown/halo and numeric ID | Hypothetical/selected layout reference, state/horizon and cost |
| Candidate position | Small selectable outlined point (cluster at distance) | Candidate catalogue revision and status |
| Excluded/constraint position | Constraint coral (`#D67C64`) crosshatch/stop icon | Constraint/evidence reference; cannot be placed via chat |
| Survey required | Constraint coral (`#D67C64`) outline + question badge (shape distinct from the exclusion crosshatch) | Provisional; not approved for planting |
| Heritage review required (site level) | Constraint coral (`#D67C64`) banner/badge on the site boundary and in the inspector, with "Heritage review" text; no per-position marker (shape distinct from survey and exclusion markers) | Weston Park is a Grade II registered park and garden (Historic England 1001340; [site audit](../site-audit/STP-005-desk-audit.md)); any planting position needs heritage/land-manager review |
| Compare A-only/B-only/shared | Water blue (`#62AFC2`) / Heat amber (`#E8A476`) / split-outline, not colour alone | Same-site case comparison and per-layout identity |
| Selected feature | High-contrast outline + anchor + accessibility focus | Object ID, source, date, related result |

In this scene, amber is reserved for Plan B. No two semantic classes may share a colour without a distinct shape or pattern; this is an acceptance check.

Never draw a crown for a `recorded_location` point when only a point record exists, and never label a `detected_crown` as verified. At zoomed-out scales use clusters/coverage with visible legend, not 100,000 tiny selectable circles. Inferred shape/height/canopy should be marked approximate. Tooltips are supplemental; source and status remain available in a persistent inspector.

Tree inspector minimum: name/identifier, `evidence_class` and `match_status`, location (coordinate frame properly labelled), geometry/date, provenance and rights, available sourced attributes, uncertainty, relationship to baseline shade, actions supported by the current site. Unknown species/height/health/capture date must show **Not recorded** rather than filler. Imported attribute text (e.g. Street Trees `sitename`, `featurelocation`) is untrusted data: display it as quoted text, never as instructions or trusted agent context (§6).

## 4. Metric and evidence dictionary

The hierarchy is **decision → primary quantitative evidence → constraints/unknowns → explanation/provenance**. Values must be bound from backend results, source records or explicitly synthetic *design-example* fixtures.

| Metric/UI | Required semantics | Do not substitute |
| --- | --- | --- |
| Proposed tree count | Number of proposals in selected immutable layout | Existing city tree count or hardcoded artwork |
| Budget / cost | GBP, backend integer pence, upfront basis, profile price date/scope | Lifecycle cost, quote, monetised benefit |
| Budget remaining | Same accepted budget basis less computed upfront cost | Uncommitted draft budget with old result |
| Additional shade (geometric) | `additional_shade` metric instance, `m2_h`, `quantity_kind=geometric`, exact target/case/tree state, current result | °C cooling, general 'shade area', irradiance or weighted utility |
| Additional shade (blocking-equivalent) | Same metric with `quantity_kind=blocking_equivalent`: direct-beam blocking-equivalent `m2_h` (NUMERICS §4.3), shown with its transmission assumption | Binary fully shaded area |
| Winter sun loss | `winter_sun_loss`, `m2_h`, against the declared `maximum_loss_m2_h`; hard constraint, pass/fail in the Constraints record | An offset to summer benefit, or an optional extra |
| Weighted utility | `weighted_m2_h`, exact declared weights/targets | Physical unweighted shaded area |
| Candidate eligibility | Finite catalogue validation and explicit rule status | Planting permission or utility/soil survey |
| Constraints | Pass/fail/unknown plus observed/limit/affected scene revision | 'All clear' on unspecified checks |
| Growth/season cases | Individually computed stored case / supported declared state | Arbitrary year-based UI multiplier or sun animation |
| Source status | Capture date, accuracy, coverage, licence/display/export gates | 'Verified Sheffield science' from a source link |
| Agent evidence | Registered operation, accepted/hypothetical refs, validated args, job and run IDs, actual observation | Prewritten agent answer or invented '20 trials' |
| Cache/execution | Live/cached/recorded/fixture as returned with result delivery | Treat cached or recorded response as fresh computation |

**P0:** physical shade, upfront costs, every declared hard constraint including winter-sun loss limits (shown in the Constraints record), and the evidence/comparison view (F010). **P1:** separately displayed growth/season cases (F011/F012) and counterfactual comparisons (F013), per [FEATURE_PRIORITIES](../FEATURE_PRIORITIES.md). **P2/P3 future:** carbon, biodiversity, flood/runoff, cooling temperature, AQI, lifecycle savings and citywide equity require separate validated models and data. Show disabled labelled feature affordances or explicit **FUTURE CONCEPT** artboards, never fake live KPIs.

Every substantial metric card exposes (at least by opening a detail view) units, target, UTC time bin/local zone if relevant, horizon and leaf state, area basis, scenario/layout revision, currentness, run ID, source fingerprints, computation mode, assumptions and coverage limitations.

A valid computed **zero** is a result, not unavailable. Missing data, heuristic exhaustion, cancelled job, model/tool error and evidence status **unknown** are distinct from zero and from proven finite infeasibility.

## 5. Job, scenario and result state machines

### Scenario control

`ACCEPTED CURRENT → USER EDITS DRAFT → DIRTY/STALE → VALIDATED PROPOSED CHANGES → HUMAN ACCEPTS → NEW ACCEPTED REVISION → REAL JOB → VALIDATED RESULT`.

Hypothetical scenario prep has its own immutable reference and never activates the accepted scenario. Agent may request a hypothetical examination but cannot silently change hard constraints, site inputs, budget, objectives, profile states or temporal cases.

At the first draft change, dim or clearly label old results as **not current**, preserving last verified value/history; never relabel it as the value of the draft. Late job completion goes to its original revision and does not overwrite the selected current result. A newer accepted request for the same `(scenario_id, revision, scope, view_slot)` supersedes the older selection even within one revision; if that newer request fails or is cancelled, the slot shows no current result and never falls back to the older one (CONTRACTS §5). A rerun must be a typed API/job action and may fail; never 'clear stale' locally without backend evidence.

### Job and result conditions to render

Each row below is a derived UI condition, not a backend state. It is computed from `Job.status` ∈ {`queued`, `running`, `completed`, `failed`, `cancelled`} (CONTRACTS §5), the separate `superseded_by_revision` marker, the delivery/provenance `execution_mode` ∈ {`live`, `cached`, `recorded`, `fixture`}, the backend selections endpoint and site readiness. The frontend currentness values are `current`, `stale-draft`, `not-selected` and `superseded` (`frontend/src/planning/evaluation.ts`). `SITE_NOT_READY` and `UNSUPPORTED_OPERATION` are request errors, not job states. The backend status enum is unchanged, and a delivery badge overlays the completed conditions rather than replacing them.

| UI condition (derived) | Interface |
| --- | --- |
| Not requested | Neutral empty state with exactly what remains selectable/required |
| Queued | Job ID, selected scenario, waiting state and optional cancel |
| Running | Tool/operation, status/time if available, bounded progress only when measurable |
| Completed current | Result metric, outcome/constraints, run identity and provenance |
| Completed superseded | Historical result with stale/superseded status; no silent selection |
| Cancelled | Explicit cancellation; no fabricated final result |
| Failed / unsupported | Typed safe error, what was attempted, recovery/manual fallback |
| Cached/recorded/fixture | Persistent delivery badge and original computation identity, not 'live' |
| Site not ready | Blocked action with the typed `SITE_NOT_READY`/`UNSUPPORTED_OPERATION` error and the current readiness blockers; no "ready" badge for any `real_site`. Today `compute_readiness` reports rights/datum/coverage blockers but none for real-site geodesy, semantics or shadow context, and the runtime real-site refusal is generic; precise real-site reasons need backend readiness work (#10/#30) |

The server owns feasibility. A successful job may return a valid zero-planting outcome or exhausted search **without** implying a useful feasible proposal; model limitations must remain visible.

## 6. Agent as an evidence investigator, not a chatbot

### Interaction model

Compact entry point in Planting Studio for the accepted scenario only; open an investigation drawer on demand. `AgentLoop` pins every call to one accepted scenario and site, so in City Explorer the entry point is disabled and labelled "no agent tools for visual-only features". Selected-feature context reaches the model only as IDs, or as quoted untrusted data inside a tool observation, never in the trusted host-context block (AGENTS.md rule 8).

**Current prerequisite:** no browser-facing agent-run API exists yet. `api/app.py` has no agent-run route. The out-of-process agent loop reaches the backend only through the domain `/operations` and `/jobs` routes, and `CompareScreen.tsx` already shows "no planning-agent endpoint" as an unavailable state. The drawer keeps that state until the typed agent-run API in [#73](https://github.com/Pimentellll/sheffield-tree-planner/issues/73) exists, with the frontend consumer in [#74](https://github.com/Pimentellll/sheffield-tree-planner/issues/74).

Visible progression: **User question → grounded current scenario/selected feature → supported operation → validated arguments → job submitted/observed → returned result references → clear explanation → next optional hypothesis → human review for consequential edits**.

Show only actual observable tool actions and result IDs; do **not** display invented private reasoning or claim agent intelligence from scripted fixture text. Numerics and constraints always come from deterministic tools. The model may select a tool and interpret evidence; it cannot invent physical results, waive checks, access arbitrary network/files/SQL or self-approve proposals.

**Explanation vs model text.** The authoritative summary is the host-generated `Outcome.narrative`, built from backend Results (`AgentLoop._conclusion` in `backend/src/tree_planner/agents/__init__.py`). The model's own prose is kept as `untrusted_model_narrative`. If it is shown at all, it goes in a separate block labelled **Model interpretation, not a computed result**, never styled as a result; every number in it must trace to a cited run ID or be flagged as unsupported.

**Run outcomes.** Today's `AgentLoop` host outcomes are `completed`, `needs_evidence`, `draft_prepared` and `metadata_only`. Agent-run statuses such as clarification requested, safe abstention, stopped and exhausted are proposed, per #73 and draft PRs [#70](https://github.com/Pimentellll/sheffield-tree-planner/pull/70)/[#71](https://github.com/Pimentellll/sheffield-tree-planner/pull/71); they are not contract. Render whatever #73 finally defines, alongside `failed`/`cancelled`, rather than a separate list from this document.

### Important UX sequences

**A. 'Why here rather than there?'** Agent may call `compare_locations(scenario_ref, layout_ref, placement_id, alternative_position_enu_m)` for a **proposed** placement (recorded/existing scene trees are not movable), with other placements and assumptions fixed. Present original/alternative physical shade, costs/constraints and the infeasibility reason, with source/run IDs. **Current limitation ([#65](https://github.com/Pimentellll/sheffield-tree-planner/issues/65)):** `relocate()` keeps the tree's candidate/location identity, so every alternative currently returns a diagnostic infeasible result with reason `candidate mismatch` (`backend/src/tree_planner/search/__init__.py`). Show that reason from the Result reasons, not only the grouped "candidate and profile" constraint record, and label it "not a permitted alternative", never a better option or a spatial/site infeasibility, until #65 lands. Do not silently perform an unrelated redesign or say the agent has proven a globally optimal location.

**B. Budget changed (synthetic demo: 20000 pence = £200.00 → e.g. 15000 pence = £150.00).** Show unsaved draft and stale old metrics. A reduction may be analysed as a labelled hypothetical; an increase is a relaxation that can only be prepared, and is analysed after a human accepts a new revision, followed by a typed search job. Show the backend refusal ("Analysis exceeds the accepted budget", `agents/policy.py`) if analysis of a relaxation is attempted early. The agent can explain tradeoffs but approval is human. Money is stored as integer pence and converted to £ once for display. This is a manual-UI flow; it is an agent flow only when the deployed operation set includes `prepare_scenario` within the 8,192-token request limit (the event-day tool set does not).

**C. 'Will this cool the park by 2°C?'** Unsupported thermal claim: explicitly say shade-only model cannot quantify ambient cooling; offer validated geometric shade information and required future thermal/weather inputs instead of inventing a °C value.

**D. Model unavailable.** Preserve manual evaluate/search/compare controls. State the missing genuine local-model evidence; never present fixed workflow as a successful Nemotron trace.

**E. Scenario challenge.** For `compare_scenarios`, explicitly distinguish `fixed_layout` versus `redesign`, enumerate changed inputs and keep case/time/site identity compatible. Show why controlled conclusion is refused if comparison changed undeclared factors. This is a manual-UI flow; `AgentLoop` refuses `compare_scenarios` unless a hypothetical was first prepared in the same session, and the event-day agent tool set (`inspect_site`, `evaluate_layout`, `search_layouts`, `compare_locations`, per `docs/event-day/science/AGENT_EVALUATION_PROTOCOL.md` on main) leaves out `prepare_scenario` and `compare_scenarios`. It becomes an agent flow only when the deployed operation set includes both within the 8,192-token limit.

**F. Ambiguous request.** The agent asks for clarification. In the preferred case no computation Job or metric card is shown; a metadata-only `inspect_site` is allowed. A PASS-B run states its interpretation, runs only `search_layouts` or `evaluate_layout` within the accepted task and asks the user to confirm; show that stated interpretation with its Job and confirmation request before anything further. Graded by C4's pre-registered PASS-A/PASS-B/FAIL in `docs/event-day/science/AGENT_EVALUATION_PROTOCOL.md` (main); today's host status for PASS-A is `needs_evidence`/`metadata_only`. Render the clarification state as #73 defines it.

The drawer renders the operation list actually exposed in the run and shows "not available to the agent in this run" for any other operation.

### Agent workspace anatomy

Question and explicit selected-site/scenario context; scope/capabilities banner with the run's exposed operations; tool-action timeline (operation, args digest, job/run IDs, status; needs the #73 API); host-generated summary, with any model text in its separately labelled block; result summaries and comparisons; assumptions and constraints; cited source/result chips; human acceptance card for new proposals. Minimise clutter when closed. Tool IDs and numerical values use JetBrains Mono, never generic fake probability/confidence badges.

## 7. Map and visualisation rules

- City viewer is a geographic/navigation surface; Scientific Studio uses validated local geometry when and only when site gates pass. The same camera imagery **must not** imply solver/viewer geometry parity without testing. Until an approved row in `docs/event-day/science/EVIDENCE_AND_CLAIMS_LEDGER.md` (on main) says otherwise, ledger row S-08 governs: any real-geography view is labelled **visual context only**, and results come from synthetic geometry (`SCIENTIFIC_ACCEPTANCE.md` S-02).
- Scene overlays: recorded trees, inferred crowns, candidates, selected proposal, exclusions, target receivers, shadow if computed/declared. Each toggled layer actually changes visible data, not only local checkbox styles.
- A sun-time preview is labelled **visualisation only** unless bound to a computed scenario case. Changing year/leaf state requires a stored case/result or a new job; no hardcoded shade multipliers.
- Compare A/B displays same site and compatible source/case, a common legend and scale; side-by-side, swipe and difference-only modes are enabled only if implemented. Both halves show matching time/provenance.
- Existing green and proposed lime; Plan A blue and B amber (no other scene class uses amber); exclusions, survey-required positions and the site-level heritage banner coral, told apart by shape. Add shape/hatch/stroke differences for colour-blind users.
- Profile large feature counts and map memory; never claim a client Three.js canvas proves DGX-accelerated physical simulation.

## 8. Design system, densities and accessibility

Retain [UI_DESIGN_REFERENCE](../UI_DESIGN_REFERENCE.md) base tokens: Forest `#101E1B`, Pine `#243D35`, Lime `#B7E879`, Ivory `#F4F3ED`, Water `#62AFC2`, Heat `#E8A476`, Constraint `#D67C64`, Canopy `#527A55`. Tone should be restrained, map-first, high contrast, not noisy/neon. Manrope display, Inter UI, JetBrains Mono numeric/IDs/units. Test actual WCAG contrast rather than assuming palette pairs pass.

Desktop prototype reference viewport 1600×1000 or 1920×1080; tablet 1024×768; mobile approximately 390×844. Keyboard operability, visible focus, status aria-live announcements, accessible feature list/table, sufficient touch targets, reduced-motion response and stable drawer focus are required. Avoid controls that hide the map or inaccessible hover-only evidence.

No permanent overload of simultaneously open context, agent and scenario panels. At most one primary side drawer plus compact auxiliary information in normal exploration; allow deliberate split-view mode for Compare.

## 9. Design artifact and implementation handoff matrix

**Timing:** this design exploration is post-submission work. It does not start before the 13 November 16:00 engineering freeze, and it keeps the existing forest/ivory direction rather than opening new aesthetic directions ([UI_DESIGN_REFERENCE](../UI_DESIGN_REFERENCE.md)).

The design exercise should yield state-coverage artboards in the existing direction, not one beautiful static concept:
- city explorer, layers, Weston Park tree selection, inferred canopy inspector, readiness (including heritage review), studio geometry/tree selection;
- budget editing, stale state, job running/completed, search rankings, two-plan comparison, winter-limit pass/fail;
- compact agent, expanded investigation, tool trace, 'why here' showing the current diagnostic `candidate mismatch` result (#65), hypothetical review, clarification, unsupported/failure, model text containing an unsupported number;
- review pack, source/rights view, mobile explorer, tablet Studio.

Use a consistent sample scenario (the synthetic demo: 20000 pence = £200.00, maximum two trees), numbers, units, run IDs and visually labelled **ILLUSTRATIVE / SYNTHETIC** status. Provide a contact sheet, interaction storyboard, component inventory, key states and selected final design. A design image is **not an implemented UI** and may not assert functionality.

The UI implementation PRs must supply actual screenshots/browser interaction receipts from source SHA; PNG concept art alone does not pass a functional issue.

## 10. Implementation slices and acceptance

UX3D-xx rows are supplementary acceptance checklists, not task IDs, assignments or a status board (AGENTS.md rule 10). [BUILD](../BUILD.md) is the only status home. Live issue assignment governs; this table assigns no writer. Status: see BUILD / the mapped issue. GEO3D-xx IDs are defined in [PR #66](https://github.com/Pimentellll/sheffield-tree-planner/pull/66).

| ID | Deliverable | Explicit acceptance | Dependencies | Existing B/F IDs and issues |
| --- | --- | --- | --- | --- |
| UX3D-01 | Final map-first information architecture and visual tokens | Selected coherent state-coverage artboards in the existing forest/ivory direction; mobile/desktop focus hierarchy | Design only; post-submission (§9) | B05 (UI_DESIGN_REFERENCE handoff); no issue assigned |
| UX3D-02 | Single-site explorer shell and camera (Weston Park visual pilot) | North/tilt/zoom/reset/search/layer states work on source-backed geospatial data; visual-only label | GEO3D-03 (alignment) and GEO3D-04 | B05, F001/F002; viewer work is Alex's existing unmerged branch `feat/alex/terrain-context-view` (`b1bb0e5`) / [#16](https://github.com/Pimentellll/sheffield-tree-planner/issues/16). Event day: P2-deferred ([issue index](../EVENT_DAY_ISSUE_INDEX_2026-11-13.md) X-E06). Citywide browsing/LOD is F024 (P2) and F025/F033 (P3) and needs explicit assignment plus a method/data/rights/validation plan |
| UX3D-03 | Tree inspector and symbology | Source-linked IDs; `evidence_class`/`match_status` tokens from PR #66 §3.2, each with a symbol or an inspector-only note (§3); capture date **Not recorded by source** when absent; no false species/height; keyboard alternative | GEO3D-01/05 | F002; producer [#69](https://github.com/Pimentellll/sheffield-tree-planner/issues/69) (`recorded_location`); viewer #16 |
| UX3D-04 | Site readiness and city→studio handoff | Accepted site vs visual-only/blocked; coordinate/site identity preserved; typed `SITE_NOT_READY`/unsupported error with current blockers, no "ready" badge for any `real_site`; heritage review shown for Weston Park | GEO3D-03/06; explicit real-site readiness blockers (geodesy/V03, semantics, shadow context, B08 parity) added to `compute_readiness` | B03/B08, F001; [#10](https://github.com/Pimentellll/sheffield-tree-planner/issues/10), [#30](https://github.com/Pimentellll/sheffield-tree-planner/issues/30) |
| UX3D-05 | Studio controls/currentness hardening | Draft edit marks old result stale; acceptance required; late result cannot overwrite; same-slot supersession and no fallback after a failed/cancelled newer request; unsupported controls disabled | Existing contract | B05, F009/F010; [#17](https://github.com/Pimentellll/sheffield-tree-planner/issues/17), [#25](https://github.com/Pimentellll/sheffield-tree-planner/issues/25); extends `classifyResult`/`CURRENTNESS_LABEL`/`describeJob` |
| UX3D-06 | Agent investigation drawer | Real registered tool action/observation/references; Job states plus agent-run states as #73 defines them (clarification, abstention, stopped/exhausted are proposals), human approval and manual fallback; host summary separate from labelled model interpretation; exposed-operation list | #73 typed agent-run API (not yet implemented); until then the existing "no planning-agent endpoint" state | B05/B10, F008/F013; [#73](https://github.com/Pimentellll/sheffield-tree-planner/issues/73) (API, Ben), [#74](https://github.com/Pimentellll/sheffield-tree-planner/issues/74) (consumer, Arnav), [#29](https://github.com/Pimentellll/sheffield-tree-planner/issues/29)/[#56](https://github.com/Pimentellll/sheffield-tree-planner/issues/56) (panels, Alex), [#26](https://github.com/Pimentellll/sheffield-tree-planner/issues/26). Agent-evidence UI: Arnav (#74); surrounding UI shell: Alex (#56); API: Ben (#73), as assigned on those issues |
| UX3D-07 | Metric/evidence hierarchy | Physical vs utility units, `quantity_kind`, winter loss vs limit, exact cases/versions, zero/missing/cache/fixture, survey and rights status | Results | F010; #17, #29, #74; extends `EXECUTION_MODE_LABEL` |
| UX3D-08 | Comparison and report fidelity | Stored compatible run identities, changed factors, no invented benefit, rights-aware review pack with heritage/survey conditions | Results | B12, F010; #29, [#32](https://github.com/Pimentellll/sheffield-tree-planner/issues/32) (client-built review pack partly exists) |
| UX3D-09 | Responsive, access, rendering QA | 1920/1600/1024/390 captures, keyboard, contrast, map layer state, UI performance receipts | Above | B05/B12; receipts attach to the issue of the slice being captured |

These rows add acceptance deltas beyond the mapped issues only; they extend the existing components (`frontend/src/planning/evaluation.ts`, `frontend/src/panels/CompareScreen.tsx`, `Requirements.tsx`, `ReportScreen.tsx`) rather than rebuilding them, and must not reset already passing tests. Implementation PRs cite their STP/M/B/F/V IDs and issue; a UX3D row is an optional supplementary reference. See [BUILD](../BUILD.md) for actual completion, owner reviews, merge state and genuine Nemotron/Spark proof. The 13 November event-day priorities keep core demo and submission ahead of citywide interface redesign.

## 11. Acceptance tests for the user journey

1. Open the Weston Park explorer → rotate/tilt camera → select a `recorded_location` tree. Inspector shows source layer, source record ID (`objectid`, labelled a service record ID, not a field-verified tree ID), retrieval time and source file SHA-256; capture/survey date shows **Not recorded by source** unless the source supplies it, never back-filled from catalogue/publisher update dates; no invented biological details.
2. Select a `detected_crown` ("inferred crown") → source/method/unknowns shown; it does not become a `field_verified` tree.
3. Try to run real-site physics before V03/B08 acceptance → action is blocked with a typed `SITE_NOT_READY`/unsupported error plus the current readiness blockers; no "ready" badge for any `real_site`; *synthetic test* remains separately accessible.
4. Open accepted synthetic Studio, evaluate → queued/running/completed states from real job; actual `m2_h` result and scenario/run provenance.
5. Change budget → old result immediately stale, then a new human-accepted revision/job; verify late old job is historical only. A newer request for the same revision/slot supersedes an older one; if the newer request fails or is cancelled the slot shows no current result and never falls back to the older result.
6. Ask agent 'Why this position?' → bounded comparison tool or honest unsupported fallback; result cites real tool/run and no hidden invented °C. Until #65 lands, a `compare_locations` result passes only if its `candidate mismatch` reason is shown and it is labelled "not a permitted alternative". The host summary is the explanation; any model text appears only under **Model interpretation, not a computed result**.
7. Ask unsupported flood/AQI/cooling request → explicit unsupported model and safe explanation, not a fabricated KPI.
8. Compare incompatible cases → block false controlled difference; compatible cases show same site/scale/unit/cost basis and changed factors.
9. Prepare review pack → rights/export checks, survey conditions and, for Weston Park, the heritage review requirement; never call a report 'planting approval'.
10. Manual mode works with model endpoint missing; fixture/cache states cannot masquerade as real inference.
11. Ask an ambiguous request → clarification state; no computation Job or metric card, at most a metadata-only `inspect_site` (C4 PASS-A). A PASS-B run shows its stated interpretation and confirmation request.

**Review gates:** Alex validates actual UI/3D interaction, Ben backend contracts and tool loop, Arnav physical evidence/claim meaning. Any product-architecture change must keep [CONTRACTS](../CONTRACTS.md) as the authority, maintain generated types and preserve scientific fail-closed behaviour. This document is not permission to silently merge production code or alter shared deployment.
