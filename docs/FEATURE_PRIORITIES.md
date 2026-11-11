# Feature priorities and hackathon scope

**Status:** proposed plan; no item below is implemented. Canonical feature catalogue. [SPEC](SPEC.md) owns product requirements; [CONTRACTS](CONTRACTS.md) wire meanings; [NUMERICS](NUMERICS.md) mathematics; [BUILD](BUILD.md) tasks/decisions; [VALIDATION](VALIDATION.md) verification.

## Priority definitions

- **P0 — Essential competitive MVP:** complete minimum hackathon decision-support product: site workflow, constrained feasible proposal, computed evidence, interactive recomputation, genuine local Nemotron tool round-trip. The first vertical slice is smaller; not every contract case blocks it.
- **P1 — High-value competitive enhancements:** improve trust, comparison, investigation and presentation after the first P0 path. A hard constraint required by a selected scenario stays mandatory; P1 does not waive it.
- **P2 — Optional environmental extensions:** only after core works and adequate method/data exist; each needs separate evidence and validation.
- **P3 — Long-term roadmap:** post-hackathon research/product scope, outside critical path.

Priority is delivery order, not scientific permission. Metrics need deterministic validation, provenance and limitations. Label synthetic scenes; real Sheffield claims require B03/B08 site/rights gates. Status describes product capability.

## P0 — Essential competitive MVP

| ID / feature / purpose and user value | Inputs → outputs | Dependencies · proposed owner · B · R | Acceptance · limits · status |
|---|---|---|---|
| F001 Sheffield site: give planners a coherent location. | Georeferenced terrain/buildings, supportable trees, orientation, targets/regions, provenance/unknowns → versioned bundle/survey gaps. | B03→B08 · Arnav+Alex · R01/R07/R08 | Verify rights, CRS, scale, north, semantics/context or reject. Synthetic labelled; no citywide or planting approval. Planned; none accepted. |
| F002 Spatial UI: inspect/edit decisions. | Site, targets, exclusions, layouts, supported controls → 2D/3D view and comparison. | B05 · Alex · R05/R06/R07/R08/R10 | Select targets/edit inputs; label existing/proposed/excluded/unknown. Metrics from evaluator; 3D polish not gate. Planned. |
| F003 Solar/shadow: quantify direct shade. | Geometry, ENU, UTC bins, surfaces, tree states → additional shade over declared period. | B02/B04 · Arnav · R02 · V02/V04 | Direction/units/baseline/reference; no double count. Not temperature/full radiation. Planned. |
| F004 Placement evaluator: compare proposal to existing scene. | Baseline, positions/profiles/case → metrics and constraints. | B04 · Arnav evaluator, Ben wrapper · R02/R03 · V02/V04 | Identical samples/cases, overlap handled, zero valid; initial opaque one-tree case. No biological accuracy claim. Planned. |
| F005 Budget/placement constraints: ensure modelled feasibility. | Upfront budget, finite candidates, exclusions, spacing/clearance/pins → independently checked layout. | B03/B06 · Arnav semantics, Ben plumbing · R01/R03/R07 · V03/V04/V06 | Enforce known constraints/spend/count. Utility, ownership, soil, permits remain survey items; no planting approval. Planned. |
| F006 Basic optimisation: find reproducible alternatives. | Evaluator/candidates/objective/constraints → greedy reference, best evaluated plan, method/seed. | B04→B06 · Arnav · R03 · V04/V06 | Positions/count/cost/objective/improvement/reference/status. No global optimum; heuristic miss is not infeasibility. Planned. |
| F007 Upfront cost: expose budget basis. | Profile cost/date/scope/placements → GBP pence and assumptions. | B01/B06 · Ben+Arnav · R03/R07/R08 · V04/V06 | Reproducible totals; quote vs estimate distinguished. No lifecycle or monetised benefit. Planned. |
| F008 Local Nemotron: choose tool and ground answer. | Request/accepted scenario/registered schemas → actual dispatch/observation/explanation. | B01/B09 then B10 · Ben · R04/R08/R09 · V08/V09 | Record checkpoint/runtime/device/args/result; script/fixture is not proof. Open PR #1 readiness tooling is not B09. Planned; no round-trip evidenced. |
| F009 Replanning: show changed requirement's consequence. | Human-accepted budget/constraint/objective revision → computation at new identity. | B05/B06/B09 · Ben+Alex, Arnav semantics · R05/R06/R08 · V05/V07/V10 | Manual replanning works before full B10; stale immediately, late result cannot replace current, human accepts consequential edits. Planned. |
| F010 Evidence/comparison UI: make choice reviewable. | Immutable result/delivery/provenance → metrics/cost/baseline/feasibility/assumptions/sources/identity/errors. | B05/B08/B12 · Alex+Ben, Arnav review · R07/R08/R10 · V03/V05/V10/V12 | Real metrics/units/run IDs; provisional/stale/cache/recorded/fixture/error labels; no survey certification. Planned. |

