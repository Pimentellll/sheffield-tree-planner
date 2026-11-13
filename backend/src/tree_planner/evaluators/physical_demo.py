"""Actual loopback HTTP/job/CPU proof; retain failures and always stop owned server."""

import argparse
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import socket
from threading import Thread
from time import monotonic, sleep

import httpx
import uvicorn

from tree_planner.contracts import Result, ScenarioRef
from .physical_runtime import create_physical_runtime


def run(output):
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    evidence = dict(
        scope="Authored synthetic geometry; actual SPA/CPU calculations; no Sheffield/model/human acceptance",
        status="running",
        http=[],
        phases=[],
        started_at_utc=datetime.now(timezone.utc).isoformat(),
    )
    server = thread = sock = runtime = None

    def require(condition, message):
        if not condition:
            raise RuntimeError(message)

    try:
        runtime = create_physical_runtime(output / "runtime", winter=True)
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        base = f"http://127.0.0.1:{sock.getsockname()[1]}"
        evidence["base_url"] = base
        server = uvicorn.Server(uvicorn.Config(runtime.app, log_level="warning", access_log=False))
        thread = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=False)
        thread.start()
        deadline = monotonic() + 30
        while not server.started:
            require(thread.is_alive() and monotonic() < deadline, "Owned server failed to start")
            sleep(0.02)
        with httpx.Client(
            base_url=base, headers={"Origin": base}, timeout=15, trust_env=False
        ) as client:

            def call(method, path, *, expected=200, **kwargs):
                response = client.request(method, path, **kwargs)
                body = response.json()
                evidence["http"].append(
                    dict(method=method, path=path, status=response.status_code, body=body)
                )
                require(
                    response.status_code == expected,
                    f"HTTP {method} {path}: {response.status_code}",
                )
                return body

            def submit(name, operation, arguments, *, ref=None):
                return call(
                    "POST",
                    "/api/v1/jobs",
                    expected=202,
                    json=dict(
                        request_id=name,
                        scenario_ref=(ref or runtime.scenario_ref).model_dump(mode="json"),
                        operation=operation,
                        arguments=arguments,
                    ),
                )

            def poll(job):
                deadline = monotonic() + 60
                while True:
                    job = call("GET", "/api/v1/jobs/" + job["job_id"])
                    if job["status"] in {"completed", "failed", "cancelled"}:
                        return job
                    require(
                        monotonic() < deadline,
                        "Job did not terminate within evidence capture deadline",
                    )
                    sleep(0.03)

            def result(job):
                job = poll(job)
                require(job["status"] == "completed", "Numerical job did not complete")
                value = call("GET", "/api/v1/results/" + job["run_id"])
                parsed = Result.model_validate(value)
                require(
                    parsed.input_fingerprint == job["input_fingerprint"],
                    "Result/job identity differs",
                )
                return job, value

            health = call("GET", "/api/v1/health")
            require(
                set(health["available_operations"])
                == {"evaluate_layout", "search_layouts", "compare_locations", "compare_scenarios"},
                "Capability advertisement differs from implemented runtime",
            )
            scenario = call(
                "GET", f"/api/v1/scenarios/{runtime.scenario_ref.scenario_id}?revision=1"
            )
            evidence["initial_scenario"] = deepcopy(scenario)
            layout_ref = scenario["input"]["proposed_layout_ref"]
            first_job, first = result(
                submit("evaluate", "evaluate_layout", dict(layout_ref=layout_ref))
            )
            require(
                any(
                    m["metric_id"] == "additional_shade"
                    and m["case_id"] == "summer"
                    and m["value"] > 0
                    for m in first["metrics"]
                ),
                "Positive summer computation missing",
            )
            search_job, search = result(submit("search", "search_layouts", {}))
            require(
                any(e["selected"] and e["feasibility"] == "feasible" for e in search["layouts"]),
                "No independently checked search selection",
            )
            moved_job, moved = result(
                submit(
                    "relocate",
                    "compare_locations",
                    dict(
                        layout_ref=layout_ref,
                        placement_id="tree-1",
                        alternative_position_enu_m=[100, 0, 0],
                    ),
                )
            )
            require(
                any(e["feasibility"] == "infeasible" for e in moved["layouts"]),
                "Requested infeasible alternative was concealed",
            )
            evidence["phases"].extend(
                [
                    dict(name="evaluate", job=first_job, result=first),
                    dict(name="search", job=search_job, result=search),
                    dict(name="relocate", job=moved_job, result=moved),
                ]
            )

            changed = deepcopy(scenario["input"])
            changed["constraints"]["budget_pence"] = 0
            alternative = call(
                "POST",
                "/api/v1/operations",
                json=dict(
                    request_id="prepare",
                    operation="prepare_scenario",
                    arguments=dict(
                        base_scenario_ref=runtime.scenario_ref.model_dump(mode="json"),
                        proposed_edits=changed,
                    ),
                ),
            )
            alt_ref = {k: alternative[k] for k in ("scenario_id", "revision", "scope")}
            for mode in ("fixed_layout", "redesign"):
                args = dict(
                    base_scenario_ref=runtime.scenario_ref.model_dump(mode="json"),
                    alternative_scenario_ref=alt_ref,
                    layout_refs=[layout_ref],
                    mode=mode,
                )
                job, value = result(submit(mode, "compare_scenarios", args))
                require(
                    value["comparison"]["mode"] == mode
                    and "constraints.budget_pence" in value["comparison"]["changed_inputs"],
                    "Controlled comparison metadata mismatch",
                )
                evidence["phases"].append(dict(name=mode, job=job, result=value))

            # An unchanged same-revision request can receive the immutable source run.
            cached = submit("cache", "evaluate_layout", dict(layout_ref=layout_ref))
            # The running background worker could claim it; use a fresh manual runtime
            # in tests for deterministic controller-level cache proof instead of racing.
            cached_job, cached_result = result(cached)
            evidence["phases"].append(
                dict(name="repeat-live", job=cached_job, result=cached_result)
            )
            cancelled = submit("cancel", "search_layouts", {})
            call("POST", "/api/v1/jobs/" + cancelled["job_id"] + "/cancel")
            cancelled = poll(cancelled)
            require(
                cancelled["status"] == "cancelled" and cancelled["run_id"] is None,
                "Cancellation produced a final result",
            )
            evidence["phases"].append(dict(name="cancel", job=cancelled))

            # Corrupt only this owned registered input, prove admission fails, restore exact bytes.
            original_bytes = runtime.scene_path.read_bytes()
            try:
                runtime.scene_path.write_bytes(original_bytes + b" ")
                failed = call(
                    "POST",
                    "/api/v1/jobs",
                    expected=409,
                    json=dict(
                        request_id="bad-source",
                        scenario_ref=runtime.scenario_ref.model_dump(mode="json"),
                        operation="evaluate_layout",
                        arguments=dict(layout_ref=layout_ref),
                    ),
                )
                evidence["phases"].append(dict(name="source-failure", error=failed))
            finally:
                runtime.scene_path.write_bytes(original_bytes)
            recovery_job, recovery = result(
                submit("recover", "evaluate_layout", dict(layout_ref=layout_ref))
            )
            evidence["phases"].append(dict(name="recovery", job=recovery_job, result=recovery))

            empty = call("GET", "/api/v1/layouts/one-tree?revision=1")
            empty.update(layout_id="zero", placements=[])
            call("POST", "/api/v1/layouts", expected=201, json=empty)
            new_input = deepcopy(scenario["input"])
            new_input["proposed_layout_ref"] = dict(layout_id="zero", revision=1)
            newer = call(
                "PUT",
                "/api/v1/scenarios/" + runtime.scenario_ref.scenario_id,
                headers={"If-Match": '"1"'},
                json=new_input,
            )
            runtime.scenario_ref = ScenarioRef(
                **{k: newer[k] for k in ("scenario_id", "revision", "scope")}
            )
            zero_job, zero = result(
                submit("zero", "evaluate_layout", dict(layout_ref=new_input["proposed_layout_ref"]))
            )
            require(
                all(m["value"] == 0 for m in zero["metrics"]),
                "Empty layout did not compute valid zero",
            )
            stale = call("GET", "/api/v1/jobs/" + first_job["job_id"])
            require(
                stale["superseded_by_revision"] == 2,
                "Old result remained current after accepted edit",
            )
            evidence["phases"].extend(
                [dict(name="zero", job=zero_job, result=zero), dict(name="stale", job=stale)]
            )
            new_input["search"]["deadline_utc"] = (
                (datetime.now(timezone.utc) - timedelta(seconds=1))
                .isoformat()
                .replace("+00:00", "Z")
            )
            expired_scenario = call(
                "PUT",
                "/api/v1/scenarios/" + runtime.scenario_ref.scenario_id,
                headers={"If-Match": '"2"'},
                json=new_input,
            )
            runtime.scenario_ref = ScenarioRef(
                **{k: expired_scenario[k] for k in ("scenario_id", "revision", "scope")}
            )
            expired = poll(submit("deadline", "search_layouts", {}))
            require(
                expired["status"] == "failed"
                and expired["error"]["code"] == "DEADLINE_EXCEEDED"
                and expired["run_id"] is None,
                "Deadline was reported as success",
            )
            evidence["phases"].append(dict(name="deadline", job=expired))
        evidence["implementation"] = runtime.handler._manifest()
        evidence["status"] = "passed"
    except BaseException as exc:
        evidence.update(status="failed", failure_type=type(exc).__name__, failure=str(exc))
        raise
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(timeout=30)
        if sock is not None:
            sock.close()
        closed = True
        if "base_url" in evidence:
            with socket.socket() as probe:
                closed = (
                    probe.connect_ex(("127.0.0.1", int(evidence["base_url"].rsplit(":", 1)[1])))
                    != 0
                )
        evidence["cleanup"] = dict(
            server_stopped=thread is None or not thread.is_alive(),
            worker_stopped=runtime is None or runtime.app.state.service.worker is None,
            port_closed=closed,
        )
        (output / "evidence.json").write_text(
            json.dumps(evidence, indent=2, allow_nan=False), encoding="utf-8"
        )
        if not all(evidence["cleanup"].values()):
            raise RuntimeError("Owned server/worker cleanup failed")
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    evidence = run(args.output)
    print(
        json.dumps(
            dict(status=evidence["status"], output=str(args.output), phases=len(evidence["phases"]))
        )
    )


if __name__ == "__main__":
    main()
