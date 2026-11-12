"""HTTP integration using explicitly synthetic INPUTS; no numerical result fixtures."""

from datetime import datetime, timedelta, timezone
import json

from fastapi.testclient import TestClient
import pytest

from tree_planner.api import create_app
from tree_planner.contracts import Capabilities, ContractError, ScenarioRef, SiteBundle
from tree_planner.site.assets import PURPOSES
from tree_planner.site.service import catalogue_fingerprint, geometry_fingerprint


def broken_handler(*args):
    raise RuntimeError("private C:/restricted.sqlite and callback detail")


@pytest.fixture
def setup(tmp_path):
    root = tmp_path / "inputs"
    root.mkdir()
    (root / "mesh").write_bytes(b"explicitly synthetic geometry INPUT only")
    caps = Capabilities(
        evaluator_versions=["synthetic@unit"],
        solar_versions=["synthetic@unit"],
        search_versions=["synthetic@unit"],
    )
    app = create_app(
        tmp_path / "workspace",
        approved_asset_root=root,
        capabilities=caps,
        geometry_refs=frozenset({"mesh"}),
        handlers={"evaluate_layout": broken_handler},
        start_worker=False,
    )
    with TestClient(
        app, base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"}
    ) as client:
        yield app, client


def assert_error(response, status, code=None):
    assert response.status_code == status, response.text
    error = ContractError.model_validate(response.json())
    if code:
        assert error.code == code
    assert "restricted.sqlite" not in response.text
    assert "input" not in {k for f in response.json()["field_errors"] for k in f}
    return error


def seed(client, *, permission="permitted"):
    rights = {p: permission for p in PURPOSES}
    source = client.post(
        "/api/v1/sources",
        json={
            "source_reference": "synthetic authorship",
            "licence_reference": "test only",
            "evidence": ["synthetic declaration"],
            "rights": rights,
        },
    ).json()
    asset_response = client.post(
        "/api/v1/assets",
        json={"relative_path": "mesh", "source_id": source["source_id"], "capture_date": "unknown"},
    )
    assert asset_response.status_code == 201, asset_response.text
    asset = asset_response.json()
    identity = [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]]
    site = dict(
        schema_version="0.1.0",
        site_id="synthetic",
        scene_revision=1,
        semantic_revision=1,
        geometry_fingerprint="0" * 64,
        profile_library_revision=1,
        candidate_catalogue_revision=1,
        candidate_catalogue_fingerprint="0" * 64,
        site_kind="synthetic_test",
        name="Synthetic HTTP INPUT",
        origin={"latitude_deg": 53.3, "longitude_deg": -1.4, "height_m": 0},
        horizontal_crs="EPSG:27700",
        vertical_datum={"name": "synthetic", "status": "assumed", "evidence": ["synthetic"]},
        analysis_frame="enu_m",
        source_units="m",
        metres_per_source_unit=1,
        source_true_north=[0, 1, 0],
        source_up_axis=[0, 0, 1],
        source_to_analysis=identity,
        analysis_to_viewer=identity,
        assets=[
            dict(
                asset_id="mesh",
                ref={"registry_id": asset["registry_id"]},
                sha256=asset["sha256"],
                kind="synthetic",
                source_id=source["source_id"],
                capture_date="unknown",
                semantic_class="terrain",
            )
        ],
        targets=[
            dict(
                target_id="target",
                geometry_ref="mesh",
                area_basis="surface",
                evidence_status="synthetic",
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
                source_id=source["source_id"],
                source_reference="synthetic authorship",
                licence_reference="test only",
                required_attribution="Synthetic INPUT",
                evidence=["synthetic declaration"],
                **rights,
            )
        ],
        coverage=dict(
            study_extent_ref="mesh",
            context_extent_ref="mesh",
            missing_region_refs=[],
            horizon_limitations=["synthetic"],
            boundary_limitations=[],
        ),
        readiness=dict(
            blockers=[], warnings=[], optional_missing_inputs=[], survey_requirements=[]
        ),
    )
    typed = SiteBundle.model_validate(site)
    site["geometry_fingerprint"] = geometry_fingerprint(typed.assets)
    site["candidate_catalogue_fingerprint"] = catalogue_fingerprint(typed.candidate_catalogue)
    response = client.post("/api/v1/sites/import", json=site)
    assert response.status_code == 201, response.text
    response = client.post(
        "/api/v1/layouts",
        json=dict(
            schema_version="0.1.0", layout_id="empty", revision=1, kind="proposed", placements=[]
        ),
    )
    assert response.status_code == 201, response.text
    return dict(
        schema_version="0.1.0",
        site_id="synthetic",
        scene_revision=1,
        semantic_revision=1,
        profile_library_revision=1,
        candidate_catalogue_revision=1,
        candidate_catalogue_fingerprint=site["candidate_catalogue_fingerprint"],
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
            allowed_profile_ids=[],
            at_most_one_profile_per_location=True,
            winter_limits=[],
            survey_requirements=[],
        ),
        objective=dict(
            kind="maximise_shade_under_budget", primary_case_id="summer", quantity_kind="geometric"
        ),
        numerics=dict(
            evaluator="synthetic",
            evaluator_version="unit",
            spatial_spacing_m=1,
            ray_offset_m=0.001,
            intersection_tolerance_m=0,
            feasibility_tolerance=0,
            solar_algorithm="synthetic",
            solar_version="unit",
            quadrature="midpoint",
        ),
        search=dict(
            algorithm="synthetic",
            version="unit",
            seed=0,
            comparison_policy="synthetic",
            reference_policy="synthetic",
            deadline_utc=(datetime.now(timezone.utc) + timedelta(hours=1))
            .isoformat()
            .replace("+00:00", "Z"),
        ),
        assumptions=["synthetic"],
        proposed_layout_ref=dict(layout_id="empty", revision=1),
    )


