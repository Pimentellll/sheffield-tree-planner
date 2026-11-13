# CANOPY Sheffield — 3D product experience, agent investigation and evidence UI implementation specification

**State:** proposed implementation contract, **not** acceptance of real Sheffield geometry, agent/model performance or environmental benefits. Date: 13 November 2026.  
**Proposed owners:** Alex frontend/UI; Ben agent/API/revision plumbing; Arnav semantics/claims/visual-to-numerical parity.  
**Read with:** [BUILD](../BUILD.md), [UI_DESIGN_REFERENCE](../UI_DESIGN_REFERENCE.md), [SPEC](../SPEC.md), [CONTRACTS](../CONTRACTS.md), [FEATURE_PRIORITIES](../FEATURE_PRIORITIES.md), [NUMERICS](../NUMERICS.md), [VALIDATION](../VALIDATION.md), and [3D city/tree pipeline](3D_CITY_AND_TREE_PIPELINE.md) once merged.

## 1. Objective and design audit

Primary task: **explore a geospatial 3D scene → select a source-linked tree/site → work on a bounded scenario → use deterministic tools (manually or with a bounded agent) → inspect trustworthy evidence → compare → prepare a review pack**.

Preserve CANOPY's forest/ivory visual identity, but make the spatial view the dominant canvas. The historical Claude artboards are visual proposals, not running GIS data or validated results. The current local Three.js Studio is an engineering representation, not a city-scale digital twin.

### Explicit UX flaws to correct

| Finding | Impact | Implementation requirement |
| --- | --- | --- |
| Permanent dense panels shrink the map | Hard to navigate and see proposed geometry | Spatial canvas receives primary space; collapsible context inspector/controls and persistent compact navigation |
| City overview artboards imply data-backed heat/flood/AQI/equity | Unsupported environmental claims | Only permitted source context; no calculated physical benefit without corresponding validated engine |
| Original 'Generate' only reset local stale state | Fake solver affordance | Submit real typed job to backend, show queued/running/terminal delivery and selected run identity |
| Original weights/constraints are illustrative | Invalid multi-objective and waived hard constraints | Only supported shade-first objective; disabled future selectors; hard rules enforced server-side; unaccepted edits remain draft |
| Agent card was static sample text | Unverifiable 'AI value' | Actual registered tool selection, bounded observations, references, provenance and human approval |
| Flat geospatial illustration used as reference | False map/metric parity | Geographic layers and scientific assets explicitly separated; real UI never depicts decorative mesh as accepted solver geometry |
| Selected tree has unclear evidence class | Users mistake detected canopy for verified trees | Persistent tree status and source identity for recorded/inferred/unknown/field-verified |
| Old results look current after editing | User may adopt invalid plan | Explicit dirty → stale, late-results guard, immutable revision/run links and selectable run history |
| Time sliders imply changing results | Visual state confused with computed season/case | Mark camera/sun preview separate from evaluated case, require new run or show verified stored result |
| Widgets too numerous | Users cannot find main task | Progressive disclosure; primary metric hierarchy; detailed provenance in inspector/drawer |

## 2. Information architecture

Four top-level destinations with a persistent selected-site context:
1. **City Explorer** — Sheffield geographic orientation; browse a source-backed 3D scene, identify/inspect trees, select a site. This is an optional city-scale module, not a dependency for the synthetic P0 solver.
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

Appearance and backing data must match:

| Object | Visual treatment | Inspector status |
| --- | --- | --- |
| Recorded existing tree | Deep canopy green shape + distinctive solid marker | Recorded position; source ID/capture epoch; independent field verification unknown unless evidenced |
| LiDAR/inferred crown | Desaturated textured crown/dashed perimeter | Inferred geometry; method, confidence/limits |
| Unknown elevated object | Neutral stipple/outline | Unknown vegetation/building classification; not assigned tree identity |
| Proposed tree | Lime crown/halo and numeric ID | Hypothetical/selected layout reference, state/horizon and cost |
| Candidate position | Small selectable outlined point (cluster at distance) | Candidate catalogue revision and status |
| Excluded/constraint position | Coral crosshatch/stop icon | Constraint/evidence reference; cannot be placed via chat |
| Survey required | Amber question badge/hatch | Provisional; not approved for planting |
| Compare A-only/B-only/shared | Blue / amber / split-outline, not colour alone | Same-site case comparison and per-layout identity |
| Selected feature | High-contrast outline + anchor + accessibility focus | Object ID, source, date, related result |

