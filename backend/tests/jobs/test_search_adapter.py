"""Controlled callback fixtures exercise the consumer, not numerical search."""

import importlib.util
from pathlib import Path
import threading

import pytest
from tree_planner.jobs import JobStore
from tree_planner.contracts import Scenario
from tree_planner.jobs.search import SearchHandler, SearchProvider, SearchVerdict

_spec = importlib.util.spec_from_file_location(
    "jobs_fixtures", Path(__file__).with_name("test_jobs.py")
)
fixture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fixture)


def test_requires_independent_providers():
    with pytest.raises((TypeError, ValueError)):
        SearchProvider(None, None, None, None, None)


def test_controlled_miss_and_identity(tmp_path):
    scene = fixture.scenario()
    scene["input"]["objective"] = {
        "kind": "minimise_cost_for_target",
        "primary_case_id": "case",
        "quantity_kind": "geometric",
        "target_gain_m2_h": 1.0,
    }
    scene = Scenario.model_validate(scene).model_dump(mode="json")
    deps = {"scenario": scene, "profiles": {}}
    hashes = {"site": fixture.HASH}

    def resolve(ref, *, operation):
        return deps, dict(hashes)

    def manifest(deps):
        return {"fixture": "state-machine-only"}

    def produce(deps, job, context, run_id, local_stop, external_stop):
        result = fixture.synthetic_handler(
            job, context, run_id, local_stop, external_stop
        ).model_dump(mode="json")
        result["analytical_outcome"] = "search_exhausted_without_target"
        return result

    def validate(deps, result, local_stop, external_stop):
        return SearchVerdict(
            layouts=(),
            outcome="search_exhausted_without_target",
            target_met=False,
            proof_verified=False,
        )

    handler = SearchHandler(SearchProvider(resolve, produce, validate, manifest, manifest))
    store = JobStore(tmp_path / "db")
    store.activate("synthetic", 1)
    all_hashes = {
        **hashes,
        **{
            "execution:" + k: v
            for k, v in handler.execution_hashes(deps, operation="search_layouts").items()
        },
    }
    job = fixture.submit(
        store, "search", operation="search_layouts", hashes=all_hashes, scene=scene
    )
    finished = store.run_one({"search_layouts": handler}, threading.Event())
    assert finished.status == "completed"
    assert store.read_run(finished.run_id).analytical_outcome == "search_exhausted_without_target"
    assert store.current("synthetic", 1, "accepted", "search").job_id == job.job_id


