"""Synthetic physical-runtime adapter for the deterministic fixed workflow.

There is no manual UI capture or model provider in this adapter. Those arms are
reported blocked, never replayed as fabricated human/model sessions.
"""

from __future__ import annotations

import hashlib
import json
import re

from tree_planner.agents import tool_schemas
from tree_planner.api.service import AgentDispatcher
from tree_planner.canonical import content_hash
from tree_planner.contracts import OperationEnvelope
from tree_planner.evaluators.physical_runtime import OPERATIONS, create_physical_runtime


class BlockedArm:
    def __init__(self, reason: str, metadata: dict):
        self.blocked_reason = reason
        self._metadata = metadata

    def metadata(self, mode):
        return {"arm_status": "blocked", **self._metadata}


class PhysicalFixedWorkflow:
    def __init__(self, runtime, *, source_integrity_fault=False):
        self.runtime = runtime
        self.source_integrity_fault = source_integrity_fault
        self.dispatcher = AgentDispatcher(
            runtime.app.state.service, accepted_ref=runtime.scenario_ref
        )
        scenario = runtime.app.state.scenarios.get_scenario(runtime.scenario_ref)
        self.scenario = scenario

    def comparison_identity(self):
        def normalize(value):
            if isinstance(value, dict):
                return {
                    key: normalize(item)
                    for key, item in value.items()
                    if key not in {"source_ids", "candidate_catalogue_fingerprint", "deadline_utc"}
                }
            if isinstance(value, list):
                return [normalize(item) for item in value]
            return value

        normalized_input = normalize(self.scenario.input.model_dump(mode="json"))
        config = {
            "handler_manifest": self.runtime.handler._manifest(),
            "numerics": normalized_input["numerics"],
            "search": normalized_input["search"],
            "constraints": normalized_input["constraints"],
        }
        tools = tool_schemas(sorted(OPERATIONS))
        return {
            "input_fingerprint": content_hash(normalized_input),
            "data_sha256": hashlib.sha256(self.runtime.scene_path.read_bytes()).hexdigest(),
            "tools_sha256": hashlib.sha256(
                json.dumps(tools, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest(),
            "backend_config_sha256": content_hash(config),
            "normalization": "scenario/job/source IDs, candidate catalogue fingerprint (which includes source IDs), and seed-time deadline_utc are excluded; normalized input semantics, scene bytes, tool schemas, constraints, numerics, search policy/seed and implementation/dependency manifest remain hashed",
        }

    def metadata(self, mode):
        return {
            "arm_status": "available",
            "workflow_kind": "scripted_fixed_workflow",
            "human_run": False,
            "requested_inference_route": None,
            "requested_model": None,
            "native_session_ids": [],
            "model_attestation": "not_applicable; no model call in fixed workflow",
            "fault_injection": "synthetic registered-scene integrity mismatch"
            if self.source_integrity_fault
            else None,
        }

    def _operations(self, request: str):
        text = request.casefold()
        operations = ["evaluate_layout"]
        if re.search(r"\b(feasib|constraint|budget|proposal)\w*", text):
            operations.append("search_layouts")
        if re.search(r"\b(mov|position|location)\w*", text):
            operations.append("compare_locations")
        return operations

    def run(self, mode, task, dispatcher):
        errors = []
        scenario = self.scenario
        layout_ref = scenario.input.proposed_layout_ref.model_dump(mode="json")
        for index, operation in enumerate(self._operations(task["request"])):
            args = {"layout_ref": layout_ref} if operation == "evaluate_layout" else {}
            if operation == "compare_locations":
                placement = scenario.input.proposed_layout_ref
                layout = self.runtime.app.state.scenarios.get_layout(
                    placement.layout_id, placement.revision
                )
                if not layout.placements:
                    errors.append({"operation": operation, "reason": "no proposed placement"})
                    continue
                # A declared fixed probe input; no expected physical result is encoded.
                args = {
                    "layout_ref": layout_ref,
                    "placement_id": layout.placements[0].placement_id,
                    "alternative_position_enu_m": [100.0, 0.0, 0.0],
                }
            payload = {
                "request_id": f"b11-fixed-{task['id']}-{index}",
                "scenario_ref": self.runtime.scenario_ref.model_dump(mode="json"),
                "operation": operation,
                "arguments": args,
            }
            try:
                job = dispatcher.dispatch(OperationEnvelope.model_validate(payload))
                self.runtime.app.state.run_one()
                final = dispatcher.poll(job.job_id)
                if final.status != "completed":
                    errors.append(
                        {
                            "operation": operation,
                            "status": final.status,
                            "error_code": final.error.code if final.error else None,
                        }
                    )
            except Exception as exc:
                # This is an observed fixed-workflow failure, not a fabricated result.
                errors.append({"operation": operation, "error_type": type(exc).__name__})
        current_ids = {
            event["run_id"]
            for event in dispatcher.events
            if event.get("current") is True and event.get("run_id")
        }
        lines = []
        for run_id, result in dispatcher.results.items():
            if run_id not in current_ids:
                continue
            lines.append(
                f"Current backend result {run_id}: {result.operation}; {result.analytical_outcome}."
            )
            lines.extend(
                f"Metric {metric.metric_id}={metric.value:g} {metric.unit} (case={metric.case_id}, layout={metric.layout_id})."
                for metric in result.metrics
            )
            lines.extend(
                f"Constraint {constraint.rule}: {constraint.status}."
                for constraint in result.constraints
            )
            lines.extend(f"Limitation: {limitation}." for limitation in result.limitations)
        for event in dispatcher.events:
            if event.get("status") in {"error", "failed", "cancelled"}:
                reason = event.get("error_code") or event.get("error_type") or event.get("status")
                lines.append(f"No validated result for {event['operation']}; observed {reason}.")
        return {
            "status": "completed" if not errors else "partial",
            "tool_errors": [],
            "final_response": "\n".join(lines),
            "response_evidence_ids": sorted(current_ids),
            "user_actions": [],
            "numeric_claim_audits": [],
            "claim_audit_complete": False,
            "useful_analysis_run_ids": [],
        }


def physical_factory(task, mode_workspace, mode):
    if mode == "manual":
        return BlockedArm(
            "manual UI interaction/action capture adapter is unavailable", {"human_run": False}
        )
    if mode == "adaptive":
        return BlockedArm(
            "authorized loopback provider check at http://127.0.0.1:8001/v1 timed out; no model call attempted",
            {
                "requested_inference_route": "http://127.0.0.1:8001/v1",
                "requested_model": None,
                "native_session_ids": [],
                "model_attestation": "unavailable; endpoint did not respond; model name not observed",
            },
        )
    if mode != "fixed":
        return BlockedArm(f"unsupported workflow mode: {mode}", {})
    runtime = create_physical_runtime(mode_workspace / "runtime", start_worker=False)
    source_integrity_fault = task["id"] == "tool-failure-recovery"
    if source_integrity_fault:
        # Exercise the real trusted-source guard with a labelled synthetic fault.
        # The fresh private runtime is intentionally left corrupt so no stale or
        # cached result can be substituted into this failure task.
        runtime.scene_path.write_bytes(runtime.scene_path.read_bytes() + b" ")
    return PhysicalFixedWorkflow(runtime, source_integrity_fault=source_integrity_fault)
