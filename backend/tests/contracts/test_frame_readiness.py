"""Frame math is serialization/import validation, not shadow or solar validation."""

import pytest
from pydantic import ValidationError

from tree_planner.contracts import SiteBundle, compute_readiness
from test_site_references import site_data


def test_east_scale_and_handedness_must_match_explicit_frame():
    for east in (-1, 2):
        data = site_data()
        data["source_to_analysis"] = [[east, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
        with pytest.raises(ValidationError):
            SiteBundle.model_validate(data)


def test_row_major_column_vector_transform_roundtrip():
    data = site_data()
    data["analysis_to_viewer"] = [[1, 0, 0, 10], [0, 0, 1, 20], [0, -1, 0, 30], [0, 0, 0, 1]]
    matrix = SiteBundle.model_validate(data).analysis_to_viewer
    point = (2, 3, 4, 1)
    transformed = tuple(sum(a * b for a, b in zip(row, point)) for row in matrix)
    assert transformed == (12, 24, 27, 1)
    # Exact inverse of this synthetic axis permutation/translation.
    inverse = ((1, 0, 0, -10), (0, 0, -1, 30), (0, 1, 0, -20), (0, 0, 0, 1))
    assert tuple(sum(a * b for a, b in zip(row, transformed)) for row in inverse) == point


def test_forged_ready_cannot_override_rights_or_vertical_unknowns():
    data = site_data()
    data["readiness"]["blockers"] = []
    data["readiness"]["warnings"] = []
    result = compute_readiness(SiteBundle.model_validate(data))
    assert any("vertical datum" in blocker for blocker in result.blockers)
    for use in ("local_use_status", "team_share_status", "public_display_status", "export_status"):
        assert any(
            use in blocker
            for blocker in compute_readiness(SiteBundle.model_validate(data), use=use).blockers
        )


def test_imported_bounding_boxes_do_not_assert_polygon_overlap():
    data = site_data()
    data["targets"][0]["area_basis"] = "planimetric"
    bounds = dict(minimum_enu_m=[0, 0, 0], maximum_enu_m=[10, 10, 0])
    data["targets"][0]["bounds"] = bounds
    # Distinct polygon references can have intersecting bounding envelopes and
    # disjoint actual surfaces. Runtime geometry validation must decide overlap.
    data["targets"].append(
        {**data["targets"][0], "target_id": "other", "geometry_ref": "other-surface"}
    )
    assert SiteBundle.model_validate(data).targets[1].bounds is not None
