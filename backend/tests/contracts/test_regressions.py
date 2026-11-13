"""Synthetic end-to-end serialization/reference checks; never evaluator proof."""

import copy
import json

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient
from fastapi.responses import JSONResponse
import pytest
from pydantic import ValidationError

from tree_planner.contracts import (
    Capabilities,
    Constraints,
    EvaluationCase,
    Layout,
    ReferenceValidationError,
    Scenario,
    ScenarioInput,
    ScenarioRef,
    SiteBundle,
    TreeProfile,
    validate_scenario_ref,
    validate_scenario_references,
)
from test_basic import placement, state
from test_site_references import SHA, site_data


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


def scenario_data():
    return dict(
        schema_version="0.1.0",
        scenario_id="synthetic-scenario",
        revision=1,
        created_at_utc="2026-11-12T12:00:00Z",
        scope="accepted",
        base_scenario_ref=None,
        input=input_data(),
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


def reference_args():
    data = site_data()
    data["vertical_datum"] = dict(
        name="synthetic z=0 assumption", status="assumed", evidence=["synthetic"]
    )
    # Labelled synthetic permissions exercise policy. No real-source permission is asserted.
    data["rights"][0]["local_use_status"] = "permitted"
    data["rights"][0]["evidence"] = ["synthetic test authorship"]
    layout = Layout(
        schema_version="0.1.0",
        layout_id="synthetic-layout",
        revision=1,
        kind="proposed",
        placements=[placement()],
    )
    return dict(
        site=SiteBundle.model_validate(data),
        profiles={"synthetic-profile": TreeProfile.model_validate(profile_data())},
        layouts={(layout.layout_id, 1): layout},
        scenarios={},
        capabilities=Capabilities(
            evaluator_versions=["synthetic-test@unit"],
            solar_versions=["synthetic-test@unit"],
            search_versions=["synthetic-test@unit"],
        ),
        verified_catalogue_fingerprint=SHA,
        verified_geometry_fingerprint=SHA,
    )


def test_real_http_arrays_strict_nested_and_nonfinite():
    app = FastAPI()

    @app.exception_handler(RequestValidationError)
    async def safe_test_errors(request, exc):
        # Test-only error mapper: the API owner must likewise avoid echoing NaN
        # or arbitrary input/exception contexts into JSON error bodies.
        return JSONResponse(status_code=422, content={"code": "INVALID_INPUT"})

    @app.post("/synthetic-contract-only")
    def submit(body: ScenarioInput):
        return body

    with TestClient(app) as client:
        response = client.post("/synthetic-contract-only", json=input_data())
        assert response.status_code == 200
        assert isinstance(response.json()["evaluation_cases"], list)
        for value in (True, "1", 1.0):
            data = input_data()
            data["scene_revision"] = value
            assert client.post("/synthetic-contract-only", json=data).status_code == 422
        data = input_data()
        data["numerics"]["ray_offset_m"] = float("inf")
        # Raw JSON exercises actual HTTP decoding, including nonstandard float tokens.
        assert (
            client.post(
                "/synthetic-contract-only",
                content=json.dumps(data),
                headers={"content-type": "application/json"},
            ).status_code
            == 422
        )


def object_paths(value, prefix=()):
    if isinstance(value, dict):
        yield prefix
        for key, item in value.items():
            yield from object_paths(item, (*prefix, key))
    elif isinstance(value, list):
        for key, item in enumerate(value):
            yield from object_paths(item, (*prefix, key))


def test_unknown_at_every_nested_model_boundary():
    # states/target_weights are intentional ID-key maps; their VALUES remain strict.
    for model, source, skip in (
        (Scenario, scenario_data(), {("input", "evaluation_cases", 0, "target_weights")}),
        (TreeProfile, profile_data(), {("states",)}),
    ):
        for path in object_paths(source):
            if path in skip:
                continue
            data = copy.deepcopy(source)
            target = data
            for part in path:
                target = target[part]
            target["extra"] = "untrusted"
            with pytest.raises(ValidationError):
                model.model_validate(data)


def test_immutable_refs_and_deep_snapshot():
    obj = Scenario.model_validate(scenario_data())
    with pytest.raises(ValidationError):
        obj.revision = 2
    with pytest.raises(TypeError):
        obj.input.evaluation_cases[0].target_weights["target"] = 10
    profile = TreeProfile.model_validate(profile_data())
    with pytest.raises(TypeError):
        profile.states.clear()


def test_valid_synthetic_reference_graph_and_roundtrip():
    obj = Scenario.model_validate_json(json.dumps(scenario_data()))
    assert Scenario.model_validate(obj.model_dump(mode="json")) == obj
    validate_scenario_references(obj, **reference_args())


@pytest.mark.parametrize(
    "field,value",
    [
        ("scene_revision", 2),
        ("semantic_revision", 2),
        ("profile_library_revision", 2),
        ("candidate_catalogue_revision", 2),
        ("candidate_catalogue_fingerprint", "b" * 64),
        ("target_ids", ["missing"]),
    ],
)
def test_stale_or_unresolved_references(field, value):
    data = scenario_data()
    data["input"][field] = value
    with pytest.raises((ValidationError, ReferenceValidationError)):
        validate_scenario_references(Scenario.model_validate(data), **reference_args())


def test_scope_mismatch_and_wrong_mapping_identity():
    scenario = Scenario.model_validate(scenario_data())
    ref = ScenarioRef(scenario_id=scenario.scenario_id, revision=1, scope="hypothetical")
    with pytest.raises(ReferenceValidationError):
        validate_scenario_ref(ref, {(scenario.scenario_id, 1): scenario})
    ref = ScenarioRef(scenario_id="wrong", revision=1, scope="accepted")
    with pytest.raises(ReferenceValidationError):
        validate_scenario_ref(ref, {("wrong", 1): scenario})


@pytest.mark.parametrize("change", [{"horizon_years": 21}, {"profile_state": "missing"}])
def test_profile_state_horizon_reference(change):
    data = scenario_data()
    data["input"]["evaluation_cases"][0].update(change)
    with pytest.raises(ReferenceValidationError):
        validate_scenario_references(Scenario.model_validate(data), **reference_args())


def test_overlapping_and_reversed_bins():
    case = input_data()["evaluation_cases"][0]
    for bins in (
        [case["time_bins"][0]] * 2,
        [dict(midpoint_utc="2026-07-01T13:00:00Z", duration_h=2), case["time_bins"][0]],
    ):
        with pytest.raises(ValidationError):
            EvaluationCase.model_validate({**case, "time_bins": bins})
    EvaluationCase.model_validate(
        {
            **case,
            "time_bins": [
                case["time_bins"][0],
                dict(midpoint_utc="2026-07-01T13:00:00Z", duration_h=1),
            ],
        }
    )


def test_lifecycle_winter_bool_and_conflicts():
    source = input_data()["constraints"]
    for change in (
        {"budget_basis": "lifecycle"},
        {"at_most_one_profile_per_location": 1},
    ):
        with pytest.raises(ValidationError):
            Constraints.model_validate({**source, **change})
    obj = Constraints.model_validate_json(
        json.dumps({**source, "incompatible_candidate_pairs": [["a", "b"]]})
    )
    assert obj.incompatible_candidate_pairs == (("a", "b"),)


def test_candidate_location_profile_uniqueness():
    candidate = dict(
        candidate_id="a",
        location_id="location",
        position_enu_m=[0, 0, 0],
        profile_id="p1",
        plantability_status="provisional",
        source_ids=[],
        assumption_ids=["synthetic"],
    )
    data = site_data()
    # Profile alternatives at one location must be retained.
    data["candidate_catalogue"] = [
        candidate,
        {**candidate, "candidate_id": "b", "profile_id": "p2"},
    ]
    SiteBundle.model_validate(data)
    for change in (
        {"candidate_id": "a", "profile_id": "p2"},
        {"candidate_id": "b"},
        {"candidate_id": "b", "profile_id": "p2", "position_enu_m": [1, 0, 0]},
        {"candidate_id": "b", "profile_id": "p2", "location_id": "other"},
    ):
        data["candidate_catalogue"][1] = {**candidate, **change}
        with pytest.raises(ValidationError):
            SiteBundle.model_validate(data)