def create(client, inp):
    response = client.post("/api/v1/scenarios", json=inp)
    assert response.status_code == 201, response.text
    return response.json()


def request_for(scenario, request_id="synthetic-request"):
    return dict(
        request_id=request_id,
        scenario_ref={k: scenario[k] for k in ("scenario_id", "revision", "scope")},
        operation="evaluate_layout",
        arguments={"layout_ref": {"layout_id": "empty", "revision": 1}},
    )


def test_health_version_and_structured_routing(setup):
    app, client = setup
    health = client.get("/api/v1/health").json()
    assert health["status"] == "ok" and health["worker_mode"] == "manual"
    assert health["version"] and health["schema_version"] == "0.1.0"
    assert_error(client.get("/missing"), 404)
    assert_error(client.get("/api/v1/health/"), 404)
    assert_error(client.delete("/api/v1/health"), 405)
    assert app.state.jobs is app.state.service.jobs


@pytest.mark.parametrize(
    "body",
    [
        "null",
        "[]",
        "1",
        '"text"',
        '{"operation":"shell","url":"https://example.invalid"}',
        '{"operation":"evaluate_layout","request_id":"x","arguments":{},"scenario_ref":NaN}',
    ],
)
def test_safe_invalid_job_bodies(setup, body):
    _, client = setup
    assert_error(
        client.post("/api/v1/jobs", content=body, headers={"Content-Type": "application/json"}),
        422,
        "INVALID_INPUT",
    )


def test_unknown_exact_references_and_no_latest(setup):
    _, client = setup
    assert_error(
        client.get("/api/v1/sites/missing?scene_revision=1&semantic_revision=1"),
        404,
        "UNKNOWN_REVISION",
    )
    assert_error(client.get("/api/v1/sites/missing"), 422)
    assert_error(client.get("/api/v1/profiles/missing?library_revision=1"), 404)
    assert_error(client.get("/api/v1/scenarios/missing?revision=1"), 404)
    assert_error(client.get("/api/v1/jobs/missing"), 404)
    assert_error(client.get("/api/v1/results/missing"), 404)


def test_human_revision_and_agent_prepare_are_separate(setup):
    app, client = setup
    inp = seed(client)
    accepted = create(client, inp)
    path = "/api/v1/scenarios/" + accepted["scenario_id"]
    assert client.get(path + "?revision=1").headers["etag"] == '"1"'
    assert_error(client.put(path, json=inp), 409)
    assert_error(client.put(path, json=inp, headers={"If-Match": "1"}), 409)
    assert_error(client.put(path, json={**inp, "approved": True}, headers={"If-Match": '"1"'}), 422)
    envelope = dict(
        request_id="prepare",
        operation="prepare_scenario",
        arguments={
            "base_scenario_ref": request_for(accepted)["scenario_ref"],
            "proposed_edits": inp,
        },
    )
    draft = client.post("/api/v1/operations", json=envelope)
    assert draft.status_code == 200, draft.text
    assert draft.json()["scope"] == "hypothetical"
    assert not hasattr(app.state.agent, "accept_scenario")
    assert_error(client.post("/api/v1/operations", json={**envelope, "approved": True}), 422)
    newer = client.put(path, json=inp, headers={"If-Match": '"1"'})
    assert newer.status_code == 200 and newer.json()["revision"] == 2
    assert_error(client.put(path, json=inp, headers={"If-Match": '"1"'}), 409)
    assert client.get(path + "?revision=1").json()["revision"] == 1