**P0 exit:** choose a usable site, request feasible constrained proposal, inspect actual metrics/cost, change supported constraint and genuinely recompute with stale protection; Nemotron genuinely selects a registered tool, observes result and explains it. Real-site assertion also requires B03/B08; eligibility and hardware are separate gates.

## P1 — High-value competitive enhancements

| ID / feature / user value | Inputs → outputs | Dependencies · owner · B · R | Acceptance · limits · status |
|---|---|---|---|
| F011 Young/mature: show timing trade-off. | Declared growth states → separate metrics. | B07 · Arnav · R07 · V02/V07 | Never give young tree mature benefit; not survival forecast. Planned. |
| F012 Summer/winter: reveal seasons. | Supported cases → separate metrics/constraint. | B07 · Arnav+Alex · R02/R07 · V02/V07/V10 | Preserve mandatory P0 winter limits. Planned. |
| F013 Counterfactual agent: explain location/layout alternatives. | Accepted scenario/challenge → relocation/redesign/comparison. | B07/B09/B10 · Ben+Arnav · R04/R05 · V07/V09/V11 | Correct tool, controlled inputs, real observation; refuse unsupported asks. Planned. |
| F014 Sensitivity: show robustness. | Geometry/profile/resolution cases → results/ranking. | B07 · Arnav · R07 · V02/V07 | Separate numerical/input/model uncertainty; no invented probabilities. Planned. |
| F015 Alternatives: support competing priorities. | Objectives/constraints → feasible options. | B06/B07 · Arnav+Alex · R03/R05 · V06/V07 | Disclose objective/cost/count; no universal best. Planned. |
| F016 Lifecycle cost: extend cost view. | Maintenance/replacement/horizon assumptions → estimate. | B07 · Ben+Arnav · R07/R08 · V04/V07 | Explicit validated basis; retain P0 upfront basis. Planned. |
| F017 GPU: measure NVIDIA performance value. | Equivalent CPU/GPU work/device → comparison. | B09/B12 · Ben+Arnav · R09 · V08/V12 | Actual device/fair comparison; no unverified speedup/CUDA/RT claim. Planned. |
| F018 Evidence report: package review. | Validated results/rights/limits → report. | B08/B12 · Alex+Ben · R08/R10 · V03/V12 | Reproducible, rights-cleared, professional checks; not approval. Planned. |

## P2 — Optional environmental extensions

| ID / feature | Inputs → outputs | Dependencies · owner · R | Acceptance/limit · status |
|---|---|---|---|
| F019 Rain interception | Rain/canopy/method → interception | Post-B12 · Arnav · R07/R08 | Not runoff/flood reduction; validate. Roadmap. |
| F020 Carbon | Biology/growth/provenance → estimate | Post-B12 · Arnav · R07/R08 | Separate validated biological model. Roadmap. |
| F021 Multi-objective | Valid metrics/priorities → Pareto/weighted options | After extensions · Arnav+Ben · R03/R07 | No unsupported composite. Roadmap. |
| F022 Species suitability | Species/site evidence → suitability | After B03/biology · Arnav · R01/R07 | No generic species advice. Roadmap. |
| F023 Weather-weighted solar | DNI/weather/geometry → incident energy change | After B04/input validation · Arnav · R02/R07 | Not building energy/bills. Roadmap. |
| F024 Citywide investment overview | Supported canopy/equity data → priority view | Post-core rights/data · Arnav+Alex · R01/R08 | Not citywide high-resolution simulation or permission. Roadmap. |

## P3 — Long-term roadmap