Never paint an existing recorded tree as a verified LiDAR crown if only a point record exists. At zoomed-out scales use clusters/coverage with visible legend, not 100,000 tiny selectable circles. Inferred shape/height/canopy should be marked approximate. Tooltips are supplemental; source and status remain available in a persistent inspector.

Tree inspector minimum: name/identifier, recorded/detected class, location (coordinate frame properly labelled), geometry/date, provenance and rights, available sourced attributes, uncertainty, relationship to baseline shade, actions supported by the current site. Unknown species/height/health must show **Not recorded** rather than filler.

## 4. Metric and evidence dictionary

The hierarchy is **decision → primary quantitative evidence → constraints/unknowns → explanation/provenance**. Values must be bound from backend results, source records or explicitly synthetic *design-example* fixtures.

| Metric/UI | Required semantics | Do not substitute |
| --- | --- | --- |
| Proposed tree count | Number of proposals in selected immutable layout | Existing city tree count or hardcoded artwork |
| Budget / cost | GBP, backend integer pence, upfront basis, profile price date/scope | Lifecycle cost, quote, monetised benefit |
| Budget remaining | Same accepted budget basis less computed upfront cost | Uncommitted draft budget with old result |
| Physical additional shade | Actual metric instance, `m2_h`, exact target/case/tree state, current result | °C cooling, general 'shade area', irradiance or weighted utility |
| Weighted utility | `weighted_m2_h`, exact declared weights/targets | Physical unweighted shaded area |
| Candidate eligibility | Finite catalogue validation and explicit rule status | Planting permission or utility/soil survey |
| Constraints | Pass/fail/unknown plus observed/limit/affected scene revision | 'All clear' on unspecified checks |
| Growth and winter | Individually computed stored case / supported declared state | Arbitrary year-based UI multiplier or sun animation |
| Source status | Capture date, accuracy, coverage, licence/display/export gates | 'Verified Sheffield science' from a source link |
| Agent evidence | Registered operation, accepted/hypothetical refs, validated args, job and run IDs, actual observation | Prewritten agent answer or invented '20 trials' |
| Cache/execution | Live/cached/recorded/fixture as returned with result delivery | Treat cached or recorded response as fresh computation |

**Core P0/P1:** physical shade and upfront costs; optional declared growth/winter cases and controlled comparison when supported. **P2/P3 future:** carbon, biodiversity, flood/runoff, cooling temperature, AQI, lifecycle savings and citywide equity require separate validated models and data. Show disabled labelled feature affordances or explicit **FUTURE CONCEPT** artboards, never fake live KPIs.

Every substantial metric card exposes (at least by opening a detail view) units, target, UTC time bin/local zone if relevant, horizon and leaf state, area basis, scenario/layout revision, currentness, run ID, source fingerprints, computation mode, assumptions and coverage limitations.

A valid measured/computed **zero** is a result, not unavailable. Missing data, heuristic exhaustion, cancelled job, model/tool error and evidence status **unknown** are distinct from zero and from proven finite infeasibility.

## 5. Job, scenario and result state machines

### Scenario control

`ACCEPTED CURRENT → USER EDITS DRAFT → DIRTY/STALE → VALIDATED PROPOSED CHANGES → HUMAN ACCEPTS → NEW ACCEPTED REVISION → REAL JOB → VALIDATED RESULT`.

Hypothetical scenario prep has its own immutable reference and never activates the accepted scenario. Agent may request a hypothetical examination but cannot silently change hard constraints, site inputs, budget, objectives, profile states or temporal cases.

At the first draft change, dim or clearly label old results as **not current**, preserving last verified value/history; never relabel it as the value of the draft. Late job completion goes to its original revision and does not overwrite the selected current result. A rerun must be a typed API/job action and may fail; never 'clear stale' locally without backend evidence.

### Job states to render

| Backend state | Interface |
| --- | --- |
| Not requested | Neutral empty state with exactly what remains selectable/required |
| Queued | Job ID, selected scenario, waiting state and optional cancel |
| Running | Tool/operation, status/time if available, bounded progress only when measurable |
| Completed current | Result metric, outcome/constraints, run identity and provenance |
| Completed superseded | Historical result with stale/superseded status; no silent selection |
| Cancelled | Explicit cancellation; no fabricated final result |
| Failed / unsupported | Typed safe error, what was attempted, recovery/manual fallback |
| Cached/recorded/fixture | Persistent delivery badge and original computation identity, not 'live' |
| Site not ready | Blocked action with required source/survey/geodesy evidence |

The server owns feasibility. A successful job may return a valid zero-planting outcome or exhausted search **without** implying a useful feasible proposal; model limitations must remain visible.

