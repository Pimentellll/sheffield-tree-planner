# Numerical specification

**Baseline:** 0.1. **Maintainer proposed:** Arnav, with Ben reviewing implementation interfaces.  
[Contract](CONTRACTS.md) owns serialized fields/units; [Spec](SPEC.md) owns supported claims; [Build](BUILD.md) owns implementation state; [Validation](VALIDATION.md) owns acceptance cases. Source numbers refer to [Sources](SOURCES.md).

This retains the reviewed shading/search mathematics from the research baseline. It is a specification, not a validated solver. The worked arithmetic was checked during preparation; implementing and testing the evaluator remains B02/B04.

**First implementation:** opaque axis-aligned ellipsoids with an explicitly modelled trunk, CPU reference, one primary benefit case and upfront GBP-pence cost. B07 adds fixed-crossing transmission for declared growth/leaf scenarios and its V02/V07 checks. Path-length attenuation and lifecycle costing remain optional future extensions, rejected until separately implemented and validated. Additional cases extend the same model. Local analytic development does not depend on Spark access or a selected real site.

## Direct-solar shading model

The first model is **direct-solar visibility/transmission**, not local air temperature, comfort, household savings or full radiation balance. Use an established solar-position implementation such as pvlib's documented interface rather than inventing astronomy code; provide geographic position and timezone-aware timestamps.[7]

### 4.1 Coordinates and solar direction

Use right-handed local **east x, north y, up z**, in metres. Let α be solar elevation above the horizon and A azimuth clockwise from true north. Trigonometric inputs are radians internally. The direction from a surface toward the sun is:

```math
s(t) = (cos(α) sin(A), cos(α) cos(A), sin(α))
```

A sun due south has negative north component; its shadow extends northward. Store user-facing `Europe/London` time zone and unambiguous UTC instants. Explicitly reject or resolve nonexistent/repeated local times at daylight-saving transitions. Do not treat naive local times as UTC.

Each sample i has position p_i, outward unit normal n_i, represented physical area a_i, target membership and a declared priority weight. Use surface area when terrain slope matters; distinguish it from planimetric map area. Partition overlapping target polygons or define one non-duplicating membership rule.

Cast a ray from the surface toward the sun:

```math
r_i(λ) = p_i + ε n_i + λ s(t),   λ > 0
```

Use a scale-aware self-intersection offset and/or originating-triangle exclusion; do not let the offset jump through nearby thin geometry. Night does not count as useful newly created shade. Back-facing surfaces have no direct incident sunlight even without an obstruction, so do not count that as a tree benefit.

### 4.2 Crown geometry and attenuation

**Recommended first crown:** a parameterised ellipsoid above a trunk, independently represented from the visual foliage. An opaque crown is a geometric scenario, not a claim that real foliage blocks all sunlight. A fixed crossing-transmission scenario is a transparent next step; a path-length model is a later refinement if its coefficients are justified.

For an ellipsoid with centre c and radii r_x, r_y, r_z, let D be diagonal with entries 1/r_x², 1/r_y², 1/r_z². A point q is inside when `(q−c)ᵀD(q−c) ≤ 1`. Substituting a ray gives:

```math
a λ² + b λ + c0 = 0
 a  = sᵀ D s
 b  = 2 sᵀ D (p−c)
 c0 = (p−c)ᵀ D (p−c) − 1
```

Here p is the actual offset ray origin. If the discriminant is non-negative, use the positive segment between the roots; the crown path length is `max(0, λ_plus − max(λ_minus, 0))` for a unit ray. Tangency and numerical tolerances need tests. Triangle/BVH intersection handles the static site; an analytic crown avoids constructing a detailed leaf mesh for each candidate.

Let B_it be transmission through the existing scene and T_ijt transmission through candidate tree j at sample i and time t. Both lie between zero and one. Under the explicitly simplified independent-attenuation model:

```math
V_it(S) = B_it × product of T_ijt over selected trees j in S
D_it(S) = B_it − V_it(S)
```