| ID / feature | Inputs → outputs | Dependencies · owner · R | Acceptance/limit · status |
|---|---|---|---|
| F025 Citywide high-res simulation | City geometry/compute → bounded results | Post-hackathon · Arnav+Ben · R01/R02 | Validate scale/convergence/coverage. Roadmap. |
| F026 Thermal comfort/ambient cooling | Radiation/weather/surface/atmosphere → measures | New model · Arnav · R02/R07 | Shade alone insufficient. Roadmap. |
| F027 Hydrology/runoff/flood | Rain/terrain/soil/drainage → outcomes | New model/data · Arnav · R01/R07 | Local validation; river vs surface-water; no guaranteed protection/savings. Roadmap. |
| F028 Building energy/bills | Building/occupancy/weather/tariff → scenarios | New model · Arnav+Ben · R07/R08 | Incident energy insufficient. Roadmap. |
| F029 Air pollution/AQI | Emissions/weather/geometry/dispersion → pollutant measures | New model/data · Arnav · R07 | Tree count is not evidence. Roadmap. |
| F030 Ecology/biodiversity | Species/habitat/ecology → bounded evidence | Expertise/data · Arnav · R07 | No inferred benefit from planting count. Roadmap. |
| F031 Long-term economics/equity | Validated benefit/cost/distribution/policy → appraisal | F016+modules · team · R07/R08 | No unsupported monetary/equity claim. Roadmap. |
| F032 Survival/growth | Observations/species/site → scenarios | New biology/data · Arnav · R07 | Calibrate; not a guarantee. Roadmap. |
| F033 Multi-site ingestion | Rights-cleared sources/transforms → versioned bundles | F001/B03/governance · Ben+Arnav · R01/R08 | Per-source checks; no agent arbitrary fetch. Roadmap. |
| F034 Multiple cities | Regional data/policy/coordinates → validated workflows | F033/local validation · team · R01/R07 | No automatic transfer. Roadmap. |
| F035 Production hosting/auth/governance | Approved security/ops → reviewed service | Separate authorized programme · Ben+team · R08/R10 | Outside hackathon; explicit authority/security review. Roadmap. |

## Milestones, dependencies and work lanes

Milestones sequence B01–B12; BUILD remains the only task/decision status home. M0–M7 are gates, not task IDs/completion claims.

| Milestone | Scope and tasks | Exit |
|---|---|---|
| M0 Development readiness | Contracts/owners/setup/interfaces/event/data rights; B01/B03 and early B09 investigation | Actual setup/interface evidence; unknown gates explicit. |
| M1 Scientific foundation | Synthetic or audited geometry, solar ref, baseline/one tree; B02/B04 (B03 gates real claim) | Analytic reference plus repeatable difference, including zero. |
| M2 Vertical slice | API→calculation→UI, revision/stale protection; B01/B04/B05 | Edit cannot show old result as current; failure/zero/provisional shown. No optimiser/polished 3D/agent prerequisite. |
| M3 Basic optimisation | Candidates/constraints/validator/reference; B06 | Feasible proposal and honest comparison; no unsupported optimum. |
| M4 Local tool interaction | Begin when schema/runtime available; alongside M1/M2; B01/B09 then B10 | Real model selects registered tool, dispatches, observes result, explains; record device/version. Advanced sensitivity not prerequisite. |
| M5 Agentic replanning | Accepted edits recompute; B05/B06/B09/B10 | New identity, stale rejection, no relaxation. |
| M6 Competitive enhancements | Chosen P1 counterfactual/seasons/sensitivity/report; B07/B10/B12 | Each mapped V check passes; integration protected. |
| M7 P0 submission candidate | P0-scoped B08/B09/B12 evidence and actual entry gate | Peer-reproducible demo/claim ledger for scope shown. This scoped candidate does not mark B11/B12 fully Verified; full B12 retains B05–B11 and V12 acceptance. |

**Critical path:** B01→B02/B04→B05→B06→B10→B11/B12. B03 runs with synthetic work and gates real-site claims at B08. Start B09 early when runtime is available, not after all B07. Reserve final time for integration/evidence/recovery/pitch.

**Proposed lanes, pending acknowledgement:** Ben—backend/contracts/scenario/jobs/dispatcher/Nemotron/integration; Arnav—geospatial/solar/evaluator/search/science; Alex—spatial UI/controls/comparison/evidence/demo. Shared boundaries: Ben/Arnav result semantics; Arnav/Alex coordinates/render; Ben/Alex revision/async. One writer per shared file; coordinate contract changes and use isolated worktrees.

**Early agent proof:** B09 may prove one real registered operation against B01 before B10 completes. B10 adaptive investigation, permission, claims and no-progress acceptance remain required; readiness scaffolding is not a round-trip.

**Feature freeze:** determine only after deadline/rules verified. Then admit fixes, validation, evidence, recovery/demo work. Before freeze, optional features need ready dependencies, adequate method/data/rights, mapped V acceptance, and no threat to P0 integration/evidence.

## Claims, risks, unresolved decisions

After validation, claim only scoped direct geometric shade/shade-hours, supported constraints, assumed upfront costs, layout comparisons and measured performance. Direct irradiance needs aligned data/validation. Thermal comfort, temperature, interception, runoff/flood damage, air quality, carbon, biodiversity, energy/bills and long-term economics require distinct models/data. Sheffield is not universally on a floodplain; distinguish local river/surface-water risk. Trees do not guarantee flood protection/savings.

P0 is broad; M2 proceeds before F006/F008/polished 3D. No site passed rights/geometry; DGX/runtime/event eligibility unresolved; owners proposed; deadline/demo rules unknown. Confirm owners/contracts, site, runtime and event gates. Admit advanced claims only after independent modelling/validation.
