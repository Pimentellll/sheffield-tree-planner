"""Actual synthetic producers through HTTP jobs; no authored successful results."""

from copy import deepcopy

from fastapi.testclient import TestClient
import pytest

from tree_planner.evaluators.physical_runtime import create_physical_runtime


def execute(runtime, client, operation, arguments, request_id):
    response = client.post(
        "/api/v1/jobs",
        json={
            "request_id": request_id,
            "scenario_ref": runtime.scenario_ref.model_dump(mode="json"),
            "operation": operation,
            "arguments": arguments,
        },
    )
    assert response.status_code == 202, response.text
    job = response.json()
    runtime.app.state.run_one()
    job = client.get("/api/v1/jobs/" + job["job_id"]).json()
    assert job["status"] == "completed", job
    result = client.get("/api/v1/results/" + job["run_id"])
    assert result.status_code == 200, result.text
    return job, result.json()


def test_actual_evaluation_search_and_controlled_relocation(tmp_path):
    runtime = create_physical_runtime(tmp_path, start_worker=False)
    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        health = client.get("/api/v1/health").json()
        assert {"evaluate_layout", "search_layouts", "compare_locations"} <= set(
            health["available_operations"]
        )
        layout = runtime.app.state.scenarios.get_scenario(
            runtime.scenario_ref
        ).input.proposed_layout_ref
        job, result = execute(
            runtime,
            client,
            "evaluate_layout",
            {"layout_ref": layout.model_dump(mode="json")},
            "evaluate",
        )
        gain = next(
            m
            for m in result["metrics"]
            if m["metric_id"] == "additional_shade"
            and m["target_id"] is None
            and m["case_id"] == "summer"
        )
        assert gain["value"] > 0
        assert result["provenance"]["execution_mode"] == "live"
        assert result["input_fingerprint"] == job["input_fingerprint"]
        assert all(m["metric_instance_id"].startswith(job["run_id"]) for m in result["metrics"])
        _, search = execute(runtime, client, "search_layouts", {}, "search")
        assert search["analytical_outcome"] == "feasible_candidate"
        assert any(e["role"] == "reference" for e in search["layouts"])
        selected = [e for e in search["layouts"] if e["selected"]]
        assert selected and all(e["feasibility"] == "feasible" for e in selected)
        assert any(c["status"] == "unknown" for c in search["constraints"])
        _, moved = execute(
            runtime,
            client,
            "compare_locations",
            {
                "layout_ref": layout.model_dump(mode="json"),
                "placement_id": "tree-1",
                "alternative_position_enu_m": [100, 0, 0],
            },
            "relocate",
        )
        assert moved["analytical_outcome"] == "comparison_completed"
        assert any(e["feasibility"] == "infeasible" for e in moved["layouts"])
        assert moved["comparison"]["changed_inputs"] == ["placements.tree-1.position_enu_m"]
        metrics = {m["metric_instance_id"]: m for m in moved["metrics"]}
        for d in moved["comparison"]["deltas"]:
            assert d["value"] == pytest.approx(
                metrics[d["alternative_metric_instance_id"]]["value"]
                - metrics[d["base_metric_instance_id"]]["value"]
            )


def test_changed_registered_source_fails_closed_then_recovers(tmp_path):
    runtime = create_physical_runtime(tmp_path, start_worker=False)
    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        layout = runtime.app.state.scenarios.get_scenario(
            runtime.scenario_ref
        ).input.proposed_layout_ref
        payload = {
            "request_id": "admitted",
            "scenario_ref": runtime.scenario_ref.model_dump(mode="json"),
            "operation": "evaluate_layout",
            "arguments": {"layout_ref": layout.model_dump(mode="json")},
        }
        response = client.post("/api/v1/jobs", json=payload)
        assert response.status_code == 202
        source = runtime.scene_path.read_bytes()
        runtime.scene_path.write_bytes(source + b" ")
        runtime.app.state.run_one()
        failed = client.get("/api/v1/jobs/" + response.json()["job_id"]).json()
        assert failed["status"] == "failed" and failed["run_id"] is None
        runtime.scene_path.write_bytes(source)
        payload["request_id"] = "recovery"
        _, result = execute(runtime, client, "evaluate_layout", payload["arguments"], "recovery")
        assert result["metrics"]


