"""Executable HTTP/worker proof using real synthetic reference outputs."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import socket
from threading import Thread
from time import monotonic, sleep
import traceback

import httpx
import uvicorn

from tree_planner.contracts import Result, ScenarioRef
from tree_planner.jobs import JobWorker
from .runtime import SOURCE_HASHES, create_reference_runtime


def _require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run_reference_demo(output: Path, *, numerical_source: Path):
    """Own one real loopback server, stop it on every exit, retain actual receipts."""
    output = Path(output).resolve()
    output.mkdir(parents=True, exist_ok=False)
    evidence = dict(
        status="running",
        started_at_utc=datetime.now(timezone.utc).isoformat(),
        scope="synthetic one-tree geometric reference; no model or scientific acceptance",
        numerical_source_hashes=dict(SOURCE_HASHES),
        http=[],
        checks={},
    )
    server = thread = sock = runtime = None

    def save():
        (output / "evidence.json").write_text(
            json.dumps(evidence, indent=2, allow_nan=False), encoding="utf-8"
        )

    try:
        runtime = create_reference_runtime(output / "runtime", numerical_source=numerical_source)
        evidence["synthetic_inputs"] = runtime.scene.declaration()
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        base = f"http://127.0.0.1:{port}"
        evidence["server"] = dict(
            base_url=base, transport="real TCP HTTP; Uvicorn; background JobWorker"
        )
        server = uvicorn.Server(uvicorn.Config(runtime.app, log_level="warning", access_log=False))
        thread = Thread(
            target=server.run,
            kwargs={"sockets": [sock]},
            daemon=False,
            name="canopy-reference-http",
        )
        thread.start()
        deadline = monotonic() + 20
        while not server.started:
            _require(thread.is_alive() and monotonic() < deadline, "HTTP server failed to start")
            sleep(0.02)
        with httpx.Client(
            base_url=base, headers={"Origin": base}, timeout=10, trust_env=False
        ) as client:

            def call(method, path, *, expected=200, **kwargs):
                response = client.request(method, path, **kwargs)
                body = response.json()
                evidence["http"].append(
                    dict(method=method, path=path, status=response.status_code, body=body)
                )
                _require(
                    response.status_code == expected,
                    f"HTTP {method} {path}: expected {expected}, got {response.status_code}",
                )
                return body

            def selections(ref):
                return call(
                    "GET", f"/api/v1/scenarios/{ref.scenario_id}/selections?revision={ref.revision}"
                )

            def submit(ref, name):
                request = runtime.request(name, scenario=ref).model_dump(mode="json")
                return call("POST", "/api/v1/jobs", expected=202, json=request)

            def poll(job):
                deadline = monotonic() + 20
                while True:
                    value = call("GET", "/api/v1/jobs/" + job["job_id"])
                    if value["status"] in ("completed", "failed", "cancelled"):
                        return value
                    _require(
                        monotonic() < deadline, "job did not terminate before polling deadline"
                    )
                    sleep(0.025)

            def result(job):
                _require(job["status"] == "completed" and job["run_id"], "job did not complete")
                body = call("GET", "/api/v1/results/" + job["run_id"])
                typed = Result.model_validate(body)
                _require(
                    typed.layouts[0].feasibility == "not_evaluated", "feasibility claim changed"
                )
                _require(
                    typed.source_job_id == job["job_id"]
                    and typed.input_fingerprint == job["input_fingerprint"],
                    "result identity mismatch",
                )
                hashes = runtime.app.state.service.resolve_for_execution(
                    typed.input_snapshot_ref, operation="evaluate_layout"
                )[1]
                _require(
                    typed.provenance.source_hashes == hashes,
                    "result hashes differ from actual inputs",
                )
                return body

            health = call("GET", "/api/v1/health")
            _require(
                health["worker_mode"] == "background"
                and health["available_operations"] == ["evaluate_layout"],
                "unsupported provider advertised",
            )
            ref = runtime.scenario_ref
            positive_job = poll(submit(ref, "positive"))
            positive = result(positive_job)
            _require(positive["metrics"][0]["value"] == 2.0, "analytic positive invariant failed")
            _require(
                selections(ref)["evaluation"]["current_job"]["run_id"] == positive["run_id"],
                "positive result is not current",
            )
            evidence["checks"]["positive_m2_h"] = positive["metrics"][0]["value"]

            layout = call("GET", "/api/v1/layouts/synthetic-one-tree?revision=1")
            layout["revision"] = 2
            layout["placements"][0]["position_enu_m"] = [20.0, -1.0, 0.0]
            call("POST", "/api/v1/layouts", expected=201, json=layout)
            scenario = call("GET", f"/api/v1/scenarios/{ref.scenario_id}?revision=1")
            changed = scenario["input"]
            changed["proposed_layout_ref"]["revision"] = 2
            updated = call(
                "PUT",
                f"/api/v1/scenarios/{ref.scenario_id}",
                json=changed,
                headers={"If-Match": '"1"'},
            )
            new_ref = ScenarioRef.model_validate(
                {k: updated[k] for k in ("scenario_id", "revision", "scope")}
            )
            _require(
                new_ref.revision == 2 and selections(ref)["evaluation"]["current_job"] is None,
                "old revision remains current",
            )
            _require(
                call("GET", "/api/v1/results/" + positive["run_id"]) == positive,
                "immutable positive result changed",
            )
            zero_job = poll(submit(new_ref, "valid-zero"))
            zero = result(zero_job)
            _require(zero["metrics"][0]["value"] == 0.0, "valid zero invariant failed")
            _require(
                zero_job["input_fingerprint"] != positive_job["input_fingerprint"],
                "changed geometry reused the input identity",
            )
            _require(
                selections(new_ref)["evaluation"]["current_job"]["run_id"] == zero["run_id"],
                "valid zero is not current",
            )
            evidence["checks"].update(
                valid_zero_m2_h=zero["metrics"][0]["value"],
                changed_revision_stales_old=True,
                geometry_changes_fingerprint=True,
                immutable_old_result=True,
            )

            # Controlled corruption of our generated local asset AFTER admission.
            # No producer source is changed and no output is fabricated. Stop the
            # owned worker first so the failure cannot race with queue admission.
            service = runtime.app.state.service
            service.worker.stop()
            failed_job = submit(new_ref, "changed-asset-failure")
            asset_path = output / "runtime/inputs/synthetic-reference.json"
            original = asset_path.read_bytes()
            try:
                asset_path.write_bytes(original + b"\n")
                service.worker = JobWorker(service.jobs, service.handlers)
                service.worker.start(exclusive=True)
                runtime.app.state.worker = service.worker
                failed = poll(failed_job)
                _require(
                    failed["status"] == "failed" and failed["run_id"] is None,
                    "changed asset did not fail closed",
                )
                _require(
                    selections(new_ref)["evaluation"]["current_job"] is None,
                    "failed selection displays an older result as current",
                )
            finally:
                asset_path.write_bytes(original)
            recovered = result(poll(submit(new_ref, "restored-asset-recovery")))
            _require(recovered["metrics"][0]["value"] == 0.0, "restored runtime failed recovery")
            _require(
                call("GET", "/api/v1/results/" + zero["run_id"]) == zero,
                "immutable zero result changed",
            )
            evidence["checks"].update(
                changed_asset_job_failed_without_result=True,
                failed_selection_clears_current=True,
                restored_asset_recovered=True,
            )
            evidence["runs"] = dict(
                positive=positive, zero=zero, failure=failed, recovery=recovered
            )
            evidence["status"] = "passed"
    except BaseException as exc:
        evidence["status"] = "failed"
        evidence["failure"] = dict(type=type(exc).__name__, message=str(exc))
        (output / "failure.txt").write_text(traceback.format_exc(), encoding="utf-8")
        raise
    finally:
        if server is not None:
            server.should_exit = True
        if thread is not None:
            thread.join(timeout=20)
        if sock is not None:
            sock.close()
        stopped = thread is None or not thread.is_alive()
        evidence["checks"]["owned_server_stopped"] = stopped
        evidence["checks"]["owned_worker_stopped"] = (
            runtime is None or runtime.app.state.service.worker is None
        )
        if not stopped or not evidence["checks"]["owned_worker_stopped"]:
            evidence["status"] = "failed"
        evidence["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
        save()
        _require(
            stopped and evidence["checks"]["owned_worker_stopped"],
            "owned server/worker did not stop",
        )
    return evidence


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="fresh local evidence directory")
    parser.add_argument(
        "--numerical-source", type=Path, default=os.environ.get("CANOPY_NUMERICS_SOURCE")
    )
    args = parser.parse_args(argv)
    if args.numerical_source is None:
        parser.error("--numerical-source or CANOPY_NUMERICS_SOURCE is required")
    try:
        evidence = run_reference_demo(args.output, numerical_source=args.numerical_source)
    except Exception as exc:
        print(f"Reference demo FAILED: {type(exc).__name__}: {exc}")
        return 1
    print(json.dumps(dict(status=evidence["status"], checks=evidence["checks"]), sort_keys=True))
    return 0 if evidence["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
