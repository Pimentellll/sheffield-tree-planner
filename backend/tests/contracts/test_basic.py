"""Labelled synthetic inputs; these tests do not execute physical evaluation."""

import json

import pytest
from pydantic import ValidationError

from tree_planner.contracts import (
    Attenuation,
    Layout,
    Placement,
    ScenarioRef,
    TimeBin,
    TreeProfile,
    TreeState,
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


def test_http_json_arrays_and_roundtrip():
    obj = Placement.model_validate_json(json.dumps(placement()))
    assert obj.position_enu_m == (0, 0, 0)
    assert Placement.model_validate(obj.model_dump(mode="json")) == obj


@pytest.mark.parametrize("value", [True, "1", 0, -1, 1.0])
def test_strict_positive_revision(value):
    with pytest.raises(ValidationError):
        ScenarioRef(scenario_id="synthetic", revision=value, scope="accepted")


def test_strict_nested_unknown_and_finite():
    bad = state()
    bad["attenuation"]["invented"] = 1
    with pytest.raises(ValidationError):
        TreeState.model_validate(bad)
    for value in (float("nan"), float("inf"), True, "2"):
        bad = placement()
        bad["position_enu_m"][0] = value
        with pytest.raises(ValidationError):
            Placement.model_validate(bad)


def test_unsupported_attenuation_fails_closed():
    for mode in ("fixed_crossing", "path_length"):
        with pytest.raises(ValidationError):
            Attenuation.model_validate({"mode": mode, "transmission": 0.5})


def test_literal_z_and_duration():
    TimeBin(midpoint_utc="2026-07-01T12:00:00Z", duration_h=1)
    for stamp in ("2026-07-01T12:00:00+00:00", "2026-07-01T12:00:00", "badZ"):
        with pytest.raises(ValidationError):
            TimeBin(midpoint_utc=stamp, duration_h=1)


def test_duplicate_placement_and_location():
    for second in (placement(), {**placement(), "placement_id": "other"}):
        with pytest.raises(ValidationError):
            Layout(
                schema_version="0.1.0",
                layout_id="synthetic",
                revision=1,
                kind="proposed",
                placements=[placement(), second],
            )


def test_profile_accepts_synthetic_state_and_rejects_cost_bool():
    data = dict(
        schema_version="0.1.0",
        profile_id="synthetic-profile",
        library_revision=1,
        species_size_label="hypothetical generic",
        source_ids=[],
        assumption_ids=["synthetic"],
        cost_pence=10000,
        cost_scope="synthetic upfront estimate",
        price_date="2026-11-12",
        states={"mature": state()},
    )
    assert TreeProfile.model_validate(data).states["mature"].horizon_years == 20
    data["cost_pence"] = True
    with pytest.raises(ValidationError):
        TreeProfile.model_validate(data)
