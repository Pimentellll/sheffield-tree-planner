# Validation, runtime evidence and demonstration

**State:** acceptance/test specifications, not tests already implemented or passed. The earlier arithmetic checks verified illustrative calculations only. No application test suite, Spark benchmark or clean installation is claimed here.

Related: [Spec requirements](SPEC.md) · [Contract](CONTRACTS.md) · [Numerics](NUMERICS.md) · [Tasks](BUILD.md).

## 1. Traceability and acceptance

Each verification ID names observable proof. Record actual commands/output, revision, inputs, environment, reviewer and limitations in its BUILD task. No command below is claimed to exist unless later marked verified in the runbook.

### V01 — schema, units and references

**Requirements:** R01/R02/R06/R08. **Tasks:** B01.

Accept a correctly labelled synthetic bundle/scenario through real serialization. Reject unsupported schema, unknown/wrong-type fields, NaN/Infinity, negative radii/time/area/cost, absent profile state, malformed UTC, unresolved revisions, overlapping target sets and invalid asset paths. Test idempotency: same request/payload reuses work; same ID/different payload conflicts. Generated frontend/API types must match the backend source.

### V02 — analytic and solar reference

**Requirements:** R02. **Tasks:** B02/B04/B06/B07/B08, full implemented-core regression at B12.

- ENU cardinal directions: south sun gives northward shadow. Known metre-scale point and normal round-trip through import/view transforms.
- Flat-ground pole reference: height H at elevation α gives H/tan(α), with correct direction. Include horizon/night handling, empty scene, simple wall and back-facing surface.
- Ellipsoid miss/hit/tangent and ray-origin-inside cases; trunk occlusion; self-intersection offset; near-grazing stability.
- Existing shading cannot produce additional tree benefit; new opaque masks combine as a union. For the documented synthetic overlapping-cell case, additional shade is 16 m²·h, not independently summed overlap.
- Attenuation example uses assumed coefficients: 0.8 × 0.5 × 0.25 gives transmission 0.1, additional blocking 0.7. Test the implemented evaluator, not only this arithmetic.
- UTC/local conversion and daylight-saving ambiguity; surface versus planimetric area; distinct interval durations and no double-counting of overlapping time bins.
- Compare solar positions against a separately sourced reference or trusted known dataset at documented instants. A second call to the same function is not independent verification.

**Phased applicability:** B02 verifies directions/transforms, solar/time references, analytic single-occluder intersections and input/finite rules. B04 verifies implemented opaque single-tree baseline/difference/zero cases. B06 adds multiple proposed trees and overlap/union correctness, including the 16 m²·h case. B07 adds fixed-crossing attenuation and the 0.1-transmission/0.7-additional-blocking case. Path-length-specific checks apply only if that optional mode is implemented. B12 reruns all implemented core subsets; an earlier slice does not fail because a later mode is deliberately unsupported.

Analytic floating-point comparisons should use tight declared tolerances suited to the formula and scale. Sampled scene totals need measured convergence criteria, not an arbitrary claim of exactness. Set tolerances with a numerical justification and retain actual residuals.

### V03 — real-site readiness and rights

**Requirements:** R01/R07/R08. **Tasks:** B03/B08.

Record real asset hashes, CRS/origin/north/units, dates, semantic separation, context extent, tree evidence and permissible use/sharing/display/export. Unknown scale/north blocks physics. Unknown utilities remains survey-required. Test that forbidden/unknown export permissions block affected output. Demonstrate that a baked existing canopy is not counted twice and leaf-on geometry is not falsely converted to winter state. Dataset availability is not a rights or validity pass.

### V04 — metric and constraint correctness

**Requirements:** R02/R03/R07. **Tasks:** B04/B06.

Verify identical baseline/proposal sampling, correct m²·h integration, unweighted versus weighted output and case/horizon labels. Show valid zero gain and diminishing marginal gain from overlap. Independently recheck all selected layouts for budget, count, exclusions, profile choice, spacing, pins and winter loss. Include a deliberately invalid candidate that search proposes and final validation rejects. Unknown survey conditions cannot appear as passed clearance.

### V05 — job and UI identity

**Requirements:** R06/R08/R10. **Tasks:** B01/B05, extended operations at B07/B10, full regression at B12.

