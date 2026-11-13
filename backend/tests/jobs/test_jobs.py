"""Synthetic bookkeeping inputs; no physical evaluation or Sheffield evidence."""

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from tree_planner.jobs import JobStore, JobStoreError
from tree_planner.contracts import Result

HASH = "a" * 64


def stamp(seconds=600):
    return (
        (datetime.now(timezone.utc) + timedelta(seconds=seconds))
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def scenario(revision=1):
    return {
        "schema_version": "0.1.0",
        "scenario_id": "synthetic",
        "revision": revision,
        "created_at_utc": "2026-01-01T00:00:00Z",
        "scope": "accepted",
        "base_scenario_ref": None,
        "input": {
            "schema_version": "0.1.0",
            "site_id": "synthetic-site",
            "scene_revision": 1,
            "semantic_revision": 1,
            "profile_library_revision": 1,
            "candidate_catalogue_revision": 1,
            "candidate_catalogue_fingerprint": HASH,
            "display_time_zone": "UTC",
            "target_ids": ["target"],
            "evaluation_cases": [
                {
                    "case_id": "case",
                    "role": "benefit",
                    "profile_state": "mature",
                    "horizon_years": 1,
                    "target_ids": ["target"],
                    "time_bins": [{"midpoint_utc": "2026-07-01T12:00:00Z", "duration_h": 1}],
                    "target_weights": {"target": 1},
                    "source_ids": [],
                    "assumption_ids": ["synthetic"],
                    "area_basis": "surface",
                }
            ],
            "constraints": {
                "budget_pence": 0,
                "budget_basis": "upfront",
                "max_tree_count": 0,
                "accepted_planting_region_ids": [],
                "excluded_region_ids": [],
                "pinned_placements": [],
                "spacing_rules": [],
                "incompatible_candidate_pairs": [],
                "allowed_profile_ids": [],
                "at_most_one_profile_per_location": True,
                "winter_limits": [],
                "survey_requirements": [],
            },
            "objective": {
                "kind": "maximise_shade_under_budget",
                "primary_case_id": "case",
                "quantity_kind": "geometric",
            },
            "numerics": {
                "evaluator": "synthetic",
                "evaluator_version": "v1",
                "spatial_spacing_m": 1,
                "ray_offset_m": 1,
                "intersection_tolerance_m": 0,
                "feasibility_tolerance": 0,
                "solar_algorithm": "synthetic",
                "solar_version": "v1",
                "quadrature": "midpoint",
            },
            "search": {
                "algorithm": "synthetic",
                "version": "v1",
                "seed": 3,
                "comparison_policy": "synthetic",
                "reference_policy": "synthetic",
                "deadline_utc": "2099-01-01T00:00:00Z",
            },
            "assumptions": ["synthetic"],
            "proposed_layout_ref": None,
        },
    }


def request(name, rev=1, operation="evaluate_layout"):
    return {
        "request_id": name,
        "scenario_ref": {"scenario_id": "synthetic", "revision": rev, "scope": "accepted"},
        "operation": operation,
        "arguments": {"layout_ref": {"layout_id": "layout", "revision": 1}}
        if operation == "evaluate_layout"
        else {},
    }


def submit(
    store,
    name,
    *,
    rev=1,
    operation="evaluate_layout",
    deadline="2099-01-01T00:00:00Z",
    hashes=None,
    scene=None,
    connection=None,
):
    return store.submit(
        request(name, rev, operation),
        scene or scenario(rev),
        content_hashes=hashes or {"site": HASH},
        deadline_utc=deadline,
        connection=connection,
    )


def synthetic_handler(job, context, run_id, local_stop, external_stop):
    # The only calculation is an explicitly synthetic integer count, not a physical result.
    count = len(context["identity"]["scenario"]["input"]["target_ids"])
    now = stamp(0)
    obj = {
        "schema_version": "0.1.0",
        "run_id": run_id,
        "source_job_id": job.job_id,
        "scenario_id": job.scenario_id,
        "scenario_revision": job.scenario_revision,
        "scope": job.scope,
        "input_fingerprint": job.input_fingerprint,
        "input_snapshot_ref": context["request"]["scenario_ref"],
        "operation": context["request"]["operation"],
        "arguments": context["request"]["arguments"],
        "analytical_outcome": "comparison_completed",
        "layouts": [],
        "metrics": [],
        "missing_metrics": [],
        "comparison": None,
        "constraints": [],
        "assumptions": [f"synthetic count {count}"],
        "limitations": ["no physical calculation"],
        "source_ids": [],
        "provenance": {
            "tool_version": "test",
            "evaluator_version": "v1",
            "search_version": "v1",
            "solar_version": "v1",
            "schema_version": "0.1.0",
            "seed": 3,
            "created_at_utc": now,
            "compute_started_at_utc": now,
            "compute_finished_at_utc": now,
            "timings_s": {},
            "physics_device": None,
            "inference_device": None,
            "source_hashes": context["identity"]["content_hashes"],
            "execution_mode": "fixture",
        },
    }
    return Result.model_validate(obj)


def run(store):
    return store.run_one({"evaluate_layout": synthetic_handler}, threading.Event())


def test_store_constructs(tmp_path):
    assert JobStore(tmp_path / "jobs.sqlite").get_job("missing") is None


def test_selection_idempotency_cache_and_no_fallback(tmp_path):
    s = JobStore(tmp_path / "db")
    s.activate("synthetic", 1)
    a = submit(s, "a")
    assert submit(s, "a") == a
    assert run(s).status == "completed"
    original = s.read_run(s.get_job(a.job_id).run_id)
    b = submit(s, "b")
    assert b.selection_seq == 2 and s.current("synthetic", 1, "accepted", "evaluation") is None
    assert s.deliver_cached(b.job_id, original.run_id)
    assert s.current("synthetic", 1, "accepted", "evaluation").delivery.source_job_id == a.job_id
    assert (
        s.get_job(b.job_id).delivery.execution_mode == "cached"
        and s.read_run(original.run_id) == original
    )
    c = submit(s, "c")
    s.cancel(c.job_id)
    assert s.current("synthetic", 1, "accepted", "evaluation") is None
    assert submit(s, "a").selection_seq == 1
    with pytest.raises(JobStoreError):
        submit(s, "a", hashes={"site": "b" * 64})
    assert submit(s, "search", operation="search_layouts").selection_seq == 1


def test_concurrent_admission_and_identity(tmp_path):
    s = JobStore(tmp_path / "db", capacity=50)
    barrier = threading.Barrier(12)

    def admit(i):
        barrier.wait()
        return submit(s, str(i))

    with ThreadPoolExecutor(max_workers=12) as pool:
        jobs = list(pool.map(admit, range(12)))
    assert sorted(j.selection_seq for j in jobs) == list(range(1, 13))
    same = threading.Barrier(8)

    def retry(_):
        same.wait()
        return submit(s, "retry")

    with ThreadPoolExecutor(max_workers=8) as pool:
        jobs = list(pool.map(retry, range(8)))
    assert len({j.job_id for j in jobs}) == 1 and jobs[0].selection_seq == 13


def test_deadline_cancel_recovery_and_invalid_result(tmp_path):
    s = JobStore(tmp_path / "db")
    a = submit(s, "a", deadline=stamp(-1))
    assert s.claim() is None
    assert s.get_job(a.job_id).error.code == "DEADLINE_EXCEEDED"
    b = submit(s, "b")
    assert s.claim().job_id == b.job_id
    assert s.cancel(b.job_id)
    assert not s.complete(b.job_id, {})
    assert s.get_job(b.job_id).status == "cancelled"
    c = submit(s, "c")
    s.claim()
    assert not s.complete(c.job_id, {"invalid": "result"})
    assert s.get_job(c.job_id).error.code == "RESULT_VALIDATION_FAILED"
    d = submit(s, "d")
    s.claim()
    with pytest.raises(JobStoreError):
        s.recover_exclusive_startup()
    assert s.recover_exclusive_startup(exclusive=True) == 1
    assert s.get_job(d.job_id).error.code == "WORKER_INTERRUPTED"


def test_transaction_atomicity_and_revision_overflow(tmp_path):
    path = tmp_path / "db"
    s = JobStore(path)
    db = sqlite3.connect(path, isolation_level=None)
    db.execute("BEGIN IMMEDIATE")
    s.activate("synthetic", 1, connection=db)
    submit(s, "rolled-back", connection=db)
    db.rollback()
    db.close()
    assert s.selection("synthetic", 1, "accepted", "evaluation") is None
    with pytest.raises(JobStoreError):
        s.activate("synthetic", 2**63)
    with pytest.raises(JobStoreError):
        submit(s, "bad", rev=2**63)


def test_exact_cache_and_revision_invalidation(tmp_path):
    s = JobStore(tmp_path / "db")
    s.activate("synthetic", 1)
    a = submit(s, "a")
    run(s)
    run_id = s.get_job(a.job_id).run_id
    altered = scenario()
    altered["input"]["constraints"]["budget_pence"] = 1
    b = submit(s, "b", scene=altered)
    with pytest.raises(JobStoreError):
        s.deliver_cached(b.job_id, run_id)
    c = submit(s, "c", rev=2)
    s.activate("synthetic", 2)
    with pytest.raises(JobStoreError):
        s.deliver_cached(c.job_id, run_id)
    assert s.get_job(a.job_id).superseded_by_revision == 2
    assert s.current("synthetic", 1, "accepted", "evaluation") is None


def test_noncooperative_handler_blocks_execution_after_cancel(tmp_path):
    s = JobStore(tmp_path / "db")
    a = submit(s, "a")
    started = threading.Event()
    release = threading.Event()

    def blocked(*args):
        started.set()
        release.wait(5)
        return synthetic_handler(*args)

    thread = threading.Thread(
        target=lambda: s.run_one({"evaluate_layout": blocked}, threading.Event())
    )
    thread.start()
    assert started.wait(2)
    assert s.cancel(a.job_id)
    b = submit(s, "b")
    assert run(s) is None and s.get_job(b.job_id).status == "queued"
    release.set()
    thread.join(3)
    assert not thread.is_alive()
    assert s.get_job(a.job_id).status == "cancelled"
    assert run(s).status == "completed"


def test_out_of_order_cached_delivery_and_late_completion(tmp_path):
    s = JobStore(tmp_path / "db")
    s.activate("synthetic", 1)
    source = submit(s, "source")
    run(s)
    run_id = s.get_job(source.job_id).run_id
    older = submit(s, "older")
    started = threading.Event()
    release = threading.Event()

    def blocked(*args):
        started.set()
        release.wait(5)
        return synthetic_handler(*args)

    thread = threading.Thread(
        target=lambda: s.run_one({"evaluate_layout": blocked}, threading.Event())
    )
    thread.start()
    assert started.wait(2)
    newer = submit(s, "newer")
    assert s.deliver_cached(newer.job_id, run_id)
    release.set()
    thread.join(3)
    assert not thread.is_alive()
    assert s.get_job(older.job_id).status == "completed"
    assert s.current("synthetic", 1, "accepted", "evaluation").job_id == newer.job_id


def test_corrupt_run_rejected_and_unsafe_error_not_exposed(tmp_path):
    path = tmp_path / "db"
    s = JobStore(path)
    a = submit(s, "a")
    run(s)
    run_id = s.get_job(a.job_id).run_id
    with sqlite3.connect(path) as db:
        db.execute("UPDATE job_runs SET result_json='{}' WHERE run_id=?", (run_id,))
    with pytest.raises(JobStoreError):
        s.read_run(run_id)
    b = submit(s, "b")
    assert not s.deliver_cached(b.job_id, run_id)
    assert s.get_job(b.job_id).error.code == "RESULT_VALIDATION_FAILED"
    c = submit(s, "c")

    def fail(*args):
        raise RuntimeError("private exception contents")

    assert s.run_one({"evaluate_layout": fail}, threading.Event()).error.code == "NUMERICAL_FAILURE"
    assert "private exception" not in s.get_job(c.job_id).model_dump_json()


def test_watchdog_expires_and_holds_capacity_until_handler_returns(tmp_path):
    s = JobStore(tmp_path / "db")
    a = submit(s, "a", deadline=stamp(0.4))
    started = threading.Event()
    release = threading.Event()

    def blocked(*args):
        started.set()
        release.wait(5)
        return synthetic_handler(*args)

    thread = threading.Thread(
        target=lambda: s.run_one({"evaluate_layout": blocked}, threading.Event())
    )
    thread.start()
    assert started.wait(2)
    for _ in range(50):
        if s.get_job(a.job_id).status == "failed":
            break
        threading.Event().wait(0.03)
    assert s.get_job(a.job_id).error.code == "DEADLINE_EXCEEDED"
    b = submit(s, "b")
    assert run(s) is None and s.get_job(b.job_id).status == "queued"
    release.set()
    thread.join(3)
    assert not thread.is_alive()
    assert s.get_job(a.job_id).run_id is None


def test_cancel_complete_race_and_progress(tmp_path):
    s = JobStore(tmp_path / "db")
    a = submit(s, "a")
    job = s.claim()
    assert s.update_progress(
        a.job_id, {"completed": 1, "total": 2, "phase": "synthetic", "unit": "items"}
    )
    row = s._read("SELECT * FROM job_records WHERE job_id=?", (a.job_id,))
    import json

    result = synthetic_handler(
        job,
        json.loads(row["request_json"]),
        row["reserved_run_id"],
        threading.Event(),
        threading.Event(),
    )
    barrier = threading.Barrier(2)

    def complete():
        barrier.wait()
        return s.complete(a.job_id, result)

    def cancel():
        barrier.wait()
        return s.cancel(a.job_id)

    with ThreadPoolExecutor(max_workers=2) as pool:
        f1 = pool.submit(complete)
        f2 = pool.submit(cancel)
        values = (f1.result(), f2.result())
    assert sorted(values) == [False, True]
    final = s.get_job(a.job_id)
    assert final.status in ("completed", "cancelled")
    assert (final.run_id is not None) == (final.status == "completed")
    assert not s.update_progress(
        a.job_id, {"completed": 2, "total": 2, "phase": "synthetic", "unit": "items"}
    )


def test_worker_stop_is_truthful(tmp_path):
    from tree_planner.jobs import JobWorker

    s = JobStore(tmp_path / "db")
    submit(s, "a")
    started = threading.Event()
    release = threading.Event()

    def blocked(*args):
        started.set()
        release.wait(5)
        return synthetic_handler(*args)

    worker = JobWorker(s, {"evaluate_layout": blocked}, poll_interval=0.01)
    with pytest.raises(JobStoreError):
        worker.start()
    worker.start(exclusive=True)
    assert started.wait(2)
    assert worker.stop(timeout=0.01) is False
    with pytest.raises(JobStoreError):
        s.recover_exclusive_startup(exclusive=True)
    release.set()
    assert worker.stop(timeout=3) is True


def test_expired_cancel_and_admission_limit(tmp_path):
    s = JobStore(tmp_path / "db", capacity=1)
    a = submit(s, "a", deadline=stamp(-1))
    with pytest.raises(JobStoreError):
        submit(s, "full")
    assert s.cancel(a.job_id)
    assert s.get_job(a.job_id).error.code == "DEADLINE_EXCEEDED"
    assert submit(s, "after").status == "queued"


def test_full_payload_changes_refuse_cache(tmp_path):
    s = JobStore(tmp_path / "db")
    a = submit(s, "a")
    run(s)
    run_id = s.get_job(a.job_id).run_id
    for i, change in enumerate(("seed", "site", "layout")):
        scene = scenario()
        req = request(str(i))
        hashes = {"site": HASH}
        if change == "seed":
            scene["input"]["search"]["seed"] = 4
        if change == "site":
            hashes = {"site": "b" * 64}
        if change == "layout":
            req["arguments"]["layout_ref"]["revision"] = 2
        b = s.submit(req, scene, content_hashes=hashes, deadline_utc="2099-01-01T00:00:00Z")
        with pytest.raises(JobStoreError):
            s.deliver_cached(b.job_id, run_id)


def test_reject_result_identity_mismatch(tmp_path):
    import json

    s = JobStore(tmp_path / "db")
    job = submit(s, "a")
    s.claim()
    row = s._read("SELECT * FROM job_records WHERE job_id=?", (job.job_id,))
    result = synthetic_handler(
        job,
        json.loads(row["request_json"]),
        row["reserved_run_id"],
        threading.Event(),
        threading.Event(),
    ).model_dump(mode="json")
    result["provenance"]["seed"] = 999
    assert not s.complete(job.job_id, result)
    assert s.get_job(job.job_id).error.code == "RESULT_VALIDATION_FAILED"


def test_repository_connection_composes_and_restores_factory(tmp_path):
    from tree_planner.site.repository import Repository

    repo = Repository(tmp_path / "workspace")
    s = JobStore(repo.db_path)
    with repo.transaction() as db:
        assert db.row_factory is None
        s.activate("synthetic", 1, connection=db)
        submit(s, "a", connection=db)
        assert db.row_factory is None
        db.execute("INSERT INTO heads(kind,id,revision) VALUES ('test','test',1)")
    assert s.selection("synthetic", 1, "accepted", "evaluation").selection_seq == 1
    with repo.transaction() as db:
        assert db.execute("SELECT revision FROM heads WHERE kind='test'").fetchone() == (1,)
    with pytest.raises(RuntimeError):
        with repo.transaction() as db:
            submit(s, "rollback", connection=db)
            raise RuntimeError("rollback")
    assert s.selection("synthetic", 1, "accepted", "evaluation").selection_seq == 1


@pytest.mark.parametrize("late", [False, True])
@pytest.mark.parametrize("terminal", ["failed", "cancelled"])
def test_active_context_return_never_promotes_old_job(tmp_path, late, terminal):
    s = JobStore(tmp_path / "db")
    s.activate("synthetic", 1)
    old = submit(s, "old")
    if late:
        job = s.claim()
        row = s._read("SELECT * FROM job_records WHERE job_id=?", (old.job_id,))
        import json

        result = synthetic_handler(
            job,
            json.loads(row["request_json"]),
            row["reserved_run_id"],
            threading.Event(),
            threading.Event(),
        )
    else:
        assert run(s).status == "completed"
        assert s.current("synthetic", 1, "accepted", "evaluation").job_id == old.job_id
    s.activate("other", 1)
    s.activate("synthetic", 1)
    if late:
        assert s.complete(old.job_id, result)
    original = s.read_run(s.get_job(old.job_id).run_id)
    assert s.current("synthetic", 1, "accepted", "evaluation") is None
    newer = submit(s, "newer")
    assert newer.selection_seq == old.selection_seq + 1
    if terminal == "failed":
        s.fail(newer.job_id)
    else:
        s.cancel(newer.job_id)
    assert s.current("synthetic", 1, "accepted", "evaluation") is None
    fresh = submit(s, "fresh")
    assert fresh.selection_seq == newer.selection_seq + 1
    assert s.deliver_cached(fresh.job_id, original.run_id)
    assert s.current("synthetic", 1, "accepted", "evaluation").job_id == fresh.job_id
    assert s.get_job(fresh.job_id).delivery.source_job_id == old.job_id
    assert s.read_run(original.run_id) == original
    assert submit(s, "old").job_id == old.job_id


def test_active_ref_idempotence_and_transaction_rollback(tmp_path):
    from tree_planner.contracts import ScenarioRef

    path = tmp_path / "db"
    s = JobStore(path)
    assert s.active_ref() is None
    s.activate("synthetic", 1)
    assert s.active_ref() == ScenarioRef(scenario_id="synthetic", revision=1, scope="accepted")
    old = submit(s, "old")
    run(s)
    s.activate("synthetic", 1)
    assert s.current("synthetic", 1, "accepted", "evaluation").job_id == old.job_id
    db = sqlite3.connect(path, isolation_level=None)
    db.execute("BEGIN IMMEDIATE")
    s.activate("other", 1, connection=db)
    assert db.row_factory is None
    db.rollback()
    db.close()
    assert s.active_ref().scenario_id == "synthetic"
    assert s.current("synthetic", 1, "accepted", "evaluation").job_id == old.job_id
    s.activate("other", 1)
    s.activate("synthetic", 1)
    reopened = JobStore(path)
    assert reopened.active_ref() == s.active_ref()
    assert reopened.current("synthetic", 1, "accepted", "evaluation") is None
    assert (
        reopened.selection("synthetic", 1, "accepted", "evaluation").accepted_job_id == old.job_id
    )