@pytest.mark.parametrize(
    "mutation",
    [
        "run",
        "hash",
        "scenario",
        "cost",
        "feasibility",
        "constraints",
        "target",
        "proof",
        "changed_inputs",
        "unknown",
        "target_metric",
        "candidate",
        "position",
        "pin",
        "horizon",
        "valid",
    ],
)
def test_rejects_untrusted_claims(tmp_path, mutation):
    from tree_planner.jobs.search import LayoutVerdict
    from tree_planner.canonical import content_hash
    from tree_planner.contracts import SiteBundle, TreeProfile
    from tree_planner.site.repository import Repository

    helpers = importlib.util.spec_from_file_location(
        "search_input_helpers", Path(__file__).parents[1] / "site/synthetic_inputs.py"
    )
    inputs = importlib.util.module_from_spec(helpers)
    helpers.loader.exec_module(inputs)
    scene = fixture.scenario()
    scene["input"]["constraints"]["budget_pence"] = 20
    scene["input"]["constraints"]["max_tree_count"] = 2
    scene["input"]["objective"] = {
        "kind": "minimise_cost_for_target",
        "primary_case_id": "case",
        "quantity_kind": "geometric",
        "target_gain_m2_h": 1.0,
    }
    scene["input"]["constraints"]["allowed_profile_ids"] = ["p"]
    site = inputs.site_data()
    site["site_id"] = scene["input"]["site_id"]
    site["candidate_catalogue"] = [
        dict(
            candidate_id="c",
            location_id="loc",
            position_enu_m=[0, 0, 0],
            profile_id="p",
            plantability_status="documented_model_region",
            source_ids=[],
            assumption_ids=["synthetic"],
        )
    ]
    site = SiteBundle.model_validate(site).model_dump(mode="json")
    site["candidate_catalogue_fingerprint"] = content_hash(site["candidate_catalogue"])
    scene["input"]["candidate_catalogue_fingerprint"] = site["candidate_catalogue_fingerprint"]
    scene = Scenario.model_validate(scene).model_dump(mode="json")
    profile = inputs.profile_data()
    profile.update(profile_id="p", cost_pence=10)
    profile["states"]["mature"]["horizon_years"] = 1
    profile = TreeProfile.model_validate(profile).model_dump(mode="json")
    deps = {"scenario": scene, "site": site, "profiles": {"p": profile}}
    hashes = {"site": content_hash(site), "profile:p": content_hash(profile)}

    def resolve(ref, *, operation):
        return deps, dict(hashes)

    def manifest(deps):
        return {"fixture": "controlled"}

    def produce(deps_copy, job, context, run_id, local_stop, external_stop):
        r = fixture.synthetic_handler(job, context, run_id, local_stop, external_stop).model_dump(
            mode="json"
        )
        r["analytical_outcome"] = "feasible_candidate"
        r["layouts"] = [
            {
                "layout": {
                    "schema_version": "0.1.0",
                    "layout_id": "l",
                    "revision": 1,
                    "kind": "proposed",
                    "placements": [
                        {
                            "placement_id": "p1",
                            "location_id": "loc",
                            "position_enu_m": [0, 0, 0],
                            "profile_id": "p",
                            "candidate_id": "c",
                            "pinned": False,
                        }
                    ],
                },
                "scenario_ref": context["request"]["scenario_ref"],
                "role": "alternative",
                "cost_pence": 10,
                "tree_count": 1,
                "feasibility": "feasible",
                "reasons": [],
                "selected": True,
            }
        ]
        r["metrics"] = [
            {
                "metric_instance_id": "m",
                "metric_id": "additional_shade",
                "scenario_ref": context["request"]["scenario_ref"],
                "layout_id": "l",
                "case_id": "case",
                "target_id": None,
                "horizon_years": 1.0,
                "value": 2.0,
                "unit": "m2_h",
                "weighting": "unweighted",
                "quantity_kind": "geometric",
                "area_basis": None,
                "aggregation_basis": None,
            }
        ]
        if mutation == "candidate":
            r["layouts"][0]["layout"]["placements"][0]["candidate_id"] = "unknown"
        if mutation == "position":
            r["layouts"][0]["layout"]["placements"][0]["position_enu_m"][0] = 2
        if mutation == "pin":
            r["layouts"][0]["layout"]["placements"][0]["pinned"] = True
        if mutation == "horizon":
            r["metrics"][0]["horizon_years"] = 999
        if mutation == "target_metric":
            r["metrics"][0]["value"] = 0.5
        if mutation == "run":
            r["run_id"] = "wrong"
        if mutation == "hash":
            r["provenance"]["source_hashes"] = {"site": fixture.HASH}
        if mutation == "scenario":
            r["layouts"][0]["scenario_ref"]["scenario_id"] = "wrong"
        if mutation == "cost":
            r["layouts"][0]["cost_pence"] = 9
        if mutation == "proof":
            r["analytical_outcome"] = "proven_infeasible_finite_model"
            r["layouts"][0]["selected"] = False
            r["finite_model_proof"] = {
                "method": "fixture",
                "model_fingerprint": fixture.HASH,
                "evidence_ref": "fixture",
            }
        if mutation == "changed_inputs":
            hashes["site"] = "b" * 64
        return r

    def validate(deps_copy, result, local_stop, external_stop):
        if mutation == "unknown":
            raise ValueError("validator cannot determine feasibility")
        return SearchVerdict(
            layouts=(
                LayoutVerdict(
                    "l",
                    "infeasible" if mutation == "feasibility" else "feasible",
                    10,
                    ({"fake": "pass"},) if mutation == "constraints" else (),
                ),
            ),
            outcome=result.analytical_outcome,
            target_met=False if mutation == "target" else True,
            proof_verified=False,
        )

    handler = SearchHandler(SearchProvider(resolve, produce, validate, manifest, manifest))
    repo = Repository(tmp_path / "workspace")
    with repo.transaction() as db:
        repo._insert(db, "typed_site", "search-site", 1, "", site)
        repo._insert(db, "typed_profile", "search-profile", 1, "", profile)
    store = JobStore(repo.db_path)
    store.activate("synthetic", 1)
    all_hashes = {
        **hashes,
        **{
            "execution:" + k: v
            for k, v in handler.execution_hashes(deps, operation="search_layouts").items()
        },
    }
    fixture.submit(store, "bad", operation="search_layouts", hashes=all_hashes, scene=scene)
    finished = store.run_one({"search_layouts": handler}, threading.Event())
    if mutation == "valid":
        assert finished.status == "completed"
        assert store.read_run(finished.run_id).layouts[0].cost_pence == 10
    else:
        assert finished.status == "failed" and finished.run_id is None
        assert store.current("synthetic", 1, "accepted", "search") is None


