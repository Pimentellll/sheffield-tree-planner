"""Trusted, synthetic-only adapter for the audited one-tree reference calculation.

The server supplies both dependency resolution and already-resolved numerical inputs.
No imports, paths, geometry, or callbacks are accepted from a request.
"""

from dataclasses import dataclass, fields, is_dataclass
from collections.abc import Mapping
from datetime import datetime, timezone
from types import CodeType
from time import perf_counter
from math import isfinite
from typing import Any, Callable

from tree_planner.canonical import content_hash
from tree_planner.contracts import JobRequest, Scenario, ScenarioRef, Result
from tree_planner.contracts.profiles import Layout, TreeProfile


class ReferenceUnsupported(ValueError):
    """The requested calculation cannot be established by this provider."""


@dataclass(frozen=True)
class ReferenceInputs:
    scenario_ref: ScenarioRef
    layout_id: str
    layout_revision: int
    placement_id: str
    case_id: str
    horizon_years: float
    target_id: str
    samples: tuple[Any, ...]
    bins: tuple[Any, ...]
    obstacles: tuple[Any, ...]
    tree: Any


@dataclass(frozen=True)
class ReferenceProvider:
    # resolve_dependencies must call the authoritative service each time.
    resolve_dependencies: Callable
    resolve_inputs: Callable
    evaluate: Callable
    evaluator: str
    evaluator_version: str
    solar_algorithm: str
    solar_version: str
    # Hashes of the actual trusted numerical source files, verified by server setup.
    numerical_source_hashes: tuple[tuple[str, str], ...]
    verify_implementation: Callable[[], Mapping[str, str]] | None = None
    # Explicit opt-in for boundary tests; this does not prove producer-source trust.
    synthetic_stub: bool = False

    def __post_init__(self):
        if not all(
            callable(x) for x in (self.resolve_dependencies, self.resolve_inputs, self.evaluate)
        ):
            raise ValueError("trusted dependency, numerical input and evaluator callables required")
        if not self.numerical_source_hashes or any(
            not name or len(sha) != 64 or any(c not in "0123456789abcdef" for c in sha)
            for name, sha in self.numerical_source_hashes
        ):
            raise ValueError("verified numerical source hashes required")


def numerical_identity(value):
    """Lossless canonical form of the resolved immutable numerical dataclasses."""
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, datetime):
        return value.isoformat()
    if is_dataclass(value) and not isinstance(value, type):
        return {
            "type": type(value).__name__,
            **{
                field.name: numerical_identity(getattr(value, field.name))
                for field in fields(value)
            },
        }
    if isinstance(value, tuple):
        return [numerical_identity(item) for item in value]
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise ReferenceUnsupported("unsupported numerical identity value")


def _code_identity(value):
    # marshal reference/intern flags can vary after a function executes. Hash
    # explicit immutable code fields instead of interpreter serialization state.
    if isinstance(value, CodeType):
        return {
            "code": value.co_code.hex(),
            "constants": [_code_identity(v) for v in value.co_consts],
            "names": list(value.co_names),
            "variables": list(value.co_varnames),
            "free": list(value.co_freevars),
            "cells": list(value.co_cellvars),
            "flags": value.co_flags,
            "args": value.co_argcount,
            "posonly": value.co_posonlyargcount,
            "kwonly": value.co_kwonlyargcount,
            "exceptions": value.co_exceptiontable.hex(),
        }
    if isinstance(value, bytes):
        return {"bytes": value.hex()}
    if isinstance(value, tuple):
        return [_code_identity(v) for v in value]
    if value is None or type(value) in (str, bool, int, float):
        return value
    raise ReferenceUnsupported("unsupported stub code constant")


def _now():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _check_stop(local_stop, external_stop, deadline):
    if local_stop.is_set() or external_stop.is_set():
        raise ReferenceUnsupported("execution stopped")
    if datetime.now(timezone.utc) >= datetime.fromisoformat(deadline.replace("Z", "+00:00")):
        raise ReferenceUnsupported("deadline exceeded")