## 6. Agent as an evidence investigator, not a chatbot

### Interaction model

Persistent compact entry point with selected-feature context; open an investigation drawer on demand.

Visible progression: **User question → grounded current scenario/selected feature → supported operation → validated arguments → job submitted/observed → returned result references → clear explanation → next optional hypothesis → human review for consequential edits**.

Show only actual observable tool actions and result IDs; do **not** display invented private reasoning or claim agent intelligence from scripted fixture text. Numerics and constraints always come from deterministic tools. The model may select a tool and interpret evidence; it cannot invent physical results, waive checks, access arbitrary network/files/SQL or self-approve proposals.

### Important UX sequences

**A. 'Why here rather than there?'** Agent may call `compare_locations` with same layout, tree ID, one alternative position, fixed other placements and matching assumptions. Present original/alternative physical shade, costs/constraints and any infeasibility, with source/run IDs. Do not silently perform an unrelated redesign or say the agent has proven a globally optimal location.

**B. Budget changed to £75,000.** Show unsaved draft and stale old metrics, selected/hypothetical new revision, accepted changes and recomputed search (if available); agent can explain tradeoffs but approval is human.

**C. 'Will this cool the park by 2°C?'** Unsupported thermal claim: explicitly say shade-only model cannot quantify ambient cooling; offer validated geometric shade information and required future thermal/weather inputs instead of inventing a °C value.

**D. Model unavailable.** Preserve manual evaluate/search/compare controls. State the missing genuine local-model evidence; never present fixed workflow as a successful Nemotron trace.

**E. Scenario challenge.** For `compare_scenarios`, explicitly distinguish `fixed_layout` versus `redesign`, enumerate changed inputs and keep case/time/site identity compatible. Show why controlled conclusion is refused if comparison changed undeclared factors.

### Agent workspace anatomy

Question and explicit selected-site/scenario context; scope/capabilities banner; tool-action timeline (operation, args digest, job/run IDs, status); result summaries and comparisons; assumptions and constraints; cited source/result chips; human acceptance card for new proposals. Minimise clutter when closed. Tool IDs and numerical values use JetBrains Mono, never generic fake probability/confidence badges.

## 7. Map and visualisation rules

- City viewer is a geographic/navigation surface; Scientific Studio uses validated local geometry when and only when site gates pass. The same camera imagery **must not** imply solver/viewer geometry parity without testing.
- Scene overlays: recorded trees, inferred crowns, candidates, selected proposal, exclusions, target receivers, shadow if computed/declared. Each toggled layer actually changes visible data, not only local checkbox styles.
- A sun-time preview is labelled **visualisation only** unless bound to a computed scenario case. Changing year/leaf state requires a stored case/result or a new job; no hardcoded shade multipliers.
- Compare A/B displays same site and compatible source/case, a common legend and scale; side-by-side, swipe and difference-only modes are enabled only if implemented. Both halves show matching time/provenance.
- Existing green and proposed lime; Plan A blue and B amber; exclusions coral. Add shape/hatch/stroke differences for colour-blind users.
- Profile large feature counts and map memory; never claim a client Three.js canvas proves DGX-accelerated physical simulation.

## 8. Design system, densities and accessibility

Retain [UI_DESIGN_REFERENCE](../UI_DESIGN_REFERENCE.md) base tokens: Forest `#101E1B`, Pine `#243D35`, Lime `#B7E879`, Ivory `#F4F3ED`, Water `#62AFC2`, Heat `#E8A476`, Constraint `#D67C64`, Canopy `#527A55`. Tone should be restrained, map-first, high contrast, not noisy/neon. Manrope display, Inter UI, JetBrains Mono numeric/IDs/units. Test actual WCAG contrast rather than assuming palette pairs pass.

Desktop prototype reference viewport 1600×1000 or 1920×1080; tablet 1024×768; mobile approximately 390×844. Keyboard operability, visible focus, status aria-live announcements, accessible feature list/table, sufficient touch targets, reduced-motion response and stable drawer focus are required. Avoid controls that hide the map or inaccessible hover-only evidence.

No permanent overload of simultaneously open context, agent and scenario panels. At most one primary side drawer plus compact auxiliary information in normal exploration; allow deliberate split-view mode for Compare.

## 9. Design artifact and implementation handoff matrix