An opaque existing obstruction gives B=0, so a new tree behind it adds no direct-beam blocking at that sample. Opaque candidate masks combine by union, not addition. Partial transmission combines multiplicatively under this model; intersecting/interacting crowns require care about whether that approximation remains appropriate.

A possible homogeneous path-length model is `T = exp(−κ L)`, with effective extinction κ in inverse metres and crown path length L in metres. Do not invent species-specific κ values. This does not resolve scattering, individual leaves or multi-bounce light.

### 4.3 Useful shade and winter loss

For daylight interval duration Δt in hours and a dimensionless non-negative priority w, define f_it=1 only for a sun-facing surface. Added direct-beam blocking is integrated as:

```math
F(S) = sum over i,t of a_i × Δt_t × w_it × f_it × D_it(S)
```

With opaque crowns and w=1, the result is **additional geometric shade, m²·h**, over the stated target and period. With partial transmission it is **direct-beam blocking-equivalent m²·h**, not binary fully shaded area. With priority weights, call it weighted utility and also report the unweighted physical result. A score must not masquerade as extra physical area.

Use midpoint samples or another declared quadrature rule. Selected representative summer days are not an annual climate estimate. State evaluation dates, hours, sample spacing and which surface is shaded: ground, seating or another defined exposure surface.

Compute protected winter loss with the same expression over the appropriate winter surfaces and periods, with separate priorities. It represents lost direct sunlight, not extra heating demand. Prefer an explicit winter limit to a hidden coefficient allowing unlimited harm to be compensated by summer shade.

### 4.4 Irradiance and direct energy

If direct normal irradiance DNI is available and aligned with the evaluated instants:

```math
ΔE_i = (1/1000) × sum over t of
        DNI_t × max(0, n_i · s_t) × D_it(S) × Δt_t
```

DNI is W/m²; this gives kWh/m² of changed direct incident energy. Multiply by a_i and sum to obtain kWh over the sampled surfaces. Do not substitute global horizontal irradiance into this DNI formula. Diffuse sky light, reflection, longwave radiation and weather variability need separate treatment.

**The distinction is non-negotiable:** blocked incident solar energy is not building energy saved. A thermal/building model, systems and occupancy assumptions must bridge that gap before any purchased-energy or bill estimate.

### 4.5 Worked checks—not Sheffield results

Synthetic arithmetic checks executed during preparation:

- An 8 m vertical obstruction at 45° elevation gives an 8 m flat-ground tip shadow; at 30°, approximately 13.86 m.
- Let proposed opaque shadows cover cells 0–5 and 4–9, while cells 0–1 are already shaded. Their union adds eight 1 m² cells. Over two hours that is **16 m²·h**, not the 20 obtained by separately adding both trees' apparent contributions.
- For assumed existing transmission 0.8 and new-crown transmissions 0.5 and 0.25, combined transmission is 0.1; added blocking is 0.7. Those are illustrative coefficients, not measured foliage properties.
- DNI 800 W/m², horizontal ground, 30° sun and transmission 0.5 give 200 W/m² of incident direct energy rate; two hours give 0.4 kWh/m². No weather observation or benefit claim is implied.

These verify arithmetic and unit conventions only. They are not a ray-tracing implementation, real-site validation or hardware benchmark.

## Optimisation, uncertainty and computation reuse

### Decision variables and constraints

Use a finite candidate library of **location/profile pairs**. Binary x_j selects candidate j. Alternatives at the same position are mutually exclusive. The catalogue is tied to site revision, profiles and assumptions.

Enforce:

- An explicitly chosen budget basis: upfront or lifecycle; never silently mix them.
- Tree-count limits if requested; permitted/provisional planting regions; exclusions; pinned choices.
- Pairwise spacing, access, root-space and crown-clearance conflicts, with the relevant age and clearance rule stated.
- At most one profile at a location; permitted species/profile rules where evidence supports them.
- Protected winter-sun thresholds and other user-approved hard requirements.

```math
sum_j cost_j × x_j ≤ budget
sum_j x_j ≤ maximum_tree_count
x_j + x_k ≤ 1  for each incompatible pair (j,k)
x_j ∈ {0,1}
```

