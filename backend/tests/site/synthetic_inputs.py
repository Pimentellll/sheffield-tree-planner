"""Synthetic-only contract inputs for persistence tests."""

IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
SHA = "0" * 64


def site_data():
    return dict(
        schema_version="0.1.0",
        site_id="synthetic",
        scene_revision=1,
        semantic_revision=1,
        geometry_fingerprint=SHA,
        profile_library_revision=1,
        candidate_catalogue_revision=1,
        candidate_catalogue_fingerprint=SHA,
        site_kind="synthetic_test",
        name="Synthetic contract test scene",
        origin=dict(latitude_deg=53.3, longitude_deg=-1.4, height_m=0),
        horizontal_crs="EPSG:27700",
        vertical_datum=dict(name="unknown", status="unknown", evidence=[]),
        analysis_frame="enu_m",
        source_units="m",
        metres_per_source_unit=1,
        source_true_north=[0, 1, 0],
        source_up_axis=[0, 0, 1],
        source_to_analysis=IDENTITY,
        analysis_to_viewer=IDENTITY,
        assets=[
            dict(
                asset_id="mesh",
                ref={"registry_id": "mesh"},
                sha256=SHA,
                kind="synthetic mesh",
                source_id="synthetic-source",
                capture_date="unknown",
                semantic_class="terrain",
            )
        ],
        targets=[
            dict(
                target_id="target",
                geometry_ref="mesh",
                area_basis="surface",
                evidence_status="synthetic assumption",
                source_ids=[],
                assumption_ids=["synthetic"],
            )
        ],
        planting_regions=[],
        exclusions=[],
        existing_trees=[],
        protected_surfaces=[],
        candidate_catalogue=[],
        rights=[
            dict(
                source_id="synthetic-source",
                source_reference="synthetic test authorship",
                licence_reference="unknown",
                required_attribution="Synthetic input only",
                local_use_status="unknown",
                team_share_status="unknown",
                public_display_status="unknown",
                export_status="unknown",
                evidence=[],
            )
        ],
        coverage=dict(
            study_extent_ref="mesh",
            context_extent_ref="mesh",
            missing_region_refs=[],
            horizon_limitations=["synthetic test only"],
            boundary_limitations=[],
        ),
        readiness=dict(
            blockers=[], warnings=[], optional_missing_inputs=[], survey_requirements=[]
        ),
    )


def state():
    return dict(
        horizon_years=20,
        leaf_state="synthetic leaf-on assumption",
        crown_center_height_m=4,
        crown_radii_m=[2, 2, 3],
        trunk_radius_m=0.2,
        trunk_height_m=3,
        attenuation={"mode": "opaque"},
    )


def placement():
    return dict(
        placement_id="synthetic-p1",
        location_id="synthetic-l1",
        position_enu_m=[0, 0, 0],
        profile_id="synthetic-profile",
        candidate_id=None,
        pinned=False,
    )


def input_data():
    return dict(
        schema_version="0.1.0",
        site_id="synthetic",
        scene_revision=1,
        semantic_revision=1,
        profile_library_revision=1,
        candidate_catalogue_revision=1,
        candidate_catalogue_fingerprint=SHA,
        display_time_zone="Europe/London",
        target_ids=["target"],
        evaluation_cases=[
            dict(
                case_id="summer",
                role="benefit",
                profile_state="mature",
                horizon_years=20,
                target_ids=["target"],
                time_bins=[dict(midpoint_utc="2026-07-01T12:00:00Z", duration_h=1)],
                target_weights={"target": 1},
                source_ids=[],
                assumption_ids=["synthetic"],
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
            allowed_profile_ids=["synthetic-profile"],
            at_most_one_profile_per_location=True,
            winter_limits=[],
            survey_requirements=["synthetic survey required"],
        ),
        objective=dict(
            kind="maximise_shade_under_budget", primary_case_id="summer", quantity_kind="geometric"
        ),
        numerics=dict(
            evaluator="synthetic-test",
            evaluator_version="unit",
            spatial_spacing_m=1,
            ray_offset_m=0.001,
            intersection_tolerance_m=0,
            feasibility_tolerance=0,
            solar_algorithm="synthetic-test",
            solar_version="unit",
            quadrature="midpoint",
        ),
        search=dict(
            algorithm="synthetic-test",
            version="unit",
            seed=0,
            comparison_policy="synthetic test policy",
            reference_policy="synthetic test reference",
            deadline_utc="2026-11-12T14:00:00Z",
        ),
        assumptions=["synthetic"],
        proposed_layout_ref=dict(layout_id="synthetic-layout", revision=1),
    )


def profile_data():
    return dict(
        schema_version="0.1.0",
        profile_id="synthetic-profile",
        library_revision=1,
        species_size_label="hypothetical generic",
        source_ids=[],
        assumption_ids=["synthetic"],
        cost_pence=10000,
        cost_scope="synthetic estimate",
        price_date="2026-11-12",
        states={"mature": state()},
    )