class ReferenceJobHandler:
    def __init__(self, provider: ReferenceProvider):
        if not isinstance(provider, ReferenceProvider):
            raise TypeError("trusted ReferenceProvider required")
        self.provider = provider

    def execution_hashes(self, dependencies, *, operation: str) -> Mapping[str, str]:
        """Resolve numerical content without recursing through application admission."""
        if operation != "evaluate_layout":
            raise ReferenceUnsupported("only synthetic evaluate_layout is supported")
        provider = self.provider
        if provider.verify_implementation is not None:
            implementation = dict(provider.verify_implementation())
        elif provider.synthetic_stub:
            # Code bytes and actual resolved inputs are hashed, but closure/global
            # integrity and actual numerical-source loading are NOT proved here.
            implementation = {
                "trust": "explicit non-production synthetic stub",
                **{
                    name: content_hash(_code_identity(fn.__code__))
                    for name, fn in (
                        ("inputs", provider.resolve_inputs),
                        ("evaluate", provider.evaluate),
                    )
                },
            }
        else:
            raise ReferenceUnsupported("verified implementation required")
        for name, fn in (
            ("inputs", provider.resolve_inputs),
            ("evaluate", provider.evaluate),
            ("handler", type(self).__call__),
            ("identity", type(self).execution_hashes),
        ):
            implementation["loaded:" + name] = content_hash(_code_identity(fn.__code__))
        scenario = Scenario.model_validate(dependencies["scenario"])
        request = JobRequest.model_validate(
            dict(
                request_id="execution-identity",
                scenario_ref={
                    k: getattr(scenario, k) for k in ("scenario_id", "revision", "scope")
                },
                operation=operation,
                arguments={
                    "layout_ref": scenario.input.proposed_layout_ref.model_dump(mode="json")
                },
            )
        ).root
        resolved = provider.resolve_inputs(dependencies, request)
        if not isinstance(resolved, ReferenceInputs):
            raise ReferenceUnsupported("ReferenceInputs required")
        return {
            "implementation": content_hash(implementation),
            "numerical_inputs": content_hash(numerical_identity(resolved)),
            "binding": content_hash(dependencies),
            "configuration": content_hash(
                dict(
                    evaluator=provider.evaluator,
                    evaluator_version=provider.evaluator_version,
                    solar_algorithm=provider.solar_algorithm,
                    solar_version=provider.solar_version,
                    numerical_sources=dict(provider.numerical_source_hashes),
                    synthetic_stub=provider.synthetic_stub,
                )
            ),
        }

    def __call__(self, job, context, reserved_run_id, local_stop, external_stop):
        _check_stop(local_stop, external_stop, context["deadline_utc"])
        request = JobRequest.model_validate(context["request"]).root
        identity = context["identity"]
        scenario = Scenario.model_validate(identity["scenario"])
        ref = ScenarioRef(
            scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope
        )
        if (
            job.operation != "evaluate_layout"
            or request.operation != job.operation
            or request.scenario_ref != ref
            or request.request_id != job.request_id
            or identity["operation"] != request.operation
            or identity["arguments"] != request.arguments.model_dump(mode="json")
            or (scenario.scenario_id, scenario.revision, scenario.scope)
            != (ref.scenario_id, ref.revision, ref.scope)
            or content_hash(identity) != job.input_fingerprint
        ):
            raise ReferenceUnsupported("job identity or operation mismatch")
        deps, hashes = self.provider.resolve_dependencies(ref, operation=job.operation)
        if hashes != identity["content_hashes"] or deps["scenario"] != identity["scenario"]:
            raise ReferenceUnsupported("admitted dependencies changed")
        inp = scenario.input
        n = inp.numerics
        if (
            deps["site"]["site_kind"] != "synthetic_test"
            or (n.evaluator, n.evaluator_version, n.solar_algorithm, n.solar_version)
            != (
                self.provider.evaluator,
                self.provider.evaluator_version,
                self.provider.solar_algorithm,
                self.provider.solar_version,
            )
            or inp.objective.quantity_kind != "geometric"
            or len(inp.evaluation_cases) != 1
        ):
            raise ReferenceUnsupported("unsupported site, numerical model or cases")
        case = inp.evaluation_cases[0]
        if (
            len(case.target_ids) != 1
            or case.area_basis != "surface"
            or case.weather_ref is not None
        ):
            raise ReferenceUnsupported("unsupported target or case")
        layout = Layout.model_validate(deps["layout"])
        if (
            request.arguments.layout_ref != inp.proposed_layout_ref
            or (layout.layout_id, layout.revision)
            != (request.arguments.layout_ref.layout_id, request.arguments.layout_ref.revision)
            or len(layout.placements) != 1
        ):
            raise ReferenceUnsupported("exactly one scenario-bound placement required")
        placement = layout.placements[0]
        profile = TreeProfile.model_validate(deps["profiles"][placement.profile_id])
        state = profile.states.get(case.profile_state)
        if (
            state is None
            or state.horizon_years != case.horizon_years
            or state.attenuation.mode != "opaque"
        ):
            raise ReferenceUnsupported("unsupported profile state")
        resolved = self.provider.resolve_inputs(deps, request)
        if content_hash(numerical_identity(resolved)) != hashes.get("execution:numerical_inputs"):
            raise ReferenceUnsupported("numerical inputs changed after admission")
        if not isinstance(resolved, ReferenceInputs) or (
            resolved.scenario_ref,
            resolved.layout_id,
            resolved.layout_revision,
            resolved.placement_id,
            resolved.case_id,
            resolved.horizon_years,
            resolved.target_id,
        ) != (
            ref,
            layout.layout_id,
            layout.revision,
            placement.placement_id,
            case.case_id,
            case.horizon_years,
            case.target_ids[0],
        ):
            raise ReferenceUnsupported("numerical input binding mismatch")
        if not resolved.samples or {s.target_id for s in resolved.samples} != {resolved.target_id}:
            raise ReferenceUnsupported("receiver target mismatch")
        expected_bins = [
            (datetime.fromisoformat(b.midpoint_utc.replace("Z", "+00:00")), b.duration_h)
            for b in case.time_bins
        ]
        if [(b.midpoint_utc, b.duration_h) for b in resolved.bins] != expected_bins:
            raise ReferenceUnsupported("solar bin mismatch")
        # The trusted provider owns the coordinate convention; verify its explicit tree
        # against the typed placement and profile, without deriving axes or terrain.
        tree = resolved.tree
        x, y, z = placement.position_enu_m
        if (
            tuple(tree.crown.center_enu_m) != (x, y, z + state.crown_center_height_m)
            or tuple(tree.crown.radii_m) != tuple(state.crown_radii_m)
            or (
                tree.trunk.center_east_m,
                tree.trunk.center_north_m,
                tree.trunk.base_up_m,
                tree.trunk.radius_m,
                tree.trunk.height_m,
            )
            != (x, y, z, state.trunk_radius_m, state.trunk_height_m)
        ):
            raise ReferenceUnsupported("tree/profile geometry mismatch")
        _check_stop(local_stop, external_stop, context["deadline_utc"])
        started = _now()
        tick = perf_counter()
        output = self.provider.evaluate(
            resolved.samples, resolved.bins, resolved.obstacles, tree, ray_offset_m=n.ray_offset_m
        )
        elapsed = perf_counter() - tick
        finished = _now()
        _check_stop(local_stop, external_stop, context["deadline_utc"])
        deps_after, hashes_after = self.provider.resolve_dependencies(ref, operation=job.operation)
        if (
            hashes_after != hashes
            or deps_after["scenario"] != identity["scenario"]
            or content_hash(numerical_identity(resolved)) != hashes["execution:numerical_inputs"]
        ):
            raise ReferenceUnsupported("dependencies changed during calculation")
        _check_stop(local_stop, external_stop, context["deadline_utc"])
        value = output.additional_useful_shade_m2_h
        if (
            not all(
                isfinite(v)
                for v in (value, output.baseline_direct_sun_m2_h, output.proposal_direct_sun_m2_h)
            )
            or output.sample_count != len(resolved.samples)
            or output.bin_count != len(resolved.bins)
            or value < 0
            or output.baseline_direct_sun_m2_h < output.proposal_direct_sun_m2_h
            or abs(value - (output.baseline_direct_sun_m2_h - output.proposal_direct_sun_m2_h))
            > 1e-9
        ):
            raise ReferenceUnsupported("invalid numerical calculation")
        return Result.model_validate(
            dict(
                schema_version="0.1.0",
                run_id=reserved_run_id,
                source_job_id=job.job_id,
                scenario_id=ref.scenario_id,
                scenario_revision=ref.revision,
                scope=ref.scope,
                input_fingerprint=job.input_fingerprint,
                input_snapshot_ref=ref,
                operation=job.operation,
                arguments=request.arguments,
                analytical_outcome="comparison_completed",
                layouts=[
                    dict(
                        layout=layout,
                        scenario_ref=ref,
                        role="alternative",
                        cost_pence=profile.cost_pence,
                        tree_count=1,
                        feasibility="not_evaluated",
                        reasons=["Constraints not evaluated"],
                        selected=False,
                    )
                ],
                metrics=[
                    dict(
                        metric_instance_id="additional-shade",
                        metric_id="additional_shade",
                        scenario_ref=ref,
                        value=value,
                        unit="m2_h",
                        layout_id=layout.layout_id,
                        case_id=case.case_id,
                        target_id=resolved.target_id,
                        horizon_years=case.horizon_years,
                        weighting="unweighted",
                        quantity_kind="geometric",
                    )
                ],
                missing_metrics=[],
                comparison=None,
                constraints=[
                    dict(
                        scenario_ref=ref,
                        layout_id=layout.layout_id,
                        case_id=None,
                        rule="site_and_planting_constraints",
                        limit=None,
                        observed_value=None,
                        unit=None,
                        status="unknown",
                        evidence=[],
                    )
                ],
                assumptions=list(inp.assumptions)
                + [
                    f"Numerical source {name} sha256 {sha}"
                    for name, sha in self.provider.numerical_source_hashes
                ],
                limitations=[
                    "Synthetic reference only",
                    "Plantability and other constraints not evaluated",
                    "No temperature, energy or carbon calculation",
                ]
                + (
                    [
                        "Non-production synthetic stub: input/code identity checked; closure/global and producer loading trust not established"
                    ]
                    if self.provider.synthetic_stub
                    else []
                ),
                source_ids=list(case.source_ids),
                finite_model_proof=None,
                provenance=dict(
                    tool_version="synthetic-reference-adapter-1",
                    evaluator_version=n.evaluator_version,
                    solar_version=n.solar_version,
                    search_version=inp.search.version,
                    seed=inp.search.seed,
                    schema_version="0.1.0",
                    created_at_utc=_now(),
                    compute_started_at_utc=started,
                    compute_finished_at_utc=finished,
                    timings_s={"evaluation": elapsed},
                    physics_device=None,
                    inference_device=None,
                    source_hashes=hashes,
                    execution_mode="live",
                ),
            )
        )