def test_real_admission_poll_cancel_ordering_and_atomic_supersession(setup):
    app, client = setup
    inp = seed(client)
    scenario = create(client, inp)
    request = request_for(scenario)
    first = client.post("/api/v1/jobs", json=request)
    assert first.status_code == 202, first.text
    first = first.json()
    assert first["status"] == "queued" and first["delivery"] is None
    assert client.post("/api/v1/jobs", json=request).json() == first
    second = client.post("/api/v1/jobs", json=request_for(scenario, "second")).json()
    assert second["selection_seq"] == first["selection_seq"] + 1
    selection_path = f"/api/v1/scenarios/{scenario['scenario_id']}/selections?revision=1"
    selection = client.get(selection_path).json()
    assert selection["evaluation"]["selection"]["accepted_job_id"] == second["job_id"]
    assert selection["evaluation"]["current_job"] is None
    assert client.post(f"/api/v1/jobs/{second['job_id']}/cancel").json()["status"] == "cancelled"
    conflict = request_for(scenario)
    conflict["arguments"]["layout_ref"]["revision"] = 2
    assert_error(client.post("/api/v1/jobs", json=conflict), 404)
    newer = client.put(
        f"/api/v1/scenarios/{scenario['scenario_id']}", json=inp, headers={"If-Match": '"1"'}
    )
    assert newer.status_code == 200
    assert client.get(f"/api/v1/jobs/{first['job_id']}").json()["superseded_by_revision"] == 2
    assert client.get(selection_path).json()["evaluation"]["current_job"] is None
    app.state.run_one()
    failed = client.get(f"/api/v1/jobs/{first['job_id']}").json()
    assert failed["status"] == "failed" and failed["run_id"] is None
    ContractError.model_validate(failed["error"])
    assert "restricted.sqlite" not in json.dumps(failed)


@pytest.mark.parametrize(
    "permission,code", [("restricted", "RIGHTS_RESTRICTED"), ("unknown", "RIGHTS_UNKNOWN")]
)
def test_rights_refused_before_admission(setup, permission, code):
    app, client = setup
    scenario = create(client, seed(client, permission=permission))
    assert_error(client.post("/api/v1/jobs", json=request_for(scenario)), 422, code)
    assert app.state.jobs.selection(scenario["scenario_id"], 1, "accepted", "evaluation") is None


def test_unavailable_and_no_agent_arbitrary_operations(setup):
    _, client = setup
    scenario = create(client, seed(client))
    request = request_for(scenario)
    request.update(operation="search_layouts", arguments={})
    assert_error(client.post("/api/v1/jobs", json=request), 503, "TOOL_UNAVAILABLE")
    for extra in (
        {"handler": "os.system"},
        {"timeout": 99},
        {"view_slot": "search"},
        {"input_fingerprint": "0" * 64},
        {"approved": True},
        {"url": "file:///private"},
    ):
        assert_error(client.post("/api/v1/jobs", json={**request, **extra}), 422)
    assert_error(
        client.post(
            "/api/v1/assets",
            json={"relative_path": "../private", "source_id": "missing", "capture_date": "unknown"},
        ),
        404,
    )


def test_callback_activation_rolls_back_accepted_revision(setup, monkeypatch):
    app, client = setup
    inp = seed(client)
    scenario = create(client, inp)
    original = app.state.jobs.activate

    def corrupt(*args, **kwargs):
        original(*args, **kwargs)
        raise RuntimeError("private C:/restricted.sqlite")

    monkeypatch.setattr(app.state.jobs, "activate", corrupt)
    assert_error(
        client.put(
            f"/api/v1/scenarios/{scenario['scenario_id']}", json=inp, headers={"If-Match": '"1"'}
        ),
        503,
        "TOOL_UNAVAILABLE",
    )
    assert_error(client.get(f"/api/v1/scenarios/{scenario['scenario_id']}?revision=2"), 404)
    assert app.state.scenarios.get_scenario(ScenarioRef(**request_for(scenario)["scenario_ref"]))