Exercise queued/running/complete/failed/cancelled, deadline failure and restart-interrupted jobs. Start run A, edit to revision B, then let A finish; it may enter history but cannot overwrite B. Also start two jobs for the **same revision and slot**, finish them out of order, and prove only the later accepted selection can be current. An idempotent retry must not retake that selection; independent slots must not overwrite each other. A cached delivery must correctly bind the new requesting job to the original immutable run/source job without rewriting provenance. Test an unsubmitted draft, rejected edit, cancellation race, duplicate request and unknown revision. A hypothetical revision cannot become active merely by running it; human acceptance produces a new accepted revision. Ensure cached, recorded and fixture provenance survives UI rendering. Capture real response fixtures from implementation rather than hand-writing happy-path numbers.

**Phased applicability:** B01 tests schema/revision/idempotency/selection rules with controlled unit jobs; these are tests, not claimed live numerical results. B04/B05 exercise the implemented evaluation slot, real run delivery/cache, manual draft, late-result and failure paths. B07/B10 add the real comparison/search-slot and hypothetical-promotion paths as those operations exist. B12 runs the complete implemented matrix.

### V06 — search and unsuccessful outcomes

**Requirements:** R03. **Tasks:** B06.

Use tiny finite instances with exhaustive reference results to expose search/constraint defects. Compare against a competent deterministic reference using identical profiles, cases and hard limits. Show actual spend/count: same cap does not imply same spend. Cover empty-feasible, no eligible candidates, target miss, timeout and proven finite-model infeasibility only when proof exists. Check deterministic seed/order handling and tie-breaking. A greedy candidate may lose to the exact reference; report it honestly rather than relabel it optimal.

### V07 — comparison, sensitivity and cache validity

**Requirements:** R02/R05/R07/R08. **Tasks:** B07/B08.

For controlled relocation, assert all other placements, profiles, cases and constraints are unchanged. A redesign may change multiple positions, and must say so. An infeasible alternative returns a labelled comparison diagnostic, never a feasible recommendation; metrics/deltas identify their exact scenario and metric-instance IDs. Compare establishment/target and leaf cases without merging horizons. Vary spatial spacing, time resolution and context extent independently; report metric/ranking changes. Change crown, time, geometry or sampling and prove incompatible masks are rejected. A budget-only edit may reuse matching geometry masks but not a full old optimisation result. Evaluate missing off-site shading at low sun and retain limitations.

### V08 — actual local inference and hardware

**Requirements:** R04/R09. **Tasks:** B09.

Record model checkpoint revision, quantisation, parser, serving/runtime version, machine/device and one literal model-selected domain tool → real dispatch → observation. Measure cold start, warm turn/tool latency and memory with co-resident physics. Record physics device separately. Test model unavailability and malformed tool arguments. GPU/RT-core/acceleration claims require actual evidence for that path and an equivalent CPU workload; documentation of hardware features alone is insufficient.

### V09 — agent correctness and permissions

**Requirements:** R04/R05/R07/R08. **Tasks:** B10.

Test ordinary brief, ambiguous hard/soft requirement, one-tree relocation, accepted exclusion/redesign, reduced budget with protected priority, fragile ranking, unsupported household savings, missing north, missing optional weather, tool failure and irrelevant injected instructions in imported text. Require the correct tool/action, unchanged unapproved hard constraints, exact result-backed numbers and honest inability when appropriate. Repeated identical no-progress actions should terminate with a reason, not an invented answer. Attempt to manufacture an approval flag and prove backend refusal.

### V10 — usable spatial workflow

**Requirements:** R05/R06/R07/R08. **Tasks:** B05.

Verify known point/north/scale/crown dimensions visually and numerically. Test manual controls, keyboard/form alternatives, readable units, colour-independent labels, per-zone metrics, source/assumption panels and analysis-versus-view-only time controls. Inspect all empty, zero-benefit, stale, provisional, failed and cancelled states. A screenshot alone is not end-to-end proof; pair it with the actual run identity.

**Phased applicability:** B05 needs one target and one opaque tree, transform proof, manual evaluation, units, draft/stale/job-failure/cancel/zero/provisional/mode labels and accessible equivalents. B06/B07 add reference/search outcomes, per-zone/growth/winter/comparison panels with Alex; B10 adds agent investigations. B12 checks the full implemented interface. Later panels are not prerequisites for the first vertical slice.

### V11 — agent value, not agent theatre

**Requirements:** R04/R05. **Tasks:** B11.

Prepare held-out tasks before inspecting comparative results. Use the same validated tools, mandatory checks, input data and acceptance requirements for a competent manual UI, fixed workflow and adaptive agent. Include easy routine tasks where a fixed flow should do well and unfamiliar challenges requiring different investigations.

