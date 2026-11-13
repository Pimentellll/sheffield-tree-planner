"""B11 evidence harness. Workflow adapters call the real local domain dispatcher.

Adapters are experiment orchestration only; scoring reads job/result objects
observed by the runner and the backend JobStore. A scripted adapter is recorded
as scripted and is never described as a human run.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib
import json
import math
from pathlib import Path
import time
from typing import Any


MODES = ("manual", "fixed", "adaptive")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(path: Path, value: Any) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


class RecordingDispatcher:
    """Record typed values returned by actual service calls without rewriting them."""

    def __init__(self, dispatcher):
        self.inner = dispatcher
        self.jobs: dict[str, Any] = {}
        self.results: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []

    def dispatch(self, envelope):
        name = envelope.root.operation
        started = time.perf_counter_ns()
        try:
            value = self.inner.dispatch(envelope)
            job_id = getattr(value, "job_id", None)
            run_id = getattr(value, "run_id", None)
            if job_id:
                self.jobs[job_id] = value
            if run_id:
                self.results[run_id] = self.inner.result(run_id)
            self.events.append(
                {
                    "operation": name,
                    "status": getattr(value, "status", "returned"),
                    "job_id": job_id,
                    "run_id": run_id,
                    "elapsed_ms": (time.perf_counter_ns() - started) / 1_000_000,
                }
            )
            return value
        except Exception as exc:
            self.events.append(
                {
                    "operation": name,
                    "status": "error",
                    "error_type": type(exc).__name__,
                    "error_code": getattr(exc, "code", None),
                    "elapsed_ms": (time.perf_counter_ns() - started) / 1_000_000,
                }
            )
            raise

    def poll(self, job_id):
        job = self.inner.poll(job_id)
        self.jobs[job.job_id] = job
        current = False
        if job.status == "completed" and job.run_id:
            result = self.inner.result(job.run_id)
            self.results[job.run_id] = result
            try:
                from tree_planner.contracts import ScenarioRef, validate_delivery_currentness

                ref = ScenarioRef(
                    scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope
                )
                validate_delivery_currentness(job, result, self.inner.selection(ref, job.view_slot))
                current = True
            except (ImportError, ValueError, AttributeError):
                current = False
        self.events.append(
            {
                "operation": job.operation,
                "status": job.status,
                "job_id": job.job_id,
                "run_id": job.run_id,
                "current": current,
                "error_code": job.error.code if job.error else None,
            }
        )
        return job

    def result(self, run_id):
        value = self.inner.result(run_id)
        self.results[run_id] = value
        return value

    def selection(self, ref, slot):
        return self.inner.selection(ref, slot)


def _json_model(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def score_run(
    task: dict,
    observation: dict,
    *,
    actual_job_ids: set[str],
    actual_run_ids: set[str],
    current_run_ids: set[str] | None = None,
) -> dict:
    """Apply observable rubric fields; no scalar intelligence score is computed."""
    integrity: list[str] = []
    events = observation.get("operation_events", [])
    for event in events:
        job_id, run_id = event.get("job_id"), event.get("run_id")
        if job_id and job_id not in actual_job_ids:
            integrity.append(f"unobserved job id: {job_id}")
        if run_id and run_id not in actual_run_ids:
            integrity.append(f"unobserved run id: {run_id}")
    required_ops = set(task.get("required_operations", []))
    response_ids = set(observation.get("response_evidence_ids", []))
    for run_id in sorted(response_ids - actual_run_ids):
        integrity.append(f"response cites unobserved run id: {run_id}")
    current_run_ids = current_run_ids or {
        e.get("run_id") for e in events if e.get("current") is True and e.get("run_id")
    }
    current_results_by_op = {
        e.get("operation"): e.get("run_id")
        for e in events
        if e.get("operation") in required_ops
        and e.get("run_id") in actual_run_ids
        and e.get("run_id") in current_run_ids
        and e.get("current") is True
        and e.get("status") == "completed"
    }
    failed_ops = {
        e.get("operation")
        for e in events
        if e.get("operation") in required_ops
        and (e.get("status") in {"failed", "cancelled", "error"})
    }
    errors = list(observation.get("tool_errors", []))
    outcome_text = task.get("required_outcome", "").casefold()
    permits_failure = "failure" in outcome_text or "failed" in outcome_text
    required_succeeded = required_ops.issubset(current_results_by_op)
    # A safe explicit failure can complete a one-operation task. In compound
    # tasks every declared operation must produce a current result; one success
    # cannot mask another required operation's failure.
    accepted_single_failure = (
        len(required_ops) == 1 and permits_failure and required_ops.issubset(failed_ops)
    )
    final_response = observation.get("final_response", "")
    if not isinstance(final_response, str):
        integrity.append("invalid final_response")
        final_response = ""
    response_covers_results = required_succeeded and all(
        current_results_by_op[op] in response_ids and current_results_by_op[op] in final_response
        for op in required_ops
    )
    response_acknowledges_failure = accepted_single_failure and (
        "no validated result" in final_response.casefold()
        and all(
            (event.get("error_code") or event.get("error_type") or event.get("status", ""))
            in final_response
            for event in events
            if event.get("operation") in required_ops
            and event.get("status") in {"error", "failed", "cancelled"}
        )
    )
    completion = not integrity and (response_covers_results or response_acknowledges_failure)
    if task.get("stratum") == "counterfactual":
        run_id = current_results_by_op.get("compare_locations")
        actual_outcomes = observation.get("backend_outcomes", {})
        completion = completion and (
            (run_id is not None and actual_outcomes.get(run_id) == "comparison_completed")
            or response_acknowledges_failure
        )
    if task.get("stratum") == "infeasible":
        # Feasibility is an explicit diagnostic, so unknown checks remain valid
        # observations and are not treated as failed constraints.
        diagnostic = observation.get("backend_constraint_diagnostics", {})
        completion = completion and all(
            run_id in diagnostic and diagnostic[run_id] is True
            for run_id in (current_results_by_op.get(op) for op in required_ops)
        )
    operation_completion = {
        operation: (
            "current_result"
            if operation in current_results_by_op
            else "observed_failure_acknowledged"
            if response_acknowledges_failure and operation in failed_ops
            else "observed_failure_unacknowledged"
            if accepted_single_failure and operation in failed_ops
            else "missing_or_not_current"
        )
        for operation in sorted(required_ops)
    }

    checks = observation.get("constraint_checks", [])
    passed = sum(check.get("status") == "pass" for check in checks)
    status_counts = {
        status: sum(check.get("status") == status for check in checks)
        for status in ("pass", "fail", "unknown")
    }
    accuracy = {
        "passed": passed,
        "checked": len(checks),
        "all_passed": bool(checks) and passed == len(checks),
    }
    accuracy["counts_by_status"] = status_counts
    claims = observation.get("numeric_claim_audits", [])
    audit_complete = observation.get("claim_audit_complete") is True
    unsupported = (
        sum(claim.get("supported") is False for claim in claims) if audit_complete else None
    )
    actions = observation.get("user_actions", [])
    useful_ids = set(observation.get("useful_analysis_run_ids", []))
    useful = useful_ids.intersection(actual_run_ids).intersection(current_run_ids)
    integrity.extend(
        f"unobserved useful analysis run id: {i}" for i in sorted(useful_ids - actual_run_ids)
    )
    elapsed = observation.get("elapsed_ms")
    if type(elapsed) not in (int, float) or not math.isfinite(elapsed) or elapsed < 0:
        integrity.append("invalid elapsed_ms")
        elapsed = None
    return {
        "completion": bool(completion and not integrity),
        "required_operation_status": operation_completion,
        "constraint_accuracy": accuracy,
        "unsupported_claims": unsupported,
        "claim_audit_complete": audit_complete,
        "human_actions": len(actions),
        "human_corrections": sum(action.get("kind") == "correction" for action in actions),
        "useful_analyses": len(useful),
        "tool_errors": len(errors)
        + sum(e.get("status") in {"error", "failed", "cancelled"} for e in events),
        "latency_ms": elapsed,
        "integrity_errors": integrity,
    }


def _load_factory(spec: str):
    module_name, sep, attr = spec.partition(":")
    if not sep:
        raise ValueError("adapter must be module:factory")
    factory = getattr(importlib.import_module(module_name), attr)
    if not callable(factory):
        raise TypeError("adapter factory is not callable")
    return factory


def run_suite(task_file: Path, output: Path, adapter_spec: str) -> dict:
    """Run each task in fresh identical runtime snapshots across all workflow modes.

    Adapter factory: ``factory(task, mode_workspace, mode) -> environment`` with
    ``environment.run(mode, task, dispatcher) -> observation`` and
    ``environment.comparison_identity()`` returning immutable input, tool and
    backend-config hashes. A fresh runtime per mode prevents a prior workflow's
    selection from contaminating currentness checks; identities must match.
    """
    payload = json.loads(task_file.read_text(encoding="utf-8-sig"))
    tasks = payload.get("tasks")
    if payload.get("schema") != "canopy-b11-heldout-v1" or not isinstance(tasks, list):
        raise ValueError("unsupported held-out task manifest")
    output.mkdir(parents=True, exist_ok=False)
    factory = _load_factory(adapter_spec)
    rows = []
    comparison_identities = {}
    for task in tasks:
        task_dir = output / task["id"]
        task_dir.mkdir()
        identities = {}
        comparison_identities[task["id"]] = identities
        for mode in MODES:
            mode_dir = task_dir / mode
            mode_dir.mkdir()
            env = factory(task, mode_dir, mode)
            blocked_reason = getattr(env, "blocked_reason", None)
            if blocked_reason:
                metadata = env.metadata(mode) if callable(getattr(env, "metadata", None)) else {}
                _dump(
                    mode_dir / "blocked.json",
                    {
                        "mode": mode,
                        "status": "blocked",
                        "reason": blocked_reason,
                        "metadata": metadata,
                    },
                )
                rows.append(
                    {
                        "task_id": task["id"],
                        "mode": mode,
                        "status": "blocked",
                        "reason": blocked_reason,
                    }
                )
                continue
            identity = env.comparison_identity()
            required_identity_fields = {
                "input_fingerprint",
                "data_sha256",
                "tools_sha256",
                "backend_config_sha256",
            }
            if not isinstance(identity, dict) or not required_identity_fields <= identity.keys():
                raise ValueError("adapter must provide complete comparison identity hashes")
            identities[mode] = {k: identity[k] for k in sorted(required_identity_fields)}
            if any(not isinstance(v, str) or not v for v in identities[mode].values()):
                raise ValueError("comparison identity hashes must be nonempty strings")
            if len(set(json.dumps(v, sort_keys=True) for v in identities.values())) > 1:
                raise ValueError(
                    "task input, data, tool schemas or backend config differ across modes"
                )
            dispatcher = RecordingDispatcher(env.dispatcher)
            started = time.perf_counter_ns()
            try:
                observation = env.run(mode, task, dispatcher)
                if not isinstance(observation, dict):
                    raise TypeError("adapter observation must be a dict")
            except Exception as exc:
                observation = {
                    "status": "failed",
                    "adapter_error_type": type(exc).__name__,
                    "operation_events": dispatcher.events,
                    "tool_errors": [type(exc).__name__],
                    "constraint_checks": [],
                    "numeric_claim_audits": [],
                    "user_actions": [],
                    "useful_analysis_run_ids": [],
                    "elapsed_ms": (time.perf_counter_ns() - started) / 1_000_000,
                }
            # Never let adapter supplied events replace calls actually observed here.
            observation["operation_events"] = dispatcher.events
            # Constraints come directly from immutable backend Results, not an adapter score.
            observation["constraint_checks"] = [
                {"status": c.status, "rule": c.rule, "result_id": r.run_id}
                for r in dispatcher.results.values()
                for c in r.constraints
            ]
            observation.setdefault("tool_errors", [])
            observation.setdefault("constraint_checks", [])
            observation.setdefault("numeric_claim_audits", [])
            observation.setdefault("user_actions", [])
            observation.setdefault("useful_analysis_run_ids", [])
            observation["elapsed_ms"] = (time.perf_counter_ns() - started) / 1_000_000
            current_ids = {
                e["run_id"]
                for e in dispatcher.events
                if e.get("current") is True and e.get("run_id")
            }
            observation["backend_outcomes"] = {
                run_id: result.analytical_outcome for run_id, result in dispatcher.results.items()
            }
            observation["backend_constraint_diagnostics"] = {
                run_id: bool(result.constraints)
                and bool(result.layouts)
                and all(c.status in {"pass", "fail", "unknown"} for c in result.constraints)
                and all(
                    layout.feasibility in {"feasible", "infeasible"} for layout in result.layouts
                )
                for run_id, result in dispatcher.results.items()
            }
            scored = score_run(
                task,
                observation,
                actual_job_ids=set(dispatcher.jobs),
                actual_run_ids=set(dispatcher.results),
                current_run_ids=current_ids,
            )
            metadata = env.metadata(mode) if callable(getattr(env, "metadata", None)) else {}
            _dump(
                mode_dir / "run.json",
                {
                    "mode": mode,
                    "comparison_identity": identities[mode],
                    "metadata": metadata,
                    "observation": observation,
                    "score": scored,
                    "jobs": {k: _json_model(v) for k, v in dispatcher.jobs.items()},
                    "results": {k: _json_model(v) for k, v in dispatcher.results.items()},
                },
            )
            rows.append({"task_id": task["id"], "mode": mode, "score": scored})
    report = {
        "schema": "canopy-b11-run-v1",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_manifest_sha256": _digest(task_file),
        "adapter": adapter_spec,
        "comparison_identities": comparison_identities,
        "run_kind": "scripted_workflow_comparison; manual mode is human only when adapter declares and logs actual human actions",
        "rows": rows,
    }
    _dump(output / "report.json", report)
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tasks", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--adapter", required=True, help="Python module:factory")
    args = parser.parse_args(argv)
    run_suite(args.tasks, args.output, args.adapter)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
