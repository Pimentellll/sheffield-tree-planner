"""Fail-closed bridge to explicitly registered search and independent validation.

This module supplies no search, physics, feasibility or proof implementation.
Callbacks and their manifests are trusted server configuration, never request data.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import inspect
import types
from pathlib import Path
from typing import Callable

from tree_planner.canonical import content_hash
from tree_planner.contracts import JobRequest, Result, Scenario, ScenarioRef


class SearchRejected(ValueError):
    """The consumer cannot validate this execution."""


@dataclass(frozen=True)
class LayoutVerdict:
    """Independent determination for one layout, including all constraint records."""

    layout_id: str
    feasibility: str
    cost_pence: int
    constraints: tuple


@dataclass(frozen=True)
class SearchVerdict:
    """Independent validation of all layouts and the claimed search outcome.

    target_met is True/False only when independently established; None is unknown
    or inapplicable. proof_verified is reserved for a checked exact finite proof.
    """

    layouts: tuple[LayoutVerdict, ...]
    outcome: str
    target_met: bool | None
    proof_verified: bool


@dataclass(frozen=True)
class SearchProvider:
    resolve_dependencies: Callable
    produce: Callable
    validate: Callable
    producer_manifest: Callable
    validator_manifest: Callable

    def __post_init__(self):
        callbacks = (
            self.resolve_dependencies,
            self.produce,
            self.validate,
            self.producer_manifest,
            self.validator_manifest,
        )
        if not all(callable(c) for c in callbacks) or self.produce is self.validate:
            raise ValueError("distinct trusted producer and validator required")
        # Require inspectable Python functions, with explicit manifests for every
        # transitive implementation/config/input the trusted provider uses.
        for callback in callbacks[1:]:
            _implementation(callback)


def _code_identity(code):
    def constant(value):
        if isinstance(value, types.CodeType):
            return _code_identity(value)
        if value is None or type(value) in (str, bool, int, float):
            return value
        if type(value) is bytes:
            return {"bytes": value.hex()}
        if type(value) is tuple:
            return [constant(x) for x in value]
        if type(value) is frozenset:
            return {"frozenset": sorted((repr(x) for x in value))}
        return {"constant": repr(value)}

    return {
        "bytecode": code.co_code.hex(),
        "constants": [constant(x) for x in code.co_consts],
        "names": list(code.co_names),
        "variables": list(code.co_varnames),
        "freevars": list(code.co_freevars),
        "argcount": code.co_argcount,
        "posonlyargcount": code.co_posonlyargcount,
        "kwonlyargcount": code.co_kwonlyargcount,
        "flags": code.co_flags,
    }


def _implementation(callback):
    if not inspect.isfunction(callback) or "<lambda>" in callback.__qualname__:
        raise SearchRejected("named inspectable trusted function required")
    path = inspect.getsourcefile(callback)
    if not path or not Path(path).is_file():
        raise SearchRejected("trusted implementation source unavailable")
    return {
        "module": callback.__module__,
        "qualname": callback.__qualname__,
        "source_sha256": hashlib.sha256(Path(path).read_bytes()).hexdigest(),
        "loaded_code_sha256": content_hash(_code_identity(callback.__code__)),
    }


def _stop(local_stop, external_stop, deadline):
    if (
        local_stop.is_set()
        or external_stop.is_set()
        or datetime.now(timezone.utc) >= datetime.fromisoformat(deadline.replace("Z", "+00:00"))
    ):
        raise SearchRejected("execution stopped or deadline exceeded")


class SearchHandler:
    def __init__(self, provider: SearchProvider):
        if not isinstance(provider, SearchProvider):
            raise TypeError("registered SearchProvider required")
        self.provider = provider

    def execution_hashes(self, dependencies, *, operation):
        if operation != "search_layouts":
            raise SearchRejected("unsupported operation")
        p = self.provider
        # Manifests must contain identities of all additional code and inputs,
        # including implementation files and mutable configuration. Resolver
        # dependencies themselves are bound separately as a complete snapshot.
        return {
            "dependencies": content_hash(dependencies),
            "producer": content_hash(
                {
                    "implementation": _implementation(p.produce),
                    "manifest_function": _implementation(p.producer_manifest),
                    "manifest": p.producer_manifest(deepcopy(dependencies)),
                }
            ),
            "validator": content_hash(
                {
                    "implementation": _implementation(p.validate),
                    "manifest_function": _implementation(p.validator_manifest),
                    "manifest": p.validator_manifest(deepcopy(dependencies)),
                }
            ),
        }

    def __call__(self, job, context, reserved_run_id, local_stop, external_stop):
        deadline = context["deadline_utc"]
        _stop(local_stop, external_stop, deadline)
        req = JobRequest.model_validate(context["request"]).root
        identity = context["identity"]
        scenario = Scenario.model_validate(identity["scenario"])
        ref = ScenarioRef(
            scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope
        )
        if (
            job.operation != "search_layouts"
            or req.operation != job.operation
            or req.request_id != job.request_id
            or req.scenario_ref != ref
            or identity["operation"] != req.operation
            or identity["arguments"] != req.arguments.model_dump(mode="json")
            or (scenario.scenario_id, scenario.revision, scenario.scope)
            != (ref.scenario_id, ref.revision, ref.scope)
            or content_hash(identity) != job.input_fingerprint
            or datetime.fromisoformat(deadline.replace("Z", "+00:00"))
            > datetime.fromisoformat(scenario.input.search.deadline_utc.replace("Z", "+00:00"))
        ):
            raise SearchRejected("admitted identity mismatch")

        def resolve():
            deps, hashes = self.provider.resolve_dependencies(ref, operation="search_layouts")
            if any(k.startswith("execution:") for k in hashes):
                raise SearchRejected("reserved execution hash namespace")
            expected = dict(hashes)
            expected.update(
                {
                    "execution:" + k: v
                    for k, v in self.execution_hashes(deps, operation="search_layouts").items()
                }
            )
            if expected != identity["content_hashes"] or deps["scenario"] != identity["scenario"]:
                raise SearchRejected("execution inputs or implementation changed")
            return deps

        deps = resolve()
        raw = self.provider.produce(
            deepcopy(deps), job, deepcopy(context), reserved_run_id, local_stop, external_stop
        )
        _stop(local_stop, external_stop, deadline)
        result = Result.model_validate_json(
            raw.model_dump_json()
            if isinstance(raw, Result)
            else __import__("json").dumps(raw, allow_nan=False)
        )
        if (
            result.run_id != reserved_run_id
            or result.source_job_id != job.job_id
            or result.input_snapshot_ref != ref
            or result.input_fingerprint != job.input_fingerprint
            or result.operation != req.operation
            or result.arguments != req.arguments
            or result.provenance.source_hashes != identity["content_hashes"]
            or result.provenance.evaluator_version != scenario.input.numerics.evaluator_version
            or result.provenance.solar_version != scenario.input.numerics.solar_version
            or result.provenance.search_version != scenario.input.search.version
            or result.provenance.seed != scenario.input.search.seed
        ):
            raise SearchRejected("result identity mismatch")
        verdict = self.provider.validate(deepcopy(deps), result, local_stop, external_stop)
        _stop(local_stop, external_stop, deadline)
        self._check(result, verdict, deps, scenario, ref)
        resolve()
        _stop(local_stop, external_stop, deadline)
        return result

    @staticmethod
    def _check(result, verdict, deps, scenario, ref):
        if (
            type(verdict) is not SearchVerdict
            or type(verdict.proof_verified) is not bool
            or (verdict.target_met is not None and type(verdict.target_met) is not bool)
            or type(verdict.layouts) is not tuple
        ):
            raise SearchRejected("invalid independent verdict")
        if (
            verdict.outcome != result.analytical_outcome
            or result.analytical_outcome == "comparison_completed"
        ):
            raise SearchRejected("outcome not independently verified")
        if result.analytical_outcome == "proven_infeasible_finite_model" and (
            not verdict.proof_verified or result.finite_model_proof is None
        ):
            raise SearchRejected("exact proof not independently verified")
        target = scenario.input.objective.kind == "minimise_cost_for_target"
        if (
            target
            and result.analytical_outcome in ("feasible_candidate", "feasible_zero_planting")
            and verdict.target_met is not True
        ):
            raise SearchRejected("target not independently verified")
        if target and result.analytical_outcome in ("feasible_candidate", "feasible_zero_planting"):
            for selected in (item for item in result.layouts if item.selected):
                matching = [
                    m
                    for m in result.metrics
                    if m.scenario_ref == ref
                    and m.layout_id == selected.layout.layout_id
                    and m.case_id == scenario.input.objective.primary_case_id
                    and m.metric_id == "additional_shade"
                    and m.target_id is None
                    and m.quantity_kind == scenario.input.objective.quantity_kind
                ]
                if (
                    len(matching) != 1
                    or matching[0].value < scenario.input.objective.target_gain_m2_h
                ):
                    raise SearchRejected("target metric absent or below target")
        if result.analytical_outcome == "search_exhausted_without_target" and (
            not target or verdict.target_met is not False
        ):
            raise SearchRejected("target miss not independently verified")
        by_id = {}
        for v in verdict.layouts:
            if (
                type(v) is not LayoutVerdict
                or v.layout_id in by_id
                or type(v.cost_pence) is not int
                or type(v.constraints) is not tuple
            ):
                raise SearchRejected("invalid layout verdict")
            by_id[v.layout_id] = v
        if len(by_id) != len(result.layouts):
            raise SearchRejected("missing independent layout verdict")
        for layout in result.layouts:
            v = by_id.get(layout.layout.layout_id)
            if v is None or layout.scenario_ref != ref:
                raise SearchRejected("layout identity mismatch")
            try:
                cost = sum(
                    deps["profiles"][p.profile_id]["cost_pence"] for p in layout.layout.placements
                )
            except (KeyError, TypeError) as exc:
                raise SearchRejected("unresolved profile cost") from exc
            records = tuple(
                c.model_dump(mode="json")
                for c in result.constraints
                if c.scenario_ref == ref and c.layout_id == layout.layout.layout_id
            )
            if (
                type(cost) is not int
                or cost != layout.cost_pence
                or cost != v.cost_pence
                or v.feasibility != layout.feasibility
                or records != v.constraints
                or (
                    layout.feasibility == "feasible" and any(c["status"] == "fail" for c in records)
                )
            ):
                raise SearchRejected("independent feasibility or cost mismatch")
            if layout.selected and not any(
                m.scenario_ref == ref and m.layout_id == layout.layout.layout_id
                for m in result.metrics
            ):
                raise SearchRejected("selected layout requires an actual reported metric")
            if layout.feasibility == "feasible" and (
                cost > scenario.input.constraints.budget_pence
                or (
                    scenario.input.constraints.max_tree_count is not None
                    and layout.tree_count > scenario.input.constraints.max_tree_count
                )
            ):
                raise SearchRejected("budget or count exceeded")
