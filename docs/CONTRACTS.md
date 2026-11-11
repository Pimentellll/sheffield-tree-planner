# Shared contracts — baseline 0.1

**Status:** proposed implementation contract, not an existing API or captured runtime output.  
**Coordinator proposed:** Ben; Arnav reviews numerical meaning; Alex reviews consumption and interaction.  
**Links:** [Specification](SPEC.md) · [Numerics](NUMERICS.md) · [Validation](VALIDATION.md).

This file owns meaning until B01 creates backend schemas and generated OpenAPI/frontend types. At that point the generated schema owns serialization; retain semantic rules here and update both in the same change. No handwritten JSON in this document is a claimed simulation result.

## 1. Cross-cutting rules

- `schema_version` is the string `0.1.0` on top-level persisted/domain objects. IDs are nonempty opaque strings, not filenames. Revisions are positive integers assigned by the owning backend; published revisions are immutable.
- Reject unknown fields, wrong types, non-finite numbers, unsupported enum values and unresolved references. Do not silently turn strings into numbers or metres into degrees. Empty arrays must have a documented meaning.
- Internal geometry is right-handed local east/north/up **metres**. `Vec3` is exactly three finite numbers. Viewer coordinates are derived through an explicit invertible 4×4 row-major matrix; column-vector convention, homogeneous last coordinate 1.
- UTC timestamps are ISO 8601 strings ending in `Z`. Store `display_time_zone`, initially `Europe/London`, separately. Resolve/reject ambiguous or nonexistent local times before conversion.
- Core currency is `GBP`; costs/budgets are nonnegative **integer pence**. Initial constraint basis is `upfront`. Lifecycle cost is not silently approximated: reject that basis until its complete horizon/price-year/discount rules are implemented and tested.
- API unit tokens: `m`, `m2`, `h`, `m2_h`, `weighted_m2_h`, `kWh`, `kWh_per_m2`, `GBP_pence`. UI renders human-readable equivalents. Weighted utility is never labelled physical extra shaded area.
- `null` is permitted only where explicitly stated. Missing weather disables weather-dependent metrics; it never becomes zero irradiance. Zero shade gain is a valid computed value, not missing data.
- Asset references are registry IDs or paths relative to an approved site-bundle root. Reject traversal, absolute paths, symlink escape and external URLs; the product agent never chooses arbitrary files or network locations.

## 2. SiteBundle

Required fields:

- `site_id`, `scene_revision`, `semantic_revision`, `geometry_fingerprint`, `profile_library_revision`, `candidate_catalogue_revision`, `candidate_catalogue_fingerprint`.
- `site_kind`: `real_site` or `synthetic_test`; `name`; `origin` with `latitude_deg`, `longitude_deg`, `height_m`; `horizontal_crs`; `vertical_datum` with explicit known/assumed status.
- `analysis_frame`: constant `enu_m`; `source_units`, `metres_per_source_unit`, `source_true_north`, `source_up_axis`, `source_to_analysis` and `analysis_to_viewer` matrices. The import step resolves these; unresolved scale/north blocks evaluation.
- `assets`: registry references plus content SHA-256, kind, source ID, capture date or explicit unknown, and semantic class. Building/terrain/vegetation roles must be distinguishable or declared limited.
- `targets`: unique `target_id`, geometry/surface reference, `area_basis` (`surface` or `planimetric`) and source/assumption status. Overlap within a scored target set is rejected in 0.1; later partitioning must preserve non-duplication.
- `planting_regions`, `exclusions`, `existing_trees`, `protected_surfaces`: identified semantic features with geometry references and evidence status. Empty lists mean none supplied, **not** independently surveyed absence.
- `candidate_catalogue`: immutable finite location/profile pairs resolved by `(site_id, candidate_catalogue_revision)` and verified against `candidate_catalogue_fingerprint`. Each has `candidate_id`, `location_id`, `position_enu_m`, `profile_id`, `plantability_status` (`documented_model_region`, `provisional`, `excluded`) and supporting source/assumption IDs. Alternatives at one location are mutually exclusive. Excluded/unknown-unmodelled positions cannot become candidates by inference. ScenarioInput names this exact revision/fingerprint; never resolve an omitted or unknown revision to “latest”. Catalogue content/revision participates in the full run key and relevant masks.
- `rights`: source ID, source URL/reference, licence name/reference, required attribution, `local_use_status`, `team_share_status`, `public_display_status`, `export_status`, each `permitted`, `restricted` or `unknown`, with evidence. Do not infer sharing rights from a downloadable endpoint.
- `coverage`: study extent, surrounding context extent, missing regions and horizon/boundary limitations.
- `readiness`: computed blockers, warnings, optional missing inputs and survey requirements. Runtime validators calculate readiness; client-supplied “ready” cannot bypass them.