def test_zero_empty_layout_and_old_selection_stales(tmp_path):
    runtime = create_physical_runtime(tmp_path, start_worker=False)
    service = runtime.app.state.service
    scenario = service.scenarios.get_scenario(runtime.scenario_ref)
    original_layout = service.scenarios.get_layout(scenario.input.proposed_layout_ref.layout_id, 1)
    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        old, _ = execute(
            runtime,
            client,
            "evaluate_layout",
            {"layout_ref": scenario.input.proposed_layout_ref.model_dump(mode="json")},
            "old",
        )
        data = original_layout.model_dump(mode="json")
        data.update(layout_id="empty", placements=[])
        assert client.post("/api/v1/layouts", json=data).status_code == 201
        inp = deepcopy(scenario.input.model_dump(mode="json"))
        inp["proposed_layout_ref"] = {"layout_id": "empty", "revision": 1}
        response = client.put(
            "/api/v1/scenarios/" + scenario.scenario_id, headers={"If-Match": '"1"'}, json=inp
        )
        assert response.status_code == 200, response.text
        from tree_planner.contracts import ScenarioRef

        runtime.scenario_ref = ScenarioRef(
            scenario_id=scenario.scenario_id, revision=2, scope="accepted"
        )
        _, result = execute(
            runtime, client, "evaluate_layout", {"layout_ref": inp["proposed_layout_ref"]}, "zero"
        )
        assert all(m["value"] == 0 for m in result["metrics"])
        assert client.get("/api/v1/jobs/" + old["job_id"]).json()["superseded_by_revision"] == 2


@pytest.mark.parametrize("mode", ["fixed_layout", "redesign"])
def test_two_scenario_comparison_binds_alternative_and_constraint_diagnostics(tmp_path, mode):
    runtime = create_physical_runtime(tmp_path, start_worker=False)
    service = runtime.app.state.service
    base = service.scenarios.get_scenario(runtime.scenario_ref)
    data = deepcopy(base.input.model_dump(mode="json"))
    data["constraints"]["budget_pence"] = 0
    from tree_planner.contracts import ScenarioInput, ScenarioRef

    alternative = service.scenarios.prepare_scenario(
        ScenarioInput.model_validate(data), base_ref=runtime.scenario_ref
    )
    alt_ref = ScenarioRef(
        scenario_id=alternative.scenario_id, revision=alternative.revision, scope=alternative.scope
    )
    arguments = dict(
        base_scenario_ref=runtime.scenario_ref.model_dump(mode="json"),
        alternative_scenario_ref=alt_ref.model_dump(mode="json"),
        layout_refs=[base.input.proposed_layout_ref.model_dump(mode="json")],
        mode=mode,
    )
    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        _, result = execute(runtime, client, "compare_scenarios", arguments, mode)
        assert result["comparison"]["mode"] == mode
        assert "constraints.budget_pence" in result["comparison"]["changed_inputs"]
        assert {e["scenario_ref"]["scenario_id"] for e in result["layouts"]} == {
            base.scenario_id,
            alternative.scenario_id,
        }
        if mode == "fixed_layout":
            assert any(e["feasibility"] == "infeasible" for e in result["layouts"])
        else:
            assert any(e["tree_count"] == 0 for e in result["layouts"])
        assert result["comparison"]["deltas"]


@pytest.mark.parametrize(
    "mutation", ["imported_alias", "bound_callback", "keyword_default", "constant"]
)
def test_loaded_numerical_mutations_are_fenced(tmp_path, monkeypatch, mutation):
    runtime = create_physical_runtime(tmp_path, start_worker=False)
    from tree_planner.physics import evaluator, ray

    if mutation == "imported_alias":
        monkeypatch.setattr(evaluator, "solar_direction_enu", lambda *a, **k: (0, 0, -1))
    elif mutation == "bound_callback":
        monkeypatch.setattr(runtime.handler, "compute", lambda *a, **k: {})
    elif mutation == "keyword_default":
        monkeypatch.setitem(ray.ray_triangle_distance.__kwdefaults__, "min_distance", 1)
    else:
        monkeypatch.setattr(evaluator, "SOLAR_VERSION", "unverified")
    with pytest.raises(ValueError, match="changed"):
        runtime.handler._manifest()