@pytest.mark.parametrize("value", [float("nan"), float("inf"), "1", True, None])
def test_nonfinite_wrong_types_and_safe_field_paths(setup, value):
    _, client = setup
    inp = seed(client)
    inp["numerics"]["spatial_spacing_m"] = value
    # JSON encoder intentionally emits nonstandard NaN/Infinity to test rejection.
    error = assert_error(
        client.post(
            "/api/v1/scenarios",
            content=json.dumps(inp),
            headers={"Content-Type": "application/json"},
        ),
        422,
    )
    assert error.field_errors
    response = client.post("/api/v1/scenarios", json={"C:/restricted.sqlite": "private"})
    assert_error(response, 422)
    assert "private" not in response.text


def test_human_acceptance_of_prepared_scenario_is_atomic(setup):
    app, client = setup
    inp = seed(client)
    base = create(client, inp)
    job = client.post("/api/v1/jobs", json=request_for(base)).json()
    draft = client.post(
        "/api/v1/operations",
        json=dict(
            request_id="draft",
            operation="prepare_scenario",
            arguments=dict(base_scenario_ref=request_for(base)["scenario_ref"], proposed_edits=inp),
        ),
    ).json()
    draft_ref = request_for(draft)["scenario_ref"]
    assert_error(client.post("/api/v1/jobs", json=request_for(draft)), 409)
    accepted = client.post("/api/v1/scenarios/accept", json=draft_ref, headers={"If-Match": '"1"'})
    assert accepted.status_code == 200, accepted.text
    assert accepted.json()["revision"] == 2 and accepted.json()["scope"] == "accepted"
    assert client.get(f"/api/v1/jobs/{job['job_id']}").json()["superseded_by_revision"] == 2
    assert app.state.scenarios.acceptance_source(
        ScenarioRef(**request_for(accepted.json())["scenario_ref"])
    ) == ScenarioRef(**draft_ref)
    assert_error(
        client.post("/api/v1/scenarios/accept", json=draft_ref, headers={"If-Match": '"1"'}), 409
    )


def test_transport_boundaries_wrap_callback_errors_and_oversized_bodies(setup, monkeypatch):
    app, client = setup
    assert_error(client.post("/api/v1/jobs", content=b" " * 1_048_577), 413)
    response = client.post("/api/v1/jobs", json={}, headers={"Origin": "https://foreign.invalid"})
    assert_error(response, 403)

    def corrupt(*args):
        raise RuntimeError("C:/restricted.sqlite")

    monkeypatch.setattr(app.state.jobs, "get_job", corrupt)
    response = client.get("/api/v1/jobs/any")
    assert_error(response, 503)
    assert response.headers["cache-control"] == "no-store"
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:8000"


def test_capacity_and_actual_idempotency_conflict(setup):
    app, client = setup
    inp = seed(client)
    base = create(client, inp)
    assert client.post("/api/v1/jobs", json=request_for(base)).status_code == 202
    newer = client.put(
        f"/api/v1/scenarios/{base['scenario_id']}", json=inp, headers={"If-Match": '"1"'}
    ).json()
    assert_error(client.post("/api/v1/jobs", json=request_for(newer)), 409, "REVISION_CONFLICT")
    app.state.jobs.capacity = 1
    assert_error(client.post("/api/v1/jobs", json=request_for(newer, "new-request")), 503)


def test_profile_and_layout_exact_revision_and_durable_reopen(setup):
    app, client = setup
    inp = seed(client)
    profile = dict(
        schema_version="0.1.0",
        profile_id="synthetic-profile",
        library_revision=3,
        species_size_label="hypothetical synthetic",
        source_ids=[],
        assumption_ids=["synthetic"],
        cost_pence=100,
        cost_scope="synthetic INPUT",
        price_date="2026-11-12",
        states={
            "mature": dict(
                horizon_years=20,
                leaf_state="synthetic",
                crown_center_height_m=4,
                crown_radii_m=[2, 2, 2],
                trunk_radius_m=0.1,
                trunk_height_m=2,
                attenuation={"mode": "opaque"},
            )
        },
    )
    assert client.post("/api/v1/profiles", json=profile).status_code == 201
    assert client.get("/api/v1/profiles/synthetic-profile?library_revision=3").json() == profile
    assert_error(client.get("/api/v1/profiles/synthetic-profile?library_revision=2"), 404)
    base = create(client, inp)
    reopened = create_app(
        app.state.repository.workspace,
        approved_asset_root=app.state.assets.root,
        start_worker=False,
    )
    with TestClient(reopened, base_url="http://127.0.0.1") as other:
        assert other.get(f"/api/v1/scenarios/{base['scenario_id']}?revision=1").json() == base