An existing canopy represented in the mesh is not represented again by an independent blocking crown. Leaf-on geometry does not become leaf-off just because the evaluation date changes. Historical planting polygons are not future planting permission; School Localities are not school grounds. See [Sources](SOURCES.md).

## 3. Profiles and placements

`TreeProfile` requires `profile_id`, library revision, species/size label (generic is allowed when labelled hypothetical), source/assumption IDs, upfront `cost_pence`, cost scope/price date, and a `states` mapping.

Each named state requires `horizon_years`, `leaf_state`, `crown_center_height_m`, positive `crown_radii_m` (three ENU-axis radii), positive `trunk_radius_m`/`trunk_height_m`, and `attenuation`:

- `opaque`: transmission zero when intersected;
- `fixed_crossing`: finite `transmission` in [0,1];
- `path_length`: positive `extinction_per_m`, only when the implementation and coefficient basis are validated.

Start with opaque axis-aligned ellipsoids and an explicitly modelled trunk. B07 adds fixed-crossing attenuation for declared growth/leaf scenarios; reject that mode before its evaluator/tests exist. Path-length attenuation is a later optional extension and is rejected until separately implemented/validated. Parameters are scenarios unless independently measured/sourced. Every profile selected in an evaluation case must contain its named state and matching horizon; missing states are errors, not automatic mature-tree substitutions. Clearance/spacing rules specify which profile state they use.

`Placement` requires `placement_id`, `location_id`, `position_enu_m`, `profile_id`, nullable `candidate_id`, and `pinned` boolean. Position is trunk base; crown centre adds the state's centre height to base z. The backend validates terrain attachment and limits against imported site geometry. A manual position has no candidate ID but is still fully validated. Duplicate placements/IDs are rejected.

`Layout` requires `layout_id`, revision, kind (`existing`, `reference`, `proposed`, `hypothetical`) and proposed placements. The existing layout has an empty proposed-placement list; existing scene trees remain in SiteBundle. The model cannot delete existing trees by editing this list.

## 4. ScenarioInput and immutable Scenario

`ScenarioInput` requires exact site/scene/semantic/profile revisions, `candidate_catalogue_revision` and `candidate_catalogue_fingerprint`; `display_time_zone`; targets; `evaluation_cases`; constraints; objective; numerical/search configuration; assumptions; and one nullable proposed-layout reference. The backend creates a `Scenario` with `scenario_id`, `revision`, `created_at_utc`, `scope` (`accepted` or `hypothetical`), nullable `base_scenario_ref` and the immutable input snapshot. A `scenario_ref` is exactly `{scenario_id, revision, scope}`; mismatched scope is rejected, not trusted from the caller.

An unsaved UI draft has no analysis identity. `prepare_scenario` validates and persists a separate immutable `hypothetical` snapshot, returning its reference and change summary; it never activates it. Hypothetical evaluation/search/comparison is allowed only when `base_scenario_ref` names an accepted scenario and the requested analysis is within that accepted task's investigation scope. A new brief with no accepted base may be prepared but must be accepted by a human before analysis. Hypothetical results are visibly labelled and cannot replace an accepted scenario's evaluation/search selection. An accepted-base comparison may reference hypothetical alternatives in its own labelled comparison slot. Human acceptance creates a new accepted revision through the UI acceptance path, with provenance linking the hypothetical source; the model cannot promote it or manufacture an approval field. Backend dispatcher permissions, not a model-supplied flag, enforce this boundary.

An `evaluation_case` requires:

- `case_id`, role (`benefit`, `winter_check`, `establishment_report`, `sensitivity`), `profile_state`, `horizon_years` and target IDs;
- `time_bins`: sorted non-overlapping bins containing `midpoint_utc` and positive `duration_h`; midpoint quadrature in 0.1. Duration defines the represented interval, not elapsed time until the next sample;
- nonnegative target weights and provenance; `area_basis`; optional weather reference only for explicitly requested irradiance metrics.

The objective selects exactly one primary benefit case. Additional cases are separately reported/checks; do not silently sum seasons, horizons or representative days into an annual benefit. Compare layouts on identical case definitions. Unit-weight unweighted metrics are mandatory alongside any weighted objective.

