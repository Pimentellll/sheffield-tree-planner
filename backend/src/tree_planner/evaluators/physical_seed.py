"""Authored synthetic inputs only; all results come from the numerical producer."""

from datetime import datetime, timedelta, timezone

from tree_planner.contracts import Layout, ScenarioInput, SiteBundle, TreeProfile
from tree_planner.site.assets import PURPOSES
from tree_planner.site.service import catalogue_fingerprint, geometry_fingerprint

DECLARATION = (
    "Authored synthetic takeover-v1 scene; no surveyed Sheffield site or biological prediction"
)
IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]


def synthetic_scene():
    return {
        "format_version": "canopy-physical-scene/1",
        "spatial_spacing_m": 0.5,
        "flat_ground_z_m": 0,
        "samples": [
            dict(
                sample_id=f"s-{i}-{j}",
                position_enu_m=[i * 0.5, j * 0.5, 0],
                normal_enu=[0, 0, 1],
                area_m2=0.25,
                target_id="target",
                area_basis="surface",
            )
            for i in range(-6, 7)
            for j in range(0, 15)
        ],
        "triangles": [],
        "existing_trees": [],
        "regions": {"planting": [[-5, -5], [5, -5], [5, 5], [-5, 5]]},
    }


def seed_physical(service, *, winter=False):
    rights = {purpose: "permitted" for purpose in PURPOSES}
    source = service.assets.register_source(
        source_reference=DECLARATION,
        licence_reference="Authored synthetic test input permission; no external licence asserted",
        evidence=[DECLARATION],
        rights=rights,
    )
    asset = service.assets.register_from_source(
        "physical-scene.json", source_id=source["source_id"], capture_date="unknown"
    )
    assumption = dict(source_ids=[source["source_id"]], assumption_ids=[DECLARATION])
    candidates = [
        dict(
            candidate_id=f"candidate-{i}",
            location_id=f"location-{i}",
            position_enu_m=[x, 0, 0],
            profile_id="generic",
            plantability_status="provisional",
            **assumption,
        )
        for i, x in enumerate([0, -2, 2], 1)
    ]
    site = SiteBundle.model_validate(
        dict(
            schema_version="0.1.0",
            site_id="synthetic-physical-v1",
            scene_revision=1,
            semantic_revision=1,
            geometry_fingerprint="0" * 64,
            profile_library_revision=1,
            candidate_catalogue_revision=1,
            candidate_catalogue_fingerprint=catalogue_fingerprint(
                [
                    __import__(
                        "tree_planner.contracts", fromlist=["Candidate"]
                    ).Candidate.model_validate(c)
                    for c in candidates
                ]
            ),
            site_kind="synthetic_test",
            name="Synthetic numerical search and case harness",
            origin=dict(latitude_deg=53.38, longitude_deg=-1.47, height_m=0),
            horizontal_crs="EPSG:4326",
            vertical_datum=dict(
                name="synthetic local z=0", status="assumed", evidence=[DECLARATION]
            ),
            analysis_frame="enu_m",
            source_units="m",
            metres_per_source_unit=1,
            source_true_north=[0, 1, 0],
            source_up_axis=[0, 0, 1],
            source_to_analysis=IDENTITY,
            analysis_to_viewer=IDENTITY,
            assets=[
                dict(
                    asset_id="physical-scene",
                    ref=dict(registry_id=asset["registry_id"]),
                    sha256=asset["sha256"],
                    kind="canopy_physical_scene_v1",
                    source_id=source["source_id"],
                    capture_date="unknown",
                    semantic_class="terrain",
                )
            ],
            targets=[
                dict(
                    target_id="target",
                    geometry_ref="receiver",
                    area_basis="surface",
                    evidence_status="authored synthetic",
                    **assumption,
                )
            ],
            planting_regions=[
                dict(
                    feature_id="planting",
                    geometry_ref="planting",
                    evidence_status="synthetic provisional",
                    **assumption,
                )
            ],
            exclusions=[],
            existing_trees=[],
            protected_surfaces=[],
            candidate_catalogue=candidates,
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
                study_extent_ref="study",
                context_extent_ref="context",
                missing_region_refs=[],
                horizon_limitations=["Explicit synthetic scene without distant context"],
                boundary_limitations=["No surveyed site or environmental benefit prediction"],
            ),
            readiness=dict(
                blockers=[],
                warnings=[],
                optional_missing_inputs=[],
                survey_requirements=["Professional site/utility/soil/rights survey required"],
            ),
        )
    )
    site = site.model_copy(update={"geometry_fingerprint": geometry_fingerprint(site.assets)})
    service.scenarios.register_site(site)
    mature = dict(
        horizon_years=20,
        leaf_state="assumed opaque leaf-on",
        crown_center_height_m=4,
        crown_radii_m=[2, 2, 2.5],
        trunk_radius_m=0.15,
        trunk_height_m=2,
        attenuation=dict(mode="opaque"),
    )
    states = {
        "mature": mature,
        "establishment": {
            **mature,
            "horizon_years": 1,
            "crown_center_height_m": 1.5,
            "crown_radii_m": [0.5, 0.5, 0.5],
        },
    }
    if winter:
        states["leaf_off"] = {
            **mature,
            "leaf_state": "assumed leaf-off transmission",
            "attenuation": dict(mode="fixed_crossing", transmission=0.7),
        }
    service.scenarios.register_profile(
        TreeProfile.model_validate(
            dict(
                schema_version="0.1.0",
                profile_id="generic",
                library_revision=1,
                species_size_label="Hypothetical generic geometry; assumed sizes and costs",
                cost_pence=10000,
                cost_scope="Assumed upfront test cost",
                price_date="2026-11-13",
                states=states,
                **assumption,
            )
        )
    )
    layout = Layout.model_validate(
        dict(
            schema_version="0.1.0",
            layout_id="one-tree",
            revision=1,
            kind="proposed",
            placements=[
                dict(
                    placement_id="tree-1",
                    location_id="location-1",
                    position_enu_m=[0, 0, 0],
                    profile_id="generic",
                    candidate_id="candidate-1",
                    pinned=False,
                )
            ],
        )
    )
    service.scenarios.register_layout(layout)

    def case(case_id, role, state, year, midpoint):
        return dict(
            case_id=case_id,
            role=role,
            profile_state=state,
            horizon_years=year,
            target_ids=["target"],
            time_bins=[dict(midpoint_utc=midpoint, duration_h=1)],
            target_weights={"target": 2},
            area_basis="surface",
            **assumption,
        )

    cases = [
        case("summer", "benefit", "mature", 20, "2026-07-01T12:00:00Z"),
        case("establishment", "establishment_report", "establishment", 1, "2026-07-01T12:00:00Z"),
    ]
    if winter:
        cases.append(case("winter", "winter_check", "leaf_off", 20, "2026-12-01T12:00:00Z"))
    inp = ScenarioInput.model_validate(
        dict(
            schema_version="0.1.0",
            site_id=site.site_id,
            scene_revision=1,
            semantic_revision=1,
            profile_library_revision=1,
            candidate_catalogue_revision=1,
            candidate_catalogue_fingerprint=site.candidate_catalogue_fingerprint,
            display_time_zone="Europe/London",
            target_ids=["target"],
            evaluation_cases=cases,
            constraints=dict(
                budget_pence=20000,
                budget_basis="upfront",
                max_tree_count=2,
                accepted_planting_region_ids=["planting"],
                excluded_region_ids=[],
                pinned_placements=[],
                spacing_rules=[
                    dict(
                        minimum_centre_separation_m=2,
                        clearance_state="mature",
                        model_basis="Synthetic centre distance policy",
                        evidence=[DECLARATION],
                    )
                ],
                incompatible_candidate_pairs=[],
                allowed_profile_ids=["generic"],
                at_most_one_profile_per_location=True,
                winter_limits=[dict(case_id="winter", target_id=None, maximum_loss_m2_h=100)]
                if winter
                else [],
                survey_requirements=["Professional site/utility/soil/rights survey required"],
            ),
            objective=dict(
                kind="maximise_shade_under_budget",
                primary_case_id="summer",
                quantity_kind="geometric",
            ),
            numerics=dict(
                evaluator="canopy-cpu-reference",
                evaluator_version="takeover-v1",
                spatial_spacing_m=0.5,
                ray_offset_m=0.000001,
                intersection_tolerance_m=0.00000001,
                feasibility_tolerance=0,
                solar_algorithm="pvlib-spa-geometric",
                solar_version="0.15.2",
                quadrature="midpoint",
            ),
            search=dict(
                algorithm="overlap-greedy-local",
                version="takeover-v1",
                seed=0,
                comparison_policy="same-constraints-actual-spend-count",
                reference_policy="deterministic-reference",
                deadline_utc=(datetime.now(timezone.utc) + timedelta(hours=1))
                .isoformat()
                .replace("+00:00", "Z"),
            ),
            assumptions=[
                DECLARATION,
                "Synthetic scene located at a declared latitude for actual SPA; no real-site geometry",
                "Crown geometry, transmission and costs are illustrative assumptions",
            ],
            proposed_layout_ref=dict(layout_id=layout.layout_id, revision=1),
        )
    )
    scenario = service.create_accepted(inp)
    return site, scenario