Unknown utilities, ownership, soil and planting consent are **survey requirements**, not satisfied constraints. Call the result model-feasible/provisional, not construction-ready.

### Search policy

Start with deterministic marginal-benefit greedy selection followed by feasible add/remove/swap or relocation improvements. Generate a competent reproducible planting reference independently of the claimed winner. Use exact enumeration on tiny cases to check correctness; a more powerful solver is an upgrade when it improves measured results.

Overlapping shadows make benefit non-additive. Plain geometric coverage has useful diminishing-return structure, but spacing, costs, winter constraints and robust policies mean we cannot casually claim a general greedy optimality or approximation guarantee. Report **best evaluated layout**, search method and seed—not “globally optimal” without proof.

A common budget ceiling does not guarantee equal spend or tree count. Compare identical sites, profiles, dates, sample grids and constraints; show actual spend and count. If claiming equal cost or equal count, enforce that comparison. Report improvement over existing conditions separately from improvement over the competent planting baseline.

### Growth and robustness without misleading conservatism

Keep establishment/young, declared target-year and seasonal scenarios in the core contract. Do not give newly planted trees mature benefits. Leaf-off is not automatically transparent: branches and trunks remain.

Optimise a declared horizon and inspect uncertainty **within that horizon**. Show establishment performance separately; impose an early-benefit requirement only if the planner chooses one. Do not silently maximise the minimum across year 1 and year 20: that can collapse the decision into establishment-year shade and disguise the policy choice.

A max-min objective over a documented set of plausible same-horizon scenarios is an optional robust policy. It means best worst-case performance among those specified scenarios, not a probability guarantee or protection from every possible future. Show when layout rankings change across crown size, transmission, growth or survival scenarios. Unsupported probability distributions must not become confidence intervals.

Separate three uncertainties: numerical discretisation; uncertain input geometry/biology; and model inadequacy. Increasing ray count only addresses the first.

### Fast evaluation through reusable masks

For fixed scene, surface samples, timestamps and candidate profiles, precompute existing transmission B_it and candidate T_ijt. Search then combines masks rather than rebuilding/reraytracing the whole city for every layout. Opaque masks can use compact bitsets; partial transmission needs an appropriate numeric representation. This is exact for the stated discretised independent-attenuation model, not exact continuous physics.

Reuse requires compatible geometry/transform, sample locations/normals/areas, times, candidate positions/shapes/leaf state, attenuation model and numerical settings. A changed cost or budget may reuse geometric masks; a changed crown or evaluation time cannot reuse the wrong mask. New priorities can reuse masks only on the same spatial/time grid. Weather-only reweighting is possible when geometry/times stay fixed and the model remains direct-beam.

Illustrative storage calculation: 300 candidates × 5,000 samples × 24 times is 36 million entries—144 MB as float32 or 4.5 MB as packed binary, before metadata and additional scenarios. This is arithmetic, not a selected project scale or benchmark. Measure actual memory and runtime before choosing representations.

### Honest unsuccessful-search language

With only upper limits, the empty layout is normally feasible. “No trees can be added” is not automatically “the optimisation is infeasible.” Distinguish invalid inputs, no eligible candidates, no target-meeting layout found, cancelled work, solver failure and proven infeasibility of the exact finite model. A heuristic search failure cannot prove that no real-world planting arrangement exists.


## Implementation invariants

- Resolve all physical samples in ENU metres; carry position, outward unit normal, represented area and target membership together. Reject invalid/overlapping target definitions rather than duplicating area.
- Keep raw transmission masks separate from objective weighting and cost. Reuse requires the CONTRACTS geometry key; an unchanged mesh filename is insufficient.
- Independently validate the final selected layout. Search scoring must not be its own sole constraint validator.
- Compute and retain unweighted metrics even when optimisation uses priority weights. Report each declared horizon/case separately.
- Record discretisation and input sensitivity separately; extra rays cannot cure missing buildings, foliage assumptions or an inadequate physical model.
- Do not accept a real-site result until the required geometry/rights/readiness checks pass. Synthetic reference tests remain valid engineering evidence but are not Sheffield benefit evidence.