`constraints` requires:

- `budget_pence`, `budget_basis=upfront`, nullable `max_tree_count`;
- accepted planting-region IDs, excluded-region IDs and pinned proposed placements;
- `spacing_rules` with minimum centre separation, clearance state and model/evidence basis; explicit incompatible candidate pairs where available;
- allowed profile IDs and at-most-one-profile-per-location rule;
- winter limits as `{case_id, target_id or null, maximum_loss_m2_h}` for supported winter cases;
- survey requirements, never represented as “passed” without evidence.

`objective` is `maximise_shade_under_budget` or `minimise_cost_for_target`. The second additionally requires positive `target_gain_m2_h` against the unweighted primary case and its quantity kind. Both retain the same hard constraints. A heuristic returns best evaluated candidates and does not certify global optimality/minimal cost.

`numerics` requires evaluator/version, positive spatial spacing in metres, positive ray offset in metres, declared intersection/feasibility tolerances, solar algorithm/version and quadrature. Record resolved values; never inherit undocumented browser slider defaults. `search` requires algorithm/version, integer seed, requested comparison/reference policy and operational deadline. Deadline expiry is a failed job with `DEADLINE_EXCEEDED`; user cancellation is cancelled. Neither creates a completed Result. Partial candidates may be stored as explicitly unvalidated diagnostics, excluded from final metrics/proposals.

## 5. Job identity, lifecycle and supersession

`Job` fields: `job_id`, `request_id`, operation, scenario ID/revision/scope, `input_fingerprint`, `view_slot`, `selection_seq`, status, nullable run ID, nullable `delivery`, nullable progress, created/started/finished UTC timestamps (last two nullable), nullable `error`, `cancel_requested`, and nullable `superseded_by_revision`.

Status transitions:

- `queued → running → completed | failed | cancelled`;
- `queued → cancelled | failed`;
- terminal states never silently reopen; retry creates a new job/request ID linked to its predecessor.

`progress` is null when unknown; otherwise completed/total work with a phase and unit. Do not invent a percent from elapsed time. A cancelled job's partial values may be retained as diagnostics, never promoted to a validated final result.

**Supersession is independent of execution status.** A newer accepted scenario marks an older job/result superseded. A running old job may complete into history, but cannot become the active result. This deliberately clarifies the earlier research draft's combined `superseded` status; see D04 in [Build](BUILD.md).

Selections are keyed by `(scenario_id, revision, scope, view_slot)`. Slots are backend-assigned: `evaluate_layout → evaluation`, `search_layouts → search`, and both comparison operations → `comparison`. On acceptance of a **new** asynchronous request, atomically increment that key's `selection_seq` and set its accepted job ID before work begins. A later accepted request for the same key supersedes the earlier selection even within one revision. An idempotent resubmission returns the existing job without changing the selection. Other slots remain independent; old runs remain inspectable history. Changing the active scenario invalidates prior accepted-scope selections for the main UI; hypothetical selections never become accepted ones implicitly.

On completion, `delivery` binds the requesting `job_id` and its selection identity to `run_id`, `source_job_id`, requested scenario ID/revision/scope, input fingerprint, execution mode and delivery time. A live delivery normally has the same source/requesting job; a cache hit points to the original immutable run/source job. UI eligibility checks the **requesting Job/delivery**, latest server selection and matching Result fingerprint/scope, not an equality between the old Result's source job ID and the new request. Poll the selection endpoint or equivalent backend-derived currentness; frontend request order is not the authority. A failed/cancelled newer request leaves its slot without a current completed result; do not silently reactivate the older one. During an unsubmitted edit, show draft/stale immediately; a rejected edit must not mutate the accepted server scenario.

Jobs survive as records, not immortal processes: on restart, an abandoned running job becomes failed with `WORKER_INTERRUPTED`; never return an unverified completed status. Cancellation is cooperative and acknowledged; a late callback cannot revive a terminal cancelled job.

Idempotency scope is operation + request ID + normalized payload. An identical resubmission returns the original job, not duplicate work. Same request ID/different payload is conflict. Automatic retries are only for explicitly transient failures; deterministic invalid input is not endlessly retried.

## 6. Result and analytical outcomes

`Result` requires `run_id`, schema version, source job ID, scenario ID/revision/scope, full `input_fingerprint`, input snapshot reference, operation/arguments, analytical outcome, layouts, metrics, comparison metadata, constraints, assumptions, limitations, source IDs and provenance. For comparisons, the primary scenario is the accepted base; alternative scenario references are explicit in arguments and each evaluated entry.