The design exercise should yield multiple real visual artifacts, not one beautiful static concept:
- 3 aesthetic directions × 2 flagship screens (6);
- city explorer, layers, Weston Park tree selection, inferred canopy inspector, readiness, studio geometry/tree selection (8);
- budget editing, stale state, job running/completed, search rankings, two-plan comparison (6);
- compact agent, expanded investigation, tool trace, evidence-backed 'why here', hypothetical review, unsupported/failure (6);
- review pack, source/rights view, mobile explorer, tablet Studio (4).

**30 high-fidelity artboards minimum** as a design goal, with consistent sample scenario, numbers, units, run IDs and visually labelled **ILLUSTRATIVE / SYNTHETIC** status. Provide a contact sheet, interaction storyboard, component inventory, key states and selected final design. A design image is **not an implemented UI** and may not assert functionality.

The UI implementation PRs must supply actual screenshots/browser interaction receipts from source SHA; PNG concept art alone does not pass a functional issue.

## 10. Implementation slices and acceptance

| ID | Deliverable | Explicit acceptance | Owner / dependencies | State |
| --- | --- | --- | --- | --- |
| UX3D-01 | Final map-first information architecture and visual tokens | 3 creative directions audited; selected coherent artboards; mobile/desktop focus hierarchy | Alex + Arnav; design only | PROPOSED |
| UX3D-02 | City explorer shell and camera | North/tilt/zoom/reset/search/layer states work on source-backed geospatial data; visual-only label | Alex; GEO3D-04 | PROPOSED |
| UX3D-03 | Tree inspector and symbology | Source-linked stable IDs, recorded/inferred/unknown status, no false species/height; keyboard alternative | Alex; GEO3D-01/05 | PROPOSED |
| UX3D-04 | Site readiness and city→studio handoff | Accepted site vs visual-only/blocked; coordinate/site identity preserved | Alex + Arnav + Ben; GEO3D-03/06 | PROPOSED |
| UX3D-05 | Studio controls/currentness hardening | Draft edit marks old result stale; acceptance required; late result cannot overwrite; unsupported controls disabled | Alex + Ben; existing contract | PROPOSED (verify tests already in BUILD) |
| UX3D-06 | Agent investigation drawer | Real registered tool action/observation/references, queued/running/fail/unsupported/human approval and fallback | Alex + Ben; registered model/tools | PROPOSED |
| UX3D-07 | Metric/evidence hierarchy | Physical vs utility units, exact cases/versions, zero/missing/cache/fixture, survey and rights status | Alex + Arnav; results | PROPOSED |
| UX3D-08 | Comparison and report fidelity | Stored compatible run identities, changed factors, no invented benefit, rights-aware review pack | Alex + Ben + Arnav | PROPOSED |
| UX3D-09 | Responsive, access, rendering QA | 1920/1600/1024/390 captures, keyboard, contrast, map layer state, UI performance receipts | Alex; above | PROPOSED |

These are additive future/acceptance items and must not reset already passing tests or replace existing issue task IDs. See [BUILD](../BUILD.md) for actual completion, owner reviews, merge state and genuine Nemotron/Spark proof. The 13 November event-day priorities keep core demo and submission ahead of citywide interface redesign.

## 11. Acceptance tests for the user journey

1. Open **city** at Weston Park → rotate/tilt camera → select **recorded** tree. Inspector shows source ID/capture date, not invented biological details.
2. Select **inferred** crown → source/method/unknowns shown; it does not become a field-verified street tree.
3. Try to run real-site physics before V03/B08 acceptance → action is blocked with precise missing geometry/rights/datum/context; *synthetic test* remains separately accessible.
4. Open accepted synthetic Studio, evaluate → queued/running/completed states from real job; actual `m2_h` result and scenario/run provenance.
5. Change budget → old result immediately stale, then a new human-accepted revision/job; verify late old job is historical only.
6. Ask agent 'Why this position?' → bounded comparison tool or honest unsupported fallback; result cites real tool/run and no hidden invented °C.
7. Ask unsupported flood/AQI/cooling request → explicit unsupported model and safe explanation, not a fabricated KPI.
8. Compare incompatible cases → block false controlled difference; compatible cases show same site/scale/unit/cost basis and changed factors.
9. Prepare review pack → rights/export checks and survey conditions; never call a report 'planting approval'.
10. Manual mode works with model endpoint missing; fixture/cache states cannot masquerade as real inference.

**Review gates:** Alex validates actual UI/3D interaction, Ben backend contracts and tool loop, Arnav physical evidence/claim meaning. Any product-architecture change must keep [CONTRACTS](../CONTRACTS.md) as the authority, maintain generated types and preserve scientific fail-closed behaviour. This document is not permission to silently merge production code or alter shared deployment.