def test_separate_slots_retry_stale_and_cancellation(tmp_path):
    scene = fixture.scenario()
    scene["input"]["objective"] = {
        "kind": "minimise_cost_for_target",
        "primary_case_id": "case",
        "quantity_kind": "geometric",
        "target_gain_m2_h": 1.0,
    }
    scene = Scenario.model_validate(scene).model_dump(mode="json")
    deps = {"scenario": scene, "profiles": {}}
    hashes = {"site": fixture.HASH}

    def resolve(ref, *, operation):
        return deps, dict(hashes)

    def manifest(deps):
        return {"fixture": "state-machine"}

    def produce(deps, job, context, run_id, local_stop, external_stop):
        r = fixture.synthetic_handler(job, context, run_id, local_stop, external_stop).model_dump(
            mode="json"
        )
        r["analytical_outcome"] = "search_exhausted_without_target"
        return r

    def validate(deps, result, local_stop, external_stop):
        return SearchVerdict((), "search_exhausted_without_target", False, False)

    handler = SearchHandler(SearchProvider(resolve, produce, validate, manifest, manifest))
    s = JobStore(tmp_path / "db")
    s.activate("synthetic", 1)
    hashes.update(
        {
            "execution:" + k: v
            for k, v in handler.execution_hashes(deps, operation="search_layouts").items()
        }
    )
    # Resolver returns only authoritative non-execution hashes.
    hashes.pop("execution:dependencies")
    hashes.pop("execution:producer")
    hashes.pop("execution:validator")
    admitted = {
        **hashes,
        **{
            "execution:" + k: v
            for k, v in handler.execution_hashes(deps, operation="search_layouts").items()
        },
    }
    eval_job = fixture.submit(s, "eval", scene=scene)
    assert (
        s.run_one({"evaluate_layout": fixture.synthetic_handler}, threading.Event()).status
        == "completed"
    )
    a = fixture.submit(s, "a", operation="search_layouts", hashes=admitted, scene=scene)
    assert fixture.submit(s, "a", operation="search_layouts", hashes=admitted, scene=scene) == a
    b = fixture.submit(s, "b", operation="search_layouts", hashes=admitted, scene=scene)
    assert s.run_one({"search_layouts": handler}, threading.Event()).status == "completed"
    assert s.current("synthetic", 1, "accepted", "search") is None
    assert s.current("synthetic", 1, "accepted", "evaluation").job_id == eval_job.job_id
    assert s.cancel(b.job_id)
    assert s.current("synthetic", 1, "accepted", "search") is None
    c = fixture.submit(s, "c", operation="search_layouts", hashes=admitted, scene=scene)
    assert s.run_one({"search_layouts": handler}, threading.Event()).status == "completed"
    assert s.current("synthetic", 1, "accepted", "search").job_id == c.job_id
    s.activate("synthetic", 2)
    assert s.current("synthetic", 1, "accepted", "search") is None


def test_deadline_produces_no_result(tmp_path):
    store = JobStore(tmp_path / "db")
    job = fixture.submit(store, "expired", operation="search_layouts", deadline=fixture.stamp(-1))
    assert store.run_one({}, threading.Event()) is None
    failed = store.get_job(job.job_id)
    assert (
        failed.status == "failed"
        and failed.error.code == "DEADLINE_EXCEEDED"
        and failed.run_id is None
    )