- `layouts`: exact evaluated layout IDs/placements, scenario reference, cost pence, tree count and model feasibility (`feasible`, `infeasible`, `not_evaluated`) with reasons. Comparison results identify baseline/reference/alternative explicitly; an infeasible diagnostic layout is never a selected recommendation.
- Each `Metric` has a result-unique `metric_instance_id`, registry `metric_id`, scenario reference, finite value, unit token, layout ID, case ID, nullable target ID (null means non-duplicating aggregate), horizon, weighting and `quantity_kind` (`geometric`, `blocking_equivalent`, `weighted_utility` or `direct_incident_energy`). Missing/unevaluated metrics are absent with an explicit reason, never invented zeros.
- Metric registry: `additional_shade` → unweighted `m2_h`; `weighted_shade_utility` → `weighted_m2_h`; `winter_sun_loss` → `m2_h`; optional `direct_incident_energy_change` → `kWh` or `kWh_per_m2` with surface/aggregation basis. Never display these as temperature, purchased energy or bills.
- Constraint records identify scenario/layout and applicable case, then state rule, limit, observed value/unit, `pass`, `fail` or `unknown`, and evidence. Known numerical hard constraints must pass before a candidate is marked model-feasible; survey unknowns remain explicit and provisional.
- Provenance contains tool/evaluator/search/solar/schema versions, seed, creation/compute timestamps, timings, separate physics/inference device details, source hashes and execution mode (`live`, `cached`, `recorded`, `fixture`). Use null for unavailable hardware/inference evidence; do not infer Spark from a filename.

Analytical outcomes:

- `comparison_completed`: a controlled comparison/sensitivity calculation or feasibility diagnostic completed with explicit per-layout status. This is not a feasible-plan claim. Known alternative constraint failures may be reported without failing the entire comparison; missing/incompatible inputs or corrupted calculation still fail validation. Comparison deltas identify base/alternative metric-instance IDs, units, mode and changed inputs; differing scenario inputs cannot be hidden behind repeated case/layout IDs.
- `feasible_candidate`: selected planting passes modelled hard constraints; target mode also meets the requested target.
- `feasible_zero_planting`: empty layout is permitted and returned, even if there are no eligible candidates; explain why.
- `no_eligible_candidates`: candidate catalogue is empty after restrictions and the requested task requires planting/positive gain. Does not imply no real-world planting opportunity exists.
- `search_exhausted_without_target`: the defined heuristic/exhaustive search completed normally without a target-meeting candidate. Never use for deadline expiry or user cancellation; those follow the failed/cancelled job rules and produce no completed Result.
- `proven_infeasible_finite_model`: only with recorded exhaustive/exact proof for the stated finite model, not a heuristic miss.

Malformed input fails validation before job acceptance where possible; discovered invalid geometry/inputs fail the job with a structured error. `completed` means the requested analysis produced a validated outcome, not necessarily a beneficial plan. An independently failed result validation is `failed`, never a feasible outcome with a warning banner.

## 7. Registered operations

Each request references immutable revisions; permissions and validation are backend-owned.

- `inspect_site(site_id, scene_revision)` → readiness, licence/use status, optional gaps and survey requirements. Read-only, no network retrieval.
- `prepare_scenario(base_scenario_ref or null, proposed_edits)` → immutable hypothetical scenario reference and change summary; no activation. Analysis eligibility and human acceptance follow section 4, not a model-generated approval flag.
- `evaluate_layout(scenario_ref, layout_ref)` → job/result for existing baseline and the exact proposed placement list.
- `search_layouts(scenario_ref)` → job/result for competent reference and best evaluated alternatives under accepted constraints.
- `compare_locations(scenario_ref, layout_ref, placement_id, alternative_position_enu_m)` → controlled counterfactual. Hold all other placements/profile choices and assumptions fixed; preserve the moved tree's identity; report constraint failure rather than covertly redesigning. The hypothetical comparison may inspect a pinned tree but cannot modify the accepted pin/layout without a separate human edit.
- `compare_scenarios(base_scenario_ref, alternative_scenario_ref, layout_refs, mode)` → `fixed_layout` or `redesign` comparison. Record exactly which inputs differ; refuse a “controlled” label if unrequested factors differ. Fixed-layout comparisons can include infeasibility diagnostics without claiming a feasible recommendation. No automatic preference relaxation.
- `prepare_proposal(result_refs)` → local proposal payload containing only validated results and permitted export fields. Cannot send, publish, buy or approve planting. Rights checks apply again at export time.