def test_invalid_callback_return_cannot_complete_job(tmp_path):
    app = create_app(
        tmp_path / "workspace",
        handlers={"evaluate_layout": lambda *args: {"not": "a Result"}},
        capabilities=Capabilities(
            evaluator_versions=["synthetic@unit"],
            solar_versions=["synthetic@unit"],
            search_versions=["synthetic@unit"],
        ),
        geometry_refs=frozenset({"mesh"}),
        start_worker=False,
    )
    (app.state.assets.root / "mesh").write_bytes(b"synthetic INPUT")
    with TestClient(
        app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        base = create(client, seed(client))
        job = client.post("/api/v1/jobs", json=request_for(base)).json()
        app.state.run_one()
        polled = client.get(f"/api/v1/jobs/{job['job_id']}").json()
        assert (
            polled["status"] == "failed" and polled["delivery"] is None and polled["run_id"] is None
        )


def test_exported_agent_dispatch_also_validates_full_envelope(setup):
    app, client = setup
    inp = seed(client)
    base = create(client, inp)
    from tree_planner.api.service import AgentDispatcher

    dispatcher = AgentDispatcher(
        app.state.service,
        accepted_ref=ScenarioRef.model_validate(request_for(base)["scenario_ref"]),
    )
    prepared = dispatcher.dispatch(
        dict(
            request_id="direct-prepare",
            operation="prepare_scenario",
            arguments=dict(base_scenario_ref=request_for(base)["scenario_ref"], proposed_edits=inp),
        )
    )
    assert prepared.scope == "hypothetical"
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        dispatcher.dispatch(
            dict(
                request_id="direct-prepare",
                operation="prepare_scenario",
                approved=True,
                arguments=dict(base_scenario_ref=None, proposed_edits=inp),
            )
        )


def test_startup_recovery_requires_lease_and_does_not_touch_live_records(setup):
    app, client = setup
    base = create(client, seed(client))
    queued = client.post("/api/v1/jobs", json=request_for(base)).json()
    app.state.jobs.claim()  # Controlled abandoned running record, no successful computation.
    other = create_app(
        app.state.repository.workspace,
        approved_asset_root=app.state.assets.root,
        handlers={"evaluate_layout": broken_handler},
    )
    from tree_planner.site.repository import DomainError

    with app.state.service.lease.held():
        with pytest.raises(DomainError):
            with TestClient(other, base_url="http://127.0.0.1"):
                pass
        assert app.state.jobs.get_job(queued["job_id"]).status == "running"
    with TestClient(other, base_url="http://127.0.0.1") as running:
        interrupted = running.get(f"/api/v1/jobs/{queued['job_id']}").json()
        assert interrupted["status"] == "failed"
        assert interrupted["error"]["code"] == "WORKER_INTERRUPTED"


def test_site_readiness_is_recomputed_at_import_and_get(setup):
    _, client = setup
    seed(client, permission="unknown")
    site = client.get("/api/v1/sites/synthetic?scene_revision=1&semantic_revision=1").json()
    assert site["readiness"]["blockers"]
    site["readiness"] = dict(
        blockers=[], warnings=[], optional_missing_inputs=[], survey_requirements=[]
    )
    # Immutable stored input had this declared readiness; response must recompute it.
    imported = client.post("/api/v1/sites/import", json=site)
    assert imported.status_code == 201, imported.text
    assert imported.json()["readiness"]["blockers"]


def test_actual_http_openapi_uses_domain_responses_and_safe_errors(setup):
    _, client = setup
    schema = client.get("/api/v1/openapi.json").json()
    jobs = schema["paths"]["/api/v1/jobs"]["post"]["responses"]
    assert jobs["202"]["content"]["application/json"]["schema"]["$ref"].endswith("/Job")
    assert jobs["422"]["content"]["application/json"]["schema"]["$ref"].endswith("/ContractError")
    assert "Result" in schema["components"]["schemas"]