def test_winter_checks_zero_planting_and_cancel_deadline(tmp_path):
    runtime = create_physical_runtime(tmp_path, start_worker=False, winter=True)
    service = runtime.app.state.service
    scenario = service.scenarios.get_scenario(runtime.scenario_ref)
    from tree_planner.contracts import JobRequest, ScenarioInput, ScenarioRef

    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        _, result = execute(
            runtime,
            client,
            "evaluate_layout",
            {"layout_ref": scenario.input.proposed_layout_ref.model_dump(mode="json")},
            "winter-evaluate",
        )
        assert any(
            m["metric_id"] == "winter_sun_loss" and m["value"] > 0 for m in result["metrics"]
        )
        data = scenario.input.model_dump(mode="json")
        data["constraints"]["winter_limits"][0]["maximum_loss_m2_h"] = 0
        changed = service.replace_accepted(
            scenario.scenario_id, ScenarioInput.model_validate(data), 1
        )
        runtime.scenario_ref = ScenarioRef(
            scenario_id=changed.scenario_id, revision=2, scope="accepted"
        )
        _, result = execute(runtime, client, "search_layouts", {}, "winter-constrained")
        assert all(e["tree_count"] == 0 for e in result["layouts"] if e["selected"])
        q = dict(
            request_id="cancel",
            scenario_ref=runtime.scenario_ref.model_dump(mode="json"),
            operation="search_layouts",
            arguments={},
        )
        j = client.post("/api/v1/jobs", json=q).json()
        cancelled = client.post("/api/v1/jobs/" + j["job_id"] + "/cancel").json()
        assert cancelled["status"] == "cancelled" and cancelled["run_id"] is None
        data["search"]["deadline_utc"] = "2000-01-01T00:00:00Z"
        changed = service.replace_accepted(
            scenario.scenario_id, ScenarioInput.model_validate(data), 2
        )
        runtime.scenario_ref = ScenarioRef(
            scenario_id=changed.scenario_id, revision=3, scope="accepted"
        )
        q.update(request_id="expired", scenario_ref=runtime.scenario_ref.model_dump(mode="json"))
        j = service.submit(JobRequest.model_validate(q))
        service.run_one()
        expired = service.jobs.get_job(j.job_id)
        assert (
            expired.status == "failed"
            and expired.error.code == "DEADLINE_EXCEEDED"
            and expired.run_id is None
        )


def test_actual_cache_delivery_retains_original_computation(tmp_path):
    runtime = create_physical_runtime(tmp_path, start_worker=False)
    service = runtime.app.state.service
    scenario = service.scenarios.get_scenario(runtime.scenario_ref)
    args = {"layout_ref": scenario.input.proposed_layout_ref.model_dump(mode="json")}
    from tree_planner.contracts import JobRequest

    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        original, result = execute(runtime, client, "evaluate_layout", args, "source")
        q = JobRequest.model_validate(
            dict(
                request_id="cache",
                scenario_ref=runtime.scenario_ref,
                operation="evaluate_layout",
                arguments=args,
            )
        )
        requesting = service.submit(q)
        service.jobs.deliver_cached(requesting.job_id, original["run_id"])
        cached = client.get("/api/v1/jobs/" + requesting.job_id).json()
        assert cached["delivery"]["execution_mode"] == "cached"
        assert cached["delivery"]["source_job_id"] == original["job_id"]
        assert client.get("/api/v1/results/" + original["run_id"]).json() == result


def test_cache_rechecks_registered_source_after_admission(tmp_path):
    runtime = create_physical_runtime(tmp_path, start_worker=False)
    service = runtime.app.state.service
    scenario = service.scenarios.get_scenario(runtime.scenario_ref)
    args = {"layout_ref": scenario.input.proposed_layout_ref.model_dump(mode="json")}
    from tree_planner.contracts import JobRequest

    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        original, _ = execute(runtime, client, "evaluate_layout", args, "source")
        requesting = service.submit(
            JobRequest.model_validate(
                dict(
                    request_id="cache",
                    scenario_ref=runtime.scenario_ref,
                    operation="evaluate_layout",
                    arguments=args,
                )
            )
        )
        source = runtime.scene_path.read_bytes()
        try:
            runtime.scene_path.write_bytes(source + b" ")
            assert service.jobs.deliver_cached(requesting.job_id, original["run_id"]) is False
            assert service.jobs.get_job(requesting.job_id).status == "failed"
        finally:
            runtime.scene_path.write_bytes(source)


