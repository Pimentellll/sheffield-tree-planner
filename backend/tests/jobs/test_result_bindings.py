"""Real numerical output exercises job acceptance and legacy cache trust boundaries."""

import copy
import importlib.util
import json
import math
from pathlib import Path
import sqlite3
import sys
from datetime import datetime
from threading import Event

import pytest

from tree_planner.contracts import JobRequest, ScenarioInput
from tree_planner.evaluators import ReferenceInputs, ReferenceJobHandler, ReferenceProvider
from tree_planner.jobs import JobStore, JobStoreError

TESTS = Path(__file__).resolve().parents[1]


def module_at(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# Reuse candidate input fixtures; no review artifact or workstation path imports.
sys.path.insert(0, str(TESTS / "site"))
try:
    site_helpers = module_at("binding_site_helpers", TESTS / "site/test_service.py")
finally:
    sys.path.pop(0)
setup = site_helpers.setup
reference_helpers = module_at(
    "binding_reference_helpers", TESTS / "evaluators/test_reference_http.py"
)
numerical = reference_helpers.numerical


@pytest.fixture
def real_job(setup, numerical):
    svc, site, inp, root = setup
    data = inp.model_dump(mode="json")
    data["search"]["deadline_utc"] = "2099-01-01T00:00:00Z"
    inp = ScenarioInput.model_validate(data)
    jobs = JobStore(svc.repository.db_path)
    scenario = svc.create_accepted(inp, on_accept=jobs.activate)
    request = JobRequest.model_validate(
        dict(
            request_id="real-output",
            scenario_ref=site_helpers.ref(scenario),
            operation="evaluate_layout",
            arguments={"layout_ref": data["proposed_layout_ref"]},
        )
    )
    p = numerical

    def inputs(deps, request):
        case = deps["scenario"]["input"]["evaluation_cases"][0]
        pl = deps["layout"]["placements"][0]
        state = deps["profiles"][pl["profile_id"]]["states"][case["profile_state"]]
        x, y, z = pl["position_enu_m"]
        tree = p.ProposedTree(
            p.OpaqueEllipsoid(
                (x, y, z + state["crown_center_height_m"]), tuple(state["crown_radii_m"])
            ),
            p.OpaqueTrunk(x, y, z, state["trunk_radius_m"], state["trunk_height_m"]),
        )
        bins = tuple(
            p.DraftSolarBin(
                datetime.fromisoformat(b["midpoint_utc"].replace("Z", "+00:00")),
                b["duration_h"],
                (0, -math.sqrt(0.5), math.sqrt(0.5)),
                True,
            )
            for b in case["time_bins"]
        )
        return ReferenceInputs(
            request.scenario_ref,
            deps["layout"]["layout_id"],
            deps["layout"]["revision"],
            pl["placement_id"],
            case["case_id"],
            case["horizon_years"],
            case["target_ids"][0],
            (p.ReceiverSample((0, 0, 0), (0, 0, 1), 2, "target"),),
            bins,
            (),
            tree,
        )

    def resolve(ref, *, operation):
        deps, hashes = svc.resolve_for_job(ref, operation=operation)
        hashes.update(
            {
                "execution:" + k: v
                for k, v in handler.execution_hashes(deps, operation=operation).items()
            }
        )
        return deps, hashes

    provider = ReferenceProvider(
        resolve,
        inputs,
        p.evaluate_one_tree_synthetic,
        "synthetic-test",
        "unit",
        "synthetic-test",
        "unit",
        tuple(reference_helpers.HASHES.items()),
        verify_implementation=lambda: dict(reference_helpers.HASHES),
    )
    handler = ReferenceJobHandler(provider)
    deps, hashes = resolve(site_helpers.ref(scenario), operation="evaluate_layout")
    return jobs, scenario, request, hashes, handler, deps


def pinned_search_diagnostic(setup, numerical):
    """Derive a structural search diagnostic from actual one-tree calculation.

    The generated layout/selection metadata is a control-plane fixture, not
    output from a search producer or proof of physical feasibility.
    """
    from tree_planner.contracts import Layout, SiteBundle
    from tree_planner.site.service import catalogue_fingerprint

    svc, site, inp, root = setup
    placed = (
        svc.get_layout(inp.proposed_layout_ref.layout_id, inp.proposed_layout_ref.revision)
        .placements[0]
        .model_dump(mode="json")
    )
    placed.update(pinned=True, candidate_id="admitted-candidate")
    data = site.model_dump(mode="json")
    data.update(
        semantic_revision=2,
        candidate_catalogue=[
            {
                "candidate_id": placed["candidate_id"],
                "location_id": placed["location_id"],
                "position_enu_m": placed["position_enu_m"],
                "profile_id": placed["profile_id"],
                "plantability_status": "documented_model_region",
                "source_ids": [],
                "assumption_ids": ["explicit synthetic diagnostic catalogue"],
            }
        ],
    )
    provisional = SiteBundle.model_validate(data)
    data["candidate_catalogue_fingerprint"] = catalogue_fingerprint(provisional.candidate_catalogue)
    site = svc.register_site(SiteBundle.model_validate(data))
    pinned_layout = svc.register_layout(
        Layout(
            schema_version="0.1.0",
            layout_id="required-pin",
            revision=1,
            kind="proposed",
            placements=[placed],
        )
    )
    data = inp.model_dump(mode="json")
    data.update(
        semantic_revision=2,
        candidate_catalogue_fingerprint=site.candidate_catalogue_fingerprint,
        proposed_layout_ref={"layout_id": pinned_layout.layout_id, "revision": 1},
    )
    data["constraints"]["pinned_placements"] = [placed]
    inp = ScenarioInput.model_validate(data)
    real = real_job.__wrapped__((svc, site, inp, root), numerical)
    jobs, scenario, request, hashes, handler, _ = real
    submit(real)
    actual = jobs.run_one({"evaluate_layout": handler}, Event())
    assert actual.status == "completed"
    raw = jobs.read_run(actual.run_id).model_dump(mode="json")
    search_req = request.model_dump(mode="json")
    search_req.update(request_id="search-pin", operation="search_layouts", arguments={})
    queued = jobs.submit(
        search_req, scenario, content_hashes=hashes, deadline_utc=scenario.input.search.deadline_utc
    )
    claimed = jobs.claim()
    assert claimed.job_id == queued.job_id
    row = jobs._read("SELECT * FROM job_records WHERE job_id=?", (claimed.job_id,))
    raw.update(
        run_id=row["reserved_run_id"],
        source_job_id=claimed.job_id,
        input_fingerprint=claimed.input_fingerprint,
        operation="search_layouts",
        arguments={},
        analytical_outcome="no_eligible_candidates",
    )
    raw["layouts"][0]["layout"].update(layout_id="generated-search-diagnostic", kind="hypothetical")
    for item in raw["metrics"] + raw["constraints"]:
        item["layout_id"] = "generated-search-diagnostic"
    return jobs, scenario, search_req, hashes, claimed, raw


@pytest.mark.parametrize("rename_pin", [False, True])
@pytest.mark.parametrize("selected_claim", [False, True])
def test_pinned_search_identity_is_required_at_result_admission(
    setup, numerical, rename_pin, selected_claim
):
    jobs, scenario, _, _, claimed, raw = pinned_search_diagnostic(setup, numerical)
    if selected_claim:
        # Intentionally false metadata tests structural admission only.
        raw["analytical_outcome"] = "feasible_candidate"
        raw["layouts"][0].update(feasibility="feasible", selected=True, reasons=[])
        raw["constraints"] = []
    if rename_pin:
        raw["layouts"][0]["layout"]["placements"][0].update(
            placement_id="replacement-tree", pinned=False
        )
    accepted = jobs.complete(claimed.job_id, raw)
    assert accepted is (not rename_pin)
    current = jobs.current(scenario.scenario_id, scenario.revision, scenario.scope, "search")
    if rename_pin:
        assert current is None and jobs.read_run(raw["run_id"]) is None
    else:
        assert current.run_id == raw["run_id"]


def test_pinned_search_legacy_corruption_cannot_be_read_or_delivered_from_cache(setup, numerical):
    jobs, scenario, request, hashes, claimed, raw = pinned_search_diagnostic(setup, numerical)
    assert jobs.complete(claimed.job_id, raw)
    assert jobs.read_run(raw["run_id"]) is not None
    raw["layouts"][0]["layout"]["placements"][0].update(
        placement_id="replacement-tree", pinned=False
    )
    with sqlite3.connect(jobs.db_path) as db:
        db.execute(
            "UPDATE job_runs SET result_json=? WHERE run_id=?", (json.dumps(raw), raw["run_id"])
        )
    with pytest.raises(JobStoreError, match="stored result failed validation"):
        jobs.read_run(raw["run_id"])
    request["request_id"] += "-cached"
    cached = jobs.submit(
        request, scenario, content_hashes=hashes, deadline_utc=scenario.input.search.deadline_utc
    )
    assert jobs.deliver_cached(cached.job_id, raw["run_id"]) is False
    assert jobs.get_job(cached.job_id).status == "failed"
    assert jobs.current(scenario.scenario_id, scenario.revision, scenario.scope, "search") is None


CORRUPTIONS = (
    "nested_scope",
    "layout_revision",
    "layout_content",
    "metric_case",
    "metric_target",
    "metric_horizon",
    "constraint_case",
    "missing_case",
    "source",
)


def corrupt(raw, mutation):
    raw = copy.deepcopy(raw)
    if mutation == "nested_scope":
        for item in raw["layouts"] + raw["metrics"] + raw["constraints"]:
            item["scenario_ref"].update(scope="hypothetical", scenario_id="unresolved-other")
    elif mutation == "layout_revision":
        raw["layouts"][0]["layout"]["revision"] = 999
    elif mutation == "layout_content":
        raw["layouts"][0]["layout"]["placements"][0]["position_enu_m"][0] += 1
    elif mutation == "metric_case":
        raw["metrics"][0]["case_id"] = "unknown-case"
    elif mutation == "metric_target":
        raw["metrics"][0]["target_id"] = "unknown-target"
    elif mutation == "metric_horizon":
        raw["metrics"][0]["horizon_years"] = 999
    elif mutation == "constraint_case":
        raw["constraints"][0]["case_id"] = "unknown-case"
    elif mutation == "missing_case":
        m = raw["metrics"][0]
        raw["missing_metrics"] = [
            dict(
                scenario_ref=m["scenario_ref"],
                layout_id=m["layout_id"],
                case_id="unknown-case",
                metric_id=m["metric_id"],
                reason="not computed",
            )
        ]
    elif mutation == "source":
        raw["source_ids"] = ["unregistered-narrative-source"]
    return raw


def submit(real_job, suffix=""):
    jobs, scenario, request, hashes, handler, deps = real_job
    raw = request.model_dump(mode="json")
    raw["request_id"] += suffix
    return jobs.submit(
        raw, scenario, content_hashes=hashes, deadline_utc=scenario.input.search.deadline_utc
    )


def test_valid_real_output_and_cache_preserve_origin(real_job):
    jobs, scenario, request, hashes, handler, deps = real_job
    job = submit(real_job)
    originals = []

    def capture(*args):
        result = handler(*args)
        originals.append(result)
        return result

    outcome = jobs.run_one({"evaluate_layout": capture}, Event())
    assert outcome.status == "completed"
    original = jobs.read_run(outcome.run_id)
    assert original == originals[0]
    assert original.metrics[0].value == pytest.approx(2.0)
    cached = submit(real_job, "-cache")
    assert jobs.deliver_cached(cached.job_id, original.run_id)
    current = jobs.current(scenario.scenario_id, scenario.revision, scenario.scope, "evaluation")
    assert current.job_id == cached.job_id
    assert current.delivery.execution_mode == "cached"
    assert current.delivery.source_job_id == job.job_id
    assert jobs.read_run(original.run_id) == original


@pytest.mark.parametrize("mutation", CORRUPTIONS)
def test_reject_corrupted_real_output_before_persistence(real_job, mutation):
    jobs, scenario, request, hashes, handler, deps = real_job
    job = submit(real_job)
    originals = []

    def broken(*args):
        raw = handler(*args).model_dump(mode="json")
        originals.append(raw)
        return corrupt(raw, mutation)

    outcome = jobs.run_one({"evaluate_layout": broken}, Event())
    assert originals, "must reach actual numerical output"
    assert outcome.status == "failed" and outcome.error.code == "RESULT_VALIDATION_FAILED"
    assert (
        jobs.current(scenario.scenario_id, scenario.revision, scenario.scope, "evaluation") is None
    )
    assert jobs._read("SELECT count(*) FROM job_runs")[0] == 0
    assert jobs.get_job(job.job_id).run_id is None


@pytest.mark.parametrize("mutation", CORRUPTIONS)
def test_legacy_nested_corruption_rejected_on_read_current_and_cache(real_job, mutation):
    jobs, scenario, request, hashes, handler, deps = real_job
    job = submit(real_job)
    outcome = jobs.run_one({"evaluate_layout": handler}, Event())
    assert outcome.status == "completed"
    original = jobs.read_run(outcome.run_id)
    with sqlite3.connect(jobs.db_path) as db:
        db.execute(
            "UPDATE job_runs SET result_json=? WHERE run_id=?",
            (json.dumps(corrupt(original.model_dump(mode="json"), mutation)), original.run_id),
        )
    reopened = JobStore(jobs.db_path)
    with pytest.raises(JobStoreError):
        reopened.read_run(original.run_id)
    with pytest.raises(JobStoreError):
        reopened.current(scenario.scenario_id, scenario.revision, scenario.scope, "evaluation")
    cached = submit(real_job, "-cache")
    assert not reopened.deliver_cached(cached.job_id, original.run_id)
    assert reopened.get_job(cached.job_id).error.code == "RESULT_VALIDATION_FAILED"
    assert (
        reopened.current(scenario.scenario_id, scenario.revision, scenario.scope, "evaluation")
        is None
    )
    assert reopened.get_job(job.job_id).run_id == original.run_id


def test_missing_admitted_layout_hash_fails_closed(real_job):
    jobs, scenario, request, hashes, handler, deps = real_job
    hashes.pop("layout")
    submit(real_job)
    # The handler itself correctly refuses incomplete execution context. Directly
    # exercise the store boundary with a real Result captured before that omission.
    row = jobs._read("SELECT * FROM job_records")
    job = jobs.claim()
    from tree_planner.canonical import content_hash

    context = json.loads(row["request_json"])
    context["identity"]["content_hashes"]["layout"] = content_hash(deps["layout"])
    valid_job = job.model_copy(update={"input_fingerprint": content_hash(context["identity"])})
    raw = handler(valid_job, context, row["reserved_run_id"], Event(), Event()).model_dump(
        mode="json"
    )
    raw["input_fingerprint"] = job.input_fingerprint
    raw["provenance"]["source_hashes"] = hashes
    assert not jobs.complete(job.job_id, raw)
    assert jobs.get_job(job.job_id).error.code == "RESULT_VALIDATION_FAILED"


@pytest.mark.parametrize(
    "mutation", ["none", "profile", "tree_identity", "other_coordinate", "same_layout_identity"]
)
def test_relocation_binds_only_the_requested_move(real_job, mutation):
    # Identity-only check, reusing real output structure; this does not evaluate
    # the relocated tree or assert any counterfactual numerical value.
    from tree_planner.contracts import Result
    from tree_planner.jobs import _validate_bindings

    jobs, scenario, request, hashes, handler, deps = real_job
    submit(real_job)
    job = jobs.claim()
    row = jobs._read("SELECT * FROM job_records")
    context = json.loads(row["request_json"])
    raw = handler(job, context, row["reserved_run_id"], Event(), Event()).model_dump(mode="json")
    identity = copy.deepcopy(context["identity"])
    identity["operation"] = raw["operation"] = "compare_locations"
    identity["arguments"] = raw["arguments"] = dict(
        layout_ref=request.root.arguments.layout_ref.model_dump(mode="json"),
        placement_id=deps["layout"]["placements"][0]["placement_id"],
        alternative_position_enu_m=[2.0, 0.0, 0.0],
    )
    original_id = raw["layouts"][0]["layout"]["layout_id"]
    layout = raw["layouts"][0]["layout"]
    layout.update(layout_id="relocated", kind="hypothetical")
    layout["placements"][0]["position_enu_m"] = [2.0, 0.0, 0.0]
    for item in raw["metrics"] + raw["constraints"]:
        item["layout_id"] = "relocated"
    if mutation == "profile":
        layout["placements"][0]["profile_id"] = "unrequested-profile"
    if mutation == "tree_identity":
        layout["placements"][0]["placement_id"] = "another-tree"
    if mutation == "other_coordinate":
        layout["placements"][0]["position_enu_m"][1] = 1
    if mutation == "same_layout_identity":
        layout["layout_id"] = original_id
        for item in raw["metrics"] + raw["constraints"]:
            item["layout_id"] = original_id
    result = Result.model_validate(raw)
    db = jobs._connect()
    try:
        if mutation == "none":
            _validate_bindings(db, result, identity)
        else:
            with pytest.raises(ValueError):
                _validate_bindings(db, result, identity)
    finally:
        db.close()


@pytest.mark.parametrize("missing_context", [False, True])
def test_result_sources_require_the_admitted_manifest(real_job, missing_context):
    jobs, scenario, request, hashes, handler, deps = real_job
    submit(real_job)
    job = jobs.claim()
    row = jobs._read("SELECT * FROM job_records")
    raw = handler(
        job, json.loads(row["request_json"]), row["reserved_run_id"], Event(), Event()
    ).model_dump(mode="json")
    raw["source_ids"] = [deps["site"]["rights"][0]["source_id"]]
    if missing_context:
        with sqlite3.connect(jobs.db_path) as db:
            db.execute("DELETE FROM snapshots WHERE kind='typed_site'")
    assert jobs.complete(job.job_id, raw) is (not missing_context)
    if missing_context:
        assert jobs.get_job(job.job_id).error.code == "RESULT_VALIDATION_FAILED"
    else:
        assert jobs.read_run(raw["run_id"]).source_ids == tuple(raw["source_ids"])