def test_http_controlled_consumer_contract(tmp_path):
    """HTTP callback fixture only: no physics or real search is performed."""
    from fastapi.testclient import TestClient
    from tree_planner.api import create_app
    from tree_planner.contracts import Capabilities
    from tree_planner.api.service import ApplicationService

    if not hasattr(ApplicationService, "resolve_for_execution"):
        pytest.skip("parent admission hook resolve_for_execution not yet supplied")
    spec = importlib.util.spec_from_file_location(
        "api_fixtures", Path(__file__).parents[1] / "api/test_app.py"
    )
    h = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(h)
    root = tmp_path / "inputs"
    root.mkdir()
    (root / "mesh").write_bytes(b"synthetic")
    holder = {}

    def resolve(ref, *, operation):
        return holder["app"].state.scenarios.resolve_for_job(ref, operation=operation)

    def manifest(deps):
        return {"fixture": "HTTP state-machine only"}

    def produce(deps, job, context, run_id, local_stop, external_stop):
        r = fixture.synthetic_handler(job, context, run_id, local_stop, external_stop).model_dump(
            mode="json"
        )
        r["analytical_outcome"] = "search_exhausted_without_target"
        r["provenance"].update(
            evaluator_version="unit", search_version="unit", solar_version="unit", seed=0
        )
        return r

    def validate(deps, result, local_stop, external_stop):
        return SearchVerdict((), "search_exhausted_without_target", False, False)

    handler = SearchHandler(SearchProvider(resolve, produce, validate, manifest, manifest))
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
        handlers={"search_layouts": handler},
        start_worker=False,
    )
    holder["app"] = app
    with TestClient(
        app, base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"}
    ) as client:
        inp = h.seed(client)
        inp["objective"] = {
            "kind": "minimise_cost_for_target",
            "primary_case_id": "summer",
            "quantity_kind": "geometric",
            "target_gain_m2_h": 1.0,
        }
        scene = h.create(client, inp)
        req = h.request_for(scene)
        req.update(operation="search_layouts", arguments={})
        response = client.post("/api/v1/jobs", json=req)
        assert response.status_code == 202, response.text
        job = response.json()
        assert client.post("/api/v1/jobs", json=req).json() == job
        app.state.run_one()
        finished = client.get("/api/v1/jobs/" + job["job_id"]).json()
        assert finished["status"] == "completed"
        result = client.get("/api/v1/results/" + finished["run_id"]).json()
        assert result["analytical_outcome"] == "search_exhausted_without_target"
        assert client.get("/api/v1/jobs/missing").status_code == 404
        assert client.post("/api/v1/jobs", json={**req, "unexpected": True}).status_code == 422


def test_cancel_during_callback_suppresses_result(tmp_path):
    scene = fixture.scenario()
    scene["input"]["objective"] = {
        "kind": "minimise_cost_for_target",
        "primary_case_id": "case",
        "quantity_kind": "geometric",
        "target_gain_m2_h": 1.0,
    }
    scene = Scenario.model_validate(scene).model_dump(mode="json")
    deps = {"scenario": scene, "profiles": {}}
    hashes = {"site": fixture.HASH}
    store = JobStore(tmp_path / "db")

    def resolve(ref, *, operation):
        return deps, dict(hashes)

    def manifest(deps):
        return {"fixture": "cancel"}

    def produce(deps, job, context, run_id, local_stop, external_stop):
        store.cancel(job.job_id)
        r = fixture.synthetic_handler(job, context, run_id, local_stop, external_stop).model_dump(
            mode="json"
        )
        r["analytical_outcome"] = "search_exhausted_without_target"
        return r

    def validate(deps, result, local_stop, external_stop):
        pytest.fail("validation must not run after cancellation")

    handler = SearchHandler(SearchProvider(resolve, produce, validate, manifest, manifest))
    admitted = {
        **hashes,
        **{
            "execution:" + k: v
            for k, v in handler.execution_hashes(deps, operation="search_layouts").items()
        },
    }
    job = fixture.submit(store, "cancel", operation="search_layouts", hashes=admitted, scene=scene)
    finished = store.run_one({"search_layouts": handler}, threading.Event())
    assert (
        finished.job_id == job.job_id and finished.status == "cancelled" and finished.run_id is None
    )
