"""Synthetic contract/reference tests, not a Sheffield site or solver receipt."""

import copy
import json

import pytest
from pydantic import ValidationError

from tree_planner.contracts import (
    AssetRef,
    ReferenceValidationError,
    SiteBundle,
    compute_readiness,
    validate_asset_path,
    validate_site_references,
)

IDENTITY = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
SHA = "a" * 64


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


def test_ingestion_preserves_unknown_and_recomputes_readiness():
    site = SiteBundle.model_validate_json(json.dumps(site_data()))
    assert site.vertical_datum.status == "unknown"
    assert site.rights[0].export_status == "unknown"
    assert compute_readiness(site).blockers
    assert "local_use_status" in " ".join(compute_readiness(site).blockers)
    assert compute_readiness(site, use="export_status").blockers


@pytest.mark.parametrize(
    "ref",
    [
        {"relative_path": "../x"},
        {"relative_path": "C:/x"},
        {"relative_path": "https://example.com/x"},
        {"relative_path": "/x"},
        {"relative_path": "a\\..\\x"},
        {"relative_path": "x:stream"},
        {"registry_id": "x", "relative_path": "x"},
        {},
    ],
)
def test_bad_asset_refs(ref):
    with pytest.raises(ValidationError):
        AssetRef.model_validate(ref)


def test_registry_and_real_path_resolution(tmp_path):
    (tmp_path / "mesh.bin").write_bytes(b"synthetic")
    assert validate_asset_path(AssetRef(relative_path="mesh.bin"), tmp_path).is_file()
    with pytest.raises(ReferenceValidationError):
        validate_asset_path(AssetRef(registry_id="missing"), tmp_path, registry={})
    with pytest.raises(ReferenceValidationError):
        validate_asset_path(AssetRef(relative_path="missing.bin"), tmp_path)


def test_symlink_escape_is_rejected_on_actual_filesystem(tmp_path):
    root = tmp_path / "approved"
    root.mkdir()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"synthetic")
    link = root / "escape.bin"
    try:
        link.symlink_to(outside)
    except OSError as exc:
        pytest.skip(f"host cannot create unprivileged test symlink: {exc}")
    with pytest.raises(ReferenceValidationError):
        validate_asset_path(AssetRef(relative_path="escape.bin"), root)


def test_named_geometry_resolution_and_actual_overlap_boundary():
    data = site_data()
    data["targets"].append(
        {**data["targets"][0], "target_id": "other", "geometry_ref": "other-surface"}
    )
    site = SiteBundle.model_validate(data)
    for refs, overlap in (
        (frozenset({"mesh"}), False),
        (frozenset({"mesh", "other-surface"}), True),
        (frozenset({"mesh", "other-surface"}), None),
    ):
        with pytest.raises(ReferenceValidationError):
            validate_site_references(site, geometry_refs=refs, target_overlap=lambda a, b: overlap)


@pytest.mark.parametrize(
    "field,value",
    [
        ("horizontal_crs", "EPSG:999999"),
        ("metres_per_source_unit", 0),
        ("source_true_north", [0, 0, 0]),
        ("source_true_north", [0, 0, 1]),
        ("source_up_axis", [0, 1, 0]),
        ("source_to_analysis", [[0, 0, 0, 0]] * 4),
    ],
)
def test_known_frame_and_invertible_matrices(field, value):
    data = site_data()
    data[field] = value
    with pytest.raises(ValidationError):
        SiteBundle.model_validate(data)


def test_duplicate_targets_and_shared_surface_rejected():
    data = site_data()
    data["targets"].append(copy.deepcopy(data["targets"][0]))
    with pytest.raises(ValidationError):
        SiteBundle.model_validate(data)
    data["targets"][1]["target_id"] = "other"
    with pytest.raises(ValidationError):
        SiteBundle.model_validate(data)


def test_nested_unknown_fields_rejected():
    for path in (
        ["origin"],
        ["vertical_datum"],
        ["assets", 0],
        ["assets", 0, "ref"],
        ["targets", 0],
        ["rights", 0],
        ["coverage"],
        ["readiness"],
    ):
        data = site_data()
        target = data
        for key in path:
            target = target[key]
        target["unexpected"] = True
        with pytest.raises(ValidationError):
            SiteBundle.model_validate(data)