Measure: correct feasible completion; interpreted-constraint accuracy; unsupported claims; human corrections/actions; useful additional analyses; tool errors; full elapsed time including manual interactions. Record model/configuration and all failed runs. Report observed results, not a hand-assigned intelligence score or invented confidence percentage. If the agent is slower or less reliable without useful benefit, narrow the product claim.

### V12 — clean run, export and recovery

**Requirements:** R08/R09/R10. **Tasks:** B12.

A different teammate follows verified install/start/smoke instructions from a clean environment using pinned dependencies and permissible inputs. Complete the demo, export only allowed assets/fields, verify coordinate round-trip and reopen the proposal with its provenance. Recover from unavailable model, failed worker and late/cancelled job using honest labels. Exercise known-good restore without deleting unrelated work. Never equate a local build with hosted CI, deployment or submission.

## 2. Requirement coverage map

- R01 → V01/V03
- R02 → V01/V02/V04/V07
- R03 → V04/V06
- R04 → V08/V09/V11
- R05 → V07/V09/V10/V11
- R06 → V01/V05/V10
- R07 → V03/V04/V07/V09/V10
- R08 → V01/V03/V05/V07/V09/V10/V12
- R09 → V08/V12
- R10 → V05/V12

Core release blocks on failed hard constraints, unsupported numerical claims, stale identity or unproven mandatory local runtime. Performance improvement is measured rather than prescribed as an invented threshold. Record product latency targets after the first real benchmark and user workflow check.

## 3. Runbook — deliberately not fabricated commands

**Current state: not executable yet.** B01 supplies tested portable commands; B09 supplies tested Spark commands; B12 verifies them independently. Replace each missing entry with the actual command/configuration and observed output, not a plausible template presented as already working.

Required entries:

- Supported OS/architecture, Python/Node versions and lockfile revision.
- Clean environment/dependency installation; tested backend/frontend startup; configured ports and allowed network binding.
- Site import and schema verification; exact input/asset manifest and rights.
- CPU numerical smoke and one-tree end-to-end smoke.
- Model download/access requirements, checkpoint/quantisation/parser and server startup; no credentials in documentation.
- Local tool smoke; full demo invocation/manual interaction path.
- Test commands with recorded results; equivalent CPU/GPU benchmark if claimed.
- Shutdown/cancel, interrupted-job recovery, known-good code/data/model restore and cache compatibility checks.

No product container image, inference endpoint, package version or shell command is “verified” until that exact path ran. Avoid unnecessary deployment infrastructure; a local application is the core delivery target.

## 4. Demonstration script

The map/decision is the main surface, not the chat transcript:

1. Explain the site manager's budget/target decision and show provenance/readiness.
2. Show existing conditions, one real evaluated proposal and establishment/target assumptions.
3. Compare reference versus best evaluated layout with actual costs, counts, shade and winter effects.
4. Challenge one tree's position. Show the controlled computation, not a plausible story.
5. Accept an exclusion/budget change and let the agent choose redesign. Old values become stale immediately.
6. Inspect a justified sensitivity case; show stability or reversal exactly as calculated.
7. Open action/result/device evidence, then a permissible survey proposal with limitations.

Do not promise a dramatic numerical improvement or reversal before measuring it. An honest target miss can demonstrate correct behaviour. Confirm the actual demo-duration/submission limits rather than treating the event closing time as the cutoff.

## 5. Claim and evidence record

Record each pitch claim alongside its verified BUILD item: claim ID/text; `calculated`, `modelled scenario`, `measurement` or `proposal`; source/input/run/code identity; value/unit; environment; assumptions; limitations; reviewer; permission to use in demo. Documentary proof is not numerical validation, and a local run is not field validation.

Examples of **claim boundaries**, not results:

- Direct shade gain → may be claimed only for its evaluated target/time/horizon and run.
- Geometric or DNI-weighted solar change → not ambient cooling or purchased energy saved.
- Local model → actual device/tool trace required.
- Faster solver → equivalent workload/precision and measured end-to-end comparison required.
- Real Sheffield scene → actual site provenance/geometry proof required; synthetic fixtures stay labelled synthetic.
- Prior week's development precedent → user-reported history, not organiser permission for this entry.

## 6. Recovery decisions

If the model fails, manual numerical operation remains available but the live-agent demonstration is incomplete. If acceleration fails, use the validated CPU path and remove acceleration claims. If live computation fails, an exact-input cached result or recorded run may be shown with that label and original provenance; never change the badge to live. If the real site fails its rights/geometry gate, use a different audited site or honestly present a synthetic engineering demonstration without calling it a Sheffield reconstruction. The team decides whether remaining proof satisfies event rules before submission.
