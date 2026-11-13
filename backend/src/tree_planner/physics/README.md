# Deterministic CPU physics producer

Exploratory working contract `takeover-v1`; this is not human scientific acceptance.

`compute(dependencies, placements, stop=None, *, diagnostic=False)` returns separate
case and target totals: `physical_m2_h`, `weighted_m2_h`,
`baseline_direct_sun_m2_h`, `proposal_direct_sun_m2_h`, plus state/horizon/role,
quantity kind, scene/sampling/physics/candidate content identities and diagnostics.
Winter physical totals mean additional direct sunlight blocked relative to the
same winter baseline. Weighted totals are utility, never physical area.

Dependencies are already resolved JSON: `site` SiteBundle, `scenario` Scenario,
`profiles` mapping profile ID to TreeProfile, and `scene`. Public adapters remain
responsible for full domain validation, immutable asset binding, rights and jobs.
The producer revalidates numerical fields, states, revisions and placements.

Scene format is `format_version="canopy-physical-scene/1"`. Required fields:
`spatial_spacing_m`, explicit `flat_ground_z_m`, `samples`, `triangles`,
`existing_trees`. Samples contain `sample_id`, `position_enu_m`, `normal_enu`,
`area_m2`, `target_id`, `area_basis`; optional `origin_triangle_id` must actually
contain the receiver. Triangles contain `triangle_id`, `vertices_enu_m`.
Optional `regions` are import/search metadata. Non-null `terrain` is unsupported.
Optional `baked_vegetation` is null or an explicit object with
`supported_profile_states` and `existing_trees_separate=true`. Unknown state
coverage or possible duplicated existing canopy fails closed.

`build_masks(dependencies, candidates, stop=None)` returns real transmission
arrays, flattened sample-major/time-minor for each case. Baseline B includes
night/back-facing gating, static triangles and existing-tree transmission.
Candidate T arrays multiply. `physical_weights=area*duration`; target priorities
remain separate. Candidate masks accept alternatives at one location.
`validate_masks(dependencies, candidates, masks)` checks exact dependency and
content identities. `evaluate_masks(dependencies, candidates, masks,
selected_candidate_ids, stop=None)` verifies compatibility and combines masks
without solar/ray calls. Selected alternatives still cannot share a location.
Candidates must resolve in the supplied site's exact catalogue. Budget/cost-only
changes do not change geometry identities; source/state/grid/time/geometry
changes do. Hashes are compatibility checks, not authentication of untrusted data.

`diagnostic=True` permits only a known candidate's moved position; profile and
location identity still match. It retains IDs and records
`candidate_position_mismatch`. Only the comparison adapter may request this;
independent feasibility must mark the failed candidate constraint and never
publish that diagnostic as a feasible recommendation. Default evaluation and
search remain strict. Callbacks returning true raise `PhysicsStopped`; callback
exceptions propagate, and neither path returns partial successful output.

Numerical policies:

- `canopy-cpu-reference/takeover-v1`, `pvlib-spa-geometric/0.15.2`.
- Geometric SPA elevation uses explicit site altitude and the declared fixed
  delta-T assumption of 67 seconds. Apparent elevation is exposed only by the
  solar reference function, with explicit pressure/temperature parameters.
- Rays use positive interior ellipsoid/cylinder lengths. Exact tangencies do
  not attenuate; bare trunks remain opaque in every leaf state.
- Static triangles use dimensionless machine-scale tolerance. Origin-triangle
  exclusion avoids moving rays through nearby thin geometry. No physical ray
  offset is applied; the requested offset is retained in the identity. Declared
  metre tolerance is used for ground attachment, not as a dimensionless
  discriminant tolerance.
- CPU brute-force triangles, axis-aligned crowns, independent multiplicative
  fixed crossing and supplied receiver quadrature only. No path-length foliage,
  biology inference, weather/thermal/energy model, nonflat planting terrain,
  GPU acceleration, general mesh importer or real Sheffield evidence.

Provenance: solar ENU, DST and bin utilities preserve Arnav's PR37
`a80745d206482a631828cff09e54ae52a2dbb9db`. Geometry/shade equations build on PR43
`33493a327a99e5de2e579b5c3070ada137047c7e`; repairs replace fixed discriminant
thresholds and tangent blocking, add inside-path handling, explicit solar
conventions, multi-tree/state evaluation and immutable mask checks.
`source_manifest()` hashes actual local producer files and installed dependency
versions; it does not invent a revision or hardware claim.

Independent numerical reference: NREL TP-560-34302, Appendix A.5, pp. A-15/A-16,
https://www.nlr.gov/docs/fy08osti/34302.pdf . Matched published atmosphere and
altitude are essential when comparing the apparent zenith. Test tolerance
0.000005 degrees is the half-unit of the report's five-decimal rounding.
The pvlib SPA API documents both elevation conventions:
https://pvlib-python.readthedocs.io/en/stable/reference/generated/pvlib.solarposition.spa_python.html .

Tests under `backend/tests/physics` use labelled synthetic inputs, independently
computed analytic expectations, actual solar calls and measured refinement
residuals. Evidence logs live in the authorised local execution directory, not
as fabricated successful runtime fixtures. Continuous accuracy/field validation
is not implied by a finite sampled-scene test.