The first implemented subset is inspect/evaluate; later operations must return an explicit unsupported-operation error until implemented. Tool schemas come from the same backend models as the API. Lower-level solar/ray functions are not model-callable tools.

## 8. Proposed HTTP surface

Contract targets, not tested endpoints:

- `POST /api/v1/sites/import`: import a validated bundle through the approved asset registry; no raw host paths or arbitrary URLs. `GET /api/v1/sites/{site_id}` reads the exact requested revision.
- `POST /api/v1/scenarios`: validate a ScenarioInput and create revision 1.
- `PUT /api/v1/scenarios/{scenario_id}`: full replacement ScenarioInput with `If-Match` set to the quoted current revision; create the next revision or return conflict. Only the human-facing acceptance path can activate material changes.
- `GET /api/v1/scenarios/{scenario_id}?revision=...`: immutable snapshot.
- `GET /api/v1/scenarios/{scenario_id}/selections?revision=...`: mutable latest selection per scope/slot, including selection sequence and accepted job ID; separate from the immutable snapshot.
- `POST /api/v1/jobs`: `{request_id, scenario_ref, operation, arguments}` using the exact reference shape in section 4; accepted asynchronous work returns 202 + Job, never a fabricated result.
- `GET /api/v1/jobs/{job_id}`; `POST /api/v1/jobs/{job_id}/cancel`; `GET /api/v1/results/{run_id}`. Polling is sufficient initially; streaming is optional.
- Read-only site inspection, draft preparation and proposal preparation use corresponding domain handlers; B01 publishes their concrete routes only when added, without changing operation semantics.

Errors use `{code, message, retryable, field_errors, details}`; `details` must be safe for display. Required codes: `INVALID_INPUT`, `UNKNOWN_REVISION`, `REVISION_CONFLICT`, `RIGHTS_RESTRICTED`, `RIGHTS_UNKNOWN`, `SITE_NOT_READY`, `UNSUPPORTED_OPERATION`, `TOOL_UNAVAILABLE`, `NUMERICAL_FAILURE`, `RESULT_VALIDATION_FAILED`, `WORKER_INTERRUPTED`, `DEADLINE_EXCEEDED`, `CANCELLED`. Return 422 for invalid schema/domain input, 404 for unknown references, 409 for revision/idempotency conflict, and an appropriate 5xx for infrastructure failure. Never leak stack traces/secrets as user details.

## 9. Fingerprints, caching and export

The backend computes fingerprints, not independently implemented browser hashes. Persist the normalized complete input snapshot and referenced content hashes, then SHA-256 a deterministic canonical serialization with schema/evaluator version and operation arguments. B01 defines/tests its exact normalization; all callers use that implementation. No hashing of an ambiguous display string or mutable filename.

Two identities:

- **Full run key:** normalized scenario **including ID/revision/scope in 0.1**, relevant site/profile/catalogue content, exact layout/operation arguments, numerical/search versions and seed. Full-result reuse is restricted to that exact immutable scenario identity; cross-revision numerical reuse is limited to matching masks. A matching geometry key alone cannot reuse a full result after a budget/constraint/objective edit.
- **Geometry-mask key:** geometry/transform, semantics affecting occlusion, sample locations/normals/areas, UTC bins, candidate geometry/state/attenuation and numerical engine/settings. Budget/cost changes may reuse only these masks when the key matches; timestamps, crown changes or sampling edits invalidate them.

A cached retrieval preserves the original immutable run/provenance and records the new requesting Job/delivery link, time and `cached` mode defined in section 5; do not rewrite the original run as a new live compute. A recorded run is replay evidence; fixture mode is development-only. The UI displays these modes separately from device metadata.

UI and agent tools consume the delivery envelope **and** immutable Result together. Display/claim current execution mode from the delivery; retain the Result's original computation mode/device as provenance. A cache hit cannot look live merely because its source computation was live.

GeoJSON export uses geographic longitude/latitude order after a verified transform, never ENU metres masquerading as degrees. An alternative local-coordinate export must name its frame, origin, units and transform. Include rights/attribution, assumptions, costs, cases, run IDs, limitations and unresolved professional checks. Asset inclusion is allowlisted by rights; unknown/restricted sharing blocks that asset's export rather than being silently ignored.
