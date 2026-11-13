"""Explicit synthetic declarations registered through actual typed services."""

from datetime import datetime, timedelta, timezone

from tree_planner.contracts import Layout, ScenarioInput, SiteBundle, TreeProfile
from tree_planner.site.assets import PURPOSES
from tree_planner.site.service import catalogue_fingerprint, geometry_fingerprint
from .runtime import EVALUATOR, SOLAR, VERSION

DECLARATION = "Ben-owned generated synthetic reference inputs; no third-party or real site data"


def seed_reference(service, scene):
    rights = {purpose: "permitted" for purpose in PURPOSES}
    source = service.assets.register_source(
        source_reference=DECLARATION,
        licence_reference="Synthetic demonstration permission only; no external dataset licence asserted",
        evidence=[DECLARATION],
        rights=rights,
    )
    asset = service.assets.register_from_source(
        "synthetic-reference.json", source_id=source["source_id"], capture_date="unknown"
    )
    identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    site = SiteBundle.model_validate(
        dict(
            schema_version="0.1.0",
            site_id="synthetic-reference",
            scene_revision=1,
            semantic_revision=1,
            geometry_fingerprint="0" * 64,
            profile_library_revision=1,
            candidate_catalogue_revision=1,
            candidate_catalogue_fingerprint=catalogue_fingerprint(()),
            site_kind="synthetic_test",
            name="Explicit synthetic one-tree geometric reference",
            origin=dict(latitude_deg=0, longitude_deg=0, height_m=0),
            horizontal_crs="EPSG:4326",
            vertical_datum=dict(
                name="synthetic local up", status="assumed", evidence=[DECLARATION]
            ),
            analysis_frame="enu_m",
            source_units="m",
            metres_per_source_unit=1,
            source_true_north=[0, 1, 0],
            source_up_axis=[0, 0, 1],
            source_to_analysis=identity,
            analysis_to_viewer=identity,
            assets=[
                dict(
                    asset_id="synthetic-reference",
                    ref=dict(registry_id=asset["registry_id"]),
                    sha256=asset["sha256"],
                    kind="synthetic-explicit-input-declaration",
                    source_id=source["source_id"],
                    capture_date="unknown",
                    semantic_class="terrain",
                )
            ],
            targets=[
                dict(
                    target_id="synthetic-target",
                    geometry_ref="synthetic-reference",
                    area_basis="surface",
                    evidence_status="synthetic",
                    source_ids=[source["source_id"]],
                    assumption_ids=[DECLARATION],
                )
            ],
            planting_regions=[],
            exclusions=[],
            existing_trees=[],
            protected_surfaces=[],
            candidate_catalogue=[],
            rights=[
                dict(
                    source_id=source["source_id"],
                    source_reference=source["source_reference"],
                    licence_reference=source["licence_reference"],
                    required_attribution=DECLARATION,
                    evidence=source["evidence"],
                    **rights,
                )
            ],
            coverage=dict(
                study_extent_ref="synthetic-reference",
                context_extent_ref="synthetic-reference",
                missing_region_refs=[],
                horizon_limitations=[
                    "Chosen analytic sun direction, not SPA or geographic astronomy"
                ],
                boundary_limitations=["No SiteBundle geometry importer; explicit inputs only"],
            ),
            readiness=dict(
                blockers=[], warnings=[], optional_missing_inputs=[], survey_requirements=[]
            ),
        )
    )
    site = site.model_copy(update={"geometry_fingerprint": geometry_fingerprint(site.assets)})
    service.scenarios.register_site(site)
    service.scenarios.register_profile(
        TreeProfile.model_validate(
            dict(
                schema_version="0.1.0",
                profile_id="synthetic-tree",
                library_revision=1,
                species_size_label="synthetic opaque crown and trunk",
                source_ids=[source["source_id"]],
                assumption_ids=[DECLARATION],
                cost_pence=1234,
                cost_scope="synthetic upfront placeholder",
                price_date="2026-01-01",
                states={
                    "mature": dict(
                        horizon_years=20,
                        leaf_state="synthetic opaque",
                        crown_center_height_m=1,
                        crown_radii_m=[0.5, 0.5, 0.5],
                        trunk_radius_m=0.1,
                        trunk_height_m=2,
                        attenuation=dict(mode="opaque"),
                    )
                },
            )
        )
    )
    service.scenarios.register_layout(
        Layout.model_validate(
            dict(
                schema_version="0.1.0",
                layout_id="synthetic-one-tree",
                revision=1,
                kind="proposed",
                placements=[
                    dict(
                        placement_id="tree-1",
                        location_id="synthetic-location",
                        position_enu_m=[0, -1, 0],
                        profile_id="synthetic-tree",
                        candidate_id=None,
                        pinned=False,
                    )
                ],
            )
        )
    )
    scenario = service.create_accepted(
        ScenarioInput.model_validate(
            dict(
                schema_version="0.1.0",
                site_id=site.site_id,
                scene_revision=1,
                semantic_revision=1,
                profile_library_revision=1,
                candidate_catalogue_revision=1,
                candidate_catalogue_fingerprint=site.candidate_catalogue_fingerprint,
                display_time_zone="UTC",
                target_ids=["synthetic-target"],
                evaluation_cases=[
                    dict(
                        case_id="synthetic-bin",
                        role="benefit",
                        profile_state="mature",
                        horizon_years=20,
                        target_ids=["synthetic-target"],
                        time_bins=[
                            dict(midpoint_utc=scene.midpoint_utc, duration_h=scene.duration_h)
                        ],
                        target_weights={"synthetic-target": 1},
                        source_ids=[source["source_id"]],
                        assumption_ids=[DECLARATION],
                        area_basis="surface",
                    )
                ],
                constraints=dict(
                    budget_pence=10000,
                    budget_basis="upfront",
                    max_tree_count=None,
                    accepted_planting_region_ids=[],
                    excluded_region_ids=[],
                    pinned_placements=[],
                    spacing_rules=[],
                    incompatible_candidate_pairs=[],
                    allowed_profile_ids=["synthetic-tree"],
                    at_most_one_profile_per_location=True,
                    winter_limits=[],
                    survey_requirements=[],
                ),
                objective=dict(
                    kind="maximise_shade_under_budget",
                    primary_case_id="synthetic-bin",
                    quantity_kind="geometric",
                ),
                numerics=dict(
                    evaluator=EVALUATOR,
                    evaluator_version=VERSION,
                    spatial_spacing_m=1,
                    ray_offset_m=0.001,
                    intersection_tolerance_m=0,
                    feasibility_tolerance=0,
                    solar_algorithm=SOLAR,
                    solar_version=VERSION,
                    quadrature="midpoint",
                ),
                # Structurally required scenario field; no search provider is registered.
                search=dict(
                    algorithm="unsupported-no-search",
                    version="none",
                    seed=0,
                    comparison_policy="unsupported",
                    reference_policy="synthetic-inputs-only",
                    deadline_utc=(datetime.now(timezone.utc) + timedelta(hours=1))
                    .isoformat()
                    .replace("+00:00", "Z"),
                ),
                assumptions=[
                    DECLARATION,
                    "Sun direction analytically chosen: " + str(scene.sun_direction),
                    "Timestamp is an integration-bin label; no solar-position algorithm or SPA",
                    "Opaque geometry and synthetic represented surface area; no survey",
                    "Plantability, feasibility and constraints not evaluated",
                ],
                proposed_layout_ref=dict(layout_id="synthetic-one-tree", revision=1),
            )
        )
    )
    return site, scenario
