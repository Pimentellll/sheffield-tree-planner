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
from pathlib import Path
import time
from typing import Any


MODES = ("manual", "fixed", "adaptive")


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dump(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf-8")


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
            self.events.append({"operation": name, "status": getattr(value, "status", "returned"),
                                "job_id": job_id, "run_id": run_id,
                                "elapsed_ms": (time.perf_counter_ns() - started) / 1_000_000})
            return value
        except Exception as exc:
            self.events.append({"operation": name, "status": "error", "error_type": type(exc).__name__,
                                "elapsed_ms": (time.perf_counter_ns() - started) / 1_000_000})
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

                ref = ScenarioRef(scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope)
                validate_delivery_currentness(job, result, self.inner.selection(ref, job.view_slot))
                current = True
            except (ImportError, ValueError, AttributeError):
                current = False
        self.events.append({"operation": job.operation, "status": job.status, "job_id": job.job_id,
                            "run_id": job.run_id, "current": current})
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


def score_run(task: dict, observation: dict, *, actual_job_ids: set[str], actual_run_ids: set[str]) -> dict:
    """Apply observable rubric fields; no scalar intelligence score is computed."""
    integrity: list[str] = []
    events = observation.get("operation_events", [])
    for event in events:
        job_id, run_id = event.get("job_id"), event.get("run_id")
        if job_id and job_id not in actual_job_ids:
            integrity.append(f"unobserved job id: {job_id}")
        if run_id and run_id not in actual_run_ids:
            integrity.append(f"unobserved run id: {run_id}")
    observed_ops = {e.get("operation") for e in events}
    required_ops = set(task.get("required_operations", []))
    required_met = required_ops.issubset(observed_ops)
    observed_current_run = any(
        e.get("run_id") in actual_run_ids and e.get("current") is True for e in events
    )
    errors = list(observation.get("tool_errors", []))
    job_failures = any(e.get("status") in {"failed", "cancelled"} for e in events)
    observed_operation_error = any(e.get("status") == "error" for e in events)
    permits_failure = "explicit failure" in task.get("required_outcome", "")
    completion = not integrity and required_met and (
        observed_current_run or (permits_failure and (errors or job_failures or observed_operation_error))
    )

    checks = observation.get("constraint_checks", [])
    passed = sum(check.get("status") == "pass" for check in checks)
    accuracy = {"passed": passed, "checked": len(checks), "all_passed": bool(checks) and passed == len(checks)}
    claims = observation.get("numeric_claim_audits", [])
    audit_complete = observation.get("claim_audit_complete") is True
    unsupported = sum(claim.get("supported") is False for claim in claims) if audit_complete else None
    actions = observation.get("user_actions", [])
    useful_ids = set(observation.get("useful_analysis_run_ids", []))
    useful = useful_ids.intersection(actual_run_ids)
    integrity.extend(f"unobserved useful analysis run id: {i}" for i in sorted(useful_ids - actual_run_ids))
    elapsed = observation.get("elapsed_ms")
    if type(elapsed) not in (int, float) or elapsed < 0:
        integrity.append("invalid elapsed_ms")
        elapsed = None
    return {
        "completion": bool(completion and not integrity),
        "constraint_accuracy": accuracy,
        "unsupported_claims": unsupported,
        "claim_audit_complete": audit_complete,
        "human_actions": len(actions),
        "human_corrections": sum(action.get("kind") == "correction" for action in actions),
        "useful_analyses": len(useful),
        "tool_errors": len(errors) + sum(e.get("status") == "error" for e in events),
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
            identity = env.comparison_identity()
            required_identity_fields = {"input_fingerprint", "data_sha256", "tools_sha256", "backend_config_sha256"}
            if not isinstance(identity, dict) or not required_identity_fields <= identity.keys():
                raise ValueError("adapter must provide complete comparison identity hashes")
            identities[mode] = {k: identity[k] for k in sorted(required_identity_fields)}
            if any(not isinstance(v, str) or not v for v in identities[mode].values()):
                raise ValueError("comparison identity hashes must be nonempty strings")
            if len(set(json.dumps(v, sort_keys=True) for v in identities.values())) > 1:
                raise ValueError("task input, data, tool schemas or backend config differ across modes")
            dispatcher = RecordingDispatcher(env.dispatcher)
            started = time.perf_counter_ns()
            try:
                observation = env.run(mode, task, dispatcher)
                if not isinstance(observation, dict):
                    raise TypeError("adapter observation must be a dict")
            except Exception as exc:
                observation = {"status": "failed", "adapter_error_type": type(exc).__name__,
                               "operation_events": dispatcher.events, "tool_errors": [type(exc).__name__],
                               "constraint_checks": [], "numeric_claim_audits": [], "user_actions": [],
                               "useful_analysis_run_ids": [],
                               "elapsed_ms": (time.perf_counter_ns() - started) / 1_000_000}
            # Never let adapter supplied events replace calls actually observed here.
            observation["operation_events"] = dispatcher.events
            # Constraints come directly from immutable backend Results, not an adapter score.
            observation["constraint_checks"] = [
                {"status": c.status, "rule": c.rule, "result_id": r.run_id}
                for r in dispatcher.results.values() for c in r.constraints
            ]
            observation.setdefault("tool_errors", [])
            observation.setdefault("constraint_checks", [])
            observation.setdefault("numeric_claim_audits", [])
            observation.setdefault("user_actions", [])
            observation.setdefault("useful_analysis_run_ids", [])
            observation["elapsed_ms"] = (time.perf_counter_ns() - started) / 1_000_000
            scored = score_run(task, observation, actual_job_ids=set(dispatcher.jobs),
                               actual_run_ids=set(dispatcher.results))
            metadata = env.metadata(mode) if callable(getattr(env, "metadata", None)) else {}
            _dump(mode_dir / "run.json", {"mode": mode, "comparison_identity": identities[mode], "metadata": metadata,
                                                "observation": observation, "score": scored,
                                                "jobs": {k: _json_model(v) for k, v in dispatcher.jobs.items()},
                                                "results": {k: _json_model(v) for k, v in dispatcher.results.items()}})
            rows.append({"task_id": task["id"], "mode": mode, "score": scored})
    report = {"schema": "canopy-b11-run-v1", "created_at_utc": datetime.now(timezone.utc).isoformat(),
              "task_manifest_sha256": _digest(task_file), "adapter": adapter_spec,
              "comparison_identities": comparison_identities,
              "run_kind": "scripted_workflow_comparison; manual mode is human only when adapter declares and logs actual human actions",
              "rows": rows}
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