def test_result_delta_tampering_rejected(tmp_path):
    runtime = create_physical_runtime(tmp_path, start_worker=False)
    scenario = runtime.app.state.scenarios.get_scenario(runtime.scenario_ref)
    from tree_planner.contracts import Result

    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        _, result = execute(
            runtime,
            client,
            "compare_locations",
            dict(
                layout_ref=scenario.input.proposed_layout_ref.model_dump(mode="json"),
                placement_id="tree-1",
                alternative_position_enu_m=[100, 0, 0],
            ),
            "delta",
        )
    result["comparison"]["deltas"][0]["value"] += 1
    with pytest.raises(ValueError):
        Result.model_validate(result)


@pytest.mark.parametrize(
    "corruption",
    [
        "arithmetic",
        "mode",
        "hidden_changes",
        "missing_alternative",
        "forged_feasible",
        "missing_sources",
    ],
)
def test_stored_comparison_corruption_rejected_on_read_and_cache(tmp_path, corruption):
    import json
    from tree_planner.contracts import JobRequest, ScenarioInput, ScenarioRef, Result
    from tree_planner.jobs import _validate_bindings

    runtime = create_physical_runtime(tmp_path, start_worker=False)
    service = runtime.app.state.service
    base = service.scenarios.get_scenario(runtime.scenario_ref)
    data = base.input.model_dump(mode="json")
    data["constraints"]["budget_pence"] = 0
    alt = service.scenarios.prepare_scenario(
        ScenarioInput.model_validate(data), base_ref=runtime.scenario_ref
    )
    args = dict(
        base_scenario_ref=runtime.scenario_ref.model_dump(mode="json"),
        alternative_scenario_ref=ScenarioRef(
            scenario_id=alt.scenario_id, revision=1, scope="hypothetical"
        ).model_dump(mode="json"),
        layout_refs=[base.input.proposed_layout_ref.model_dump(mode="json")],
        mode="fixed_layout",
    )
    with TestClient(
        runtime.app, base_url="http://127.0.0.1", headers={"Origin": "http://127.0.0.1"}
    ) as client:
        _, result = execute(runtime, client, "compare_scenarios", args, "source")
        requesting = service.submit(
            JobRequest.model_validate(
                dict(
                    request_id="cache",
                    scenario_ref=runtime.scenario_ref,
                    operation="compare_scenarios",
                    arguments=args,
                )
            )
        )
        if corruption == "arithmetic":
            result["comparison"]["deltas"][0]["value"] += 1
        elif corruption == "mode":
            result["comparison"]["mode"] = "redesign"
        elif corruption == "hidden_changes":
            result["comparison"]["changed_inputs"] = []
            for d in result["comparison"]["deltas"]:
                d["changed_inputs"] = []
        elif corruption == "missing_alternative":
            result["metrics"] = [
                m for m in result["metrics"] if m["scenario_ref"]["scope"] == "accepted"
            ]
            result["comparison"]["deltas"] = []
        elif corruption == "missing_sources":
            result["source_ids"] = []
        else:
            for entry in result["layouts"]:
                if entry["scenario_ref"]["scope"] == "hypothetical":
                    entry.update(feasibility="feasible", reasons=[])
            result["constraints"] = [
                c for c in result["constraints"] if c["scenario_ref"]["scope"] == "accepted"
            ]
        with service.repository.transaction() as db:
            identity = json.loads(
                db.execute(
                    "SELECT identity_json FROM job_runs WHERE run_id=?", (result["run_id"],)
                ).fetchone()[0]
            )
            with pytest.raises(ValueError):
                typed = Result.model_validate(result)
                _validate_bindings(db, typed, identity)
            db.execute(
                "UPDATE job_runs SET result_json=? WHERE run_id=?",
                (json.dumps(result), result["run_id"]),
            )
        assert client.get("/api/v1/results/" + result["run_id"]).status_code == 503
        assert service.jobs.deliver_cached(requesting.job_id, result["run_id"]) is False
        assert service.jobs.get_job(requesting.job_id).status == "failed"
