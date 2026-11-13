"""Compact, model-facing views of async Job/Result observations.

``AgentLoop._dispatch`` returns async observations shaped exactly as
``{"job": Job.model_dump(mode="json")}`` or
``{"job": ..., "result": Result.model_dump(mode="json")}`` and the loop sends
``json.dumps(observation, ensure_ascii=False, allow_nan=False)`` to the model. A search
or comparison Result is mostly repeated metric/constraint records, so that message can
dominate the model's context.

This module builds a smaller *view* of that same observation for the model only.

* The full Job/Result is never modified. The host keeps it as the only authority for
  ``_conclusion``, evidence checks, scoring, storage and UI. The view says so.
* Nothing is invented. Values are copied from the validated record or computed
  deterministically from it (``result_attached``, ``status_counts``, pass counts, delta rows
  resolved through the record's own metric instances). ``currentness`` is the *caller's*
  assertion and is labelled as such. The current delivery mode is
  ``job.delivery.execution_mode``; ``result.provenance.source_execution_mode`` is only the
  original computation's mode, so a cache hit never looks live. Supersession stays the
  separate ``superseded_by_revision`` marker beside the contract ``status``; no derived
  state is shown. The model is told to cite ``job_id``, because AgentLoop does not accept
  a superseded job's ``run_id`` as evidence. Fields left out are listed
  in ``omitted`` with a count, their path in the full record and the existing
  ``run_id``/``job_id`` that holds them; entries for fields that only repeat values already
  shown say so. No storage reference, pagination tool, metric or status is created.
* Size is measured in UTF-8 bytes of the same serialization the loop uses. Bytes are not
  tokens: fitting a byte budget does not prove a token limit (for example the 8,192-token
  rule), which stays with the native runtime and its reported usage.
* If even the smallest view does not fit, :class:`ObservationBudgetError` is raised with
  that smallest size. A view is never string-truncated and never broken JSON.
* Shapes that are not the current async observation contract, or that the loop could not
  have produced (a Result attached to a non-completed or superseded Job), raise
  :class:`ObservationViewError` instead of being made plausible.

A Result-bearing view is much smaller than the full record. A Job-only view (queued,
running, failed, cancelled, or superseded) can be a few hundred bytes larger than the raw
Job dump, because it adds the authority notice and omission list; it has a single level.

Proposed call site (not wired here; ``agents/__init__.py`` is owned by the integrator).
In ``AgentLoop.continue_run``, where the tool message content is built from the value
``observation = self._dispatch(name, ...)``::

    if name in _ASYNC:
        try:
            observation = compact_async_observation(
                observation,
                budget_bytes=<configured budget>,
                result_validated_at_delivery="result" in observation,
            )
        except ObservationViewError as exc:
            # Fail-closed: this ends the whole run (byte detail kept in Outcome.reason).
            # The alternative, a typed refusal message to the model, is Ben's decision.
            raise ProtocolError(f"observation view refused: {exc}") from exc
    content = json.dumps(observation, ensure_ascii=False, allow_nan=False)

``"result" in observation`` is the loop's own guarantee: ``_dispatch`` attaches a Result
only after ``validate_delivery_currentness`` passed for it. ``self.jobs``/``self.results``
keep the full records and are unchanged.
"""

from __future__ import annotations

from collections.abc import Mapping
import json
from typing import Any

from pydantic import ValidationError

from tree_planner.contracts import Job, Result, ScenarioRef

VIEW_SCHEMA = "canopy-observation-view/1"
LEVELS = ("full", "reduced", "essential")
JOB_ONLY_LEVEL = "job_only"

AUTHORITY = (
    "Model-facing view. The host keeps the full Job/Result as the only authority. Cite "
    "job.job_id as evidence; never cite the run_id of a job whose superseded_by_revision is "
    "set. Items listed in 'omitted' exist only in the full record named by their "
    "'authoritative' ID."
)
CONVENTIONS = (
    "Rows follow their 'columns'. A row without a trailing scenario_ref, or a delta with a "
    "null scenario_ref, belongs to result.scenario_ref. target_id null is the aggregate over "
    "targets. A metric listed in missing_metrics was not computed; one counted in 'omitted' "
    "was computed but is not shown; one in neither was not produced for that case/layout "
    "(not applicable or unsupported). None of these means zero."
)

_METRIC_COLUMNS = [
    "layout_id",
    "metric_id",
    "case_id",
    "target_id",
    "horizon_years",
    "value",
    "unit",
    "quantity_kind",
    "weighting",
    "area_basis",
    "aggregation_basis",
    "scenario_ref?",
]
_CONSTRAINT_COLUMNS = [
    "layout_id",
    "case_id",
    "rule",
    "status",
    "observed_value",
    "limit",
    "unit",
    "evidence",
    "scenario_ref?",
]
_DELTA_COLUMNS = [
    "metric_id",
    "case_id",
    "target_id",
    "horizon_years",
    "quantity_kind",
    "weighting",
    "area_basis",
    "base_aggregation_basis",
    "alternative_aggregation_basis",
    "base_layout_id",
    "base_scenario_ref",
    "alternative_layout_id",
    "alternative_scenario_ref",
    "base_value",
    "alternative_value",
    "delta",
    "unit",
]


class ObservationViewError(ValueError):
    """The input is not a current async observation, or is internally inconsistent."""


class ObservationBudgetError(ObservationViewError):
    """Even the smallest view exceeds the caller's byte budget. Nothing is returned."""

    def __init__(self, required_bytes: int, budget_bytes: int):
        self.required_bytes = required_bytes
        self.budget_bytes = budget_bytes
        super().__init__(
            f"smallest observation view needs {required_bytes} bytes; budget is {budget_bytes}"
        )


def observation_bytes(value: Any) -> int:
    """UTF-8 size of ``value`` under the serialization AgentLoop uses for tool messages."""
    try:
        text = json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as exc:
        raise ObservationViewError(f"value is not finite JSON: {exc}") from exc
    return len(text.encode("utf-8"))


def compact_async_observation(
    observation: Mapping[str, Any],
    *,
    budget_bytes: int,
    result_validated_at_delivery: bool,
) -> dict:
    """Return the richest view of an async observation that fits ``budget_bytes``.

    With a Result, tries ``full``, then ``reduced``, then ``essential`` and returns the
    first whose serialized size is within the budget; a Job-only observation has the
    single level ``job_only``. Raises :class:`ObservationBudgetError` (carrying the
    smallest size) if nothing fits, and :class:`ObservationViewError` for any input that
    is not exactly the current ``{"job"}`` / ``{"job", "result"}`` shape.

    ``result_validated_at_delivery`` must be True when, and only when, the caller attached
    the Result after ``validate_delivery_currentness`` passed (AgentLoop's own rule). The
    view reports it; this pure function cannot check currentness itself.
    """
    if type(budget_bytes) is not int or budget_bytes <= 0:
        raise ValueError("budget_bytes must be a positive integer")
    _check_flag(result_validated_at_delivery)
    job, result = _parse(observation, result_validated_at_delivery)
    smallest = None
    for level in _levels(result):
        view = _build(job, result, level, result_validated_at_delivery)
        size = observation_bytes(view)
        if size <= budget_bytes:
            return view
        smallest = size if smallest is None else min(smallest, size)
    raise ObservationBudgetError(smallest, budget_bytes)


def view_sizes(observation: Mapping[str, Any], *, result_validated_at_delivery: bool) -> dict:
    """Serialized UTF-8 size of the raw observation and of each view level (diagnostics)."""
    _check_flag(result_validated_at_delivery)
    job, result = _parse(observation, result_validated_at_delivery)
    sizes = {"observation": observation_bytes({key: observation[key] for key in observation})}
    for level in _levels(result):
        sizes[level] = observation_bytes(_build(job, result, level, result_validated_at_delivery))
    return sizes


def _check_flag(value) -> None:
    if type(value) is not bool:
        raise ValueError("result_validated_at_delivery must be a bool")


def _levels(result) -> tuple[str, ...]:
    return LEVELS if result is not None else (JOB_ONLY_LEVEL,)


# --------------------------------------------------------------------------- parsing


def _parse(observation, validated: bool) -> tuple[Job, Result | None]:
    if not isinstance(observation, Mapping):
        raise ObservationViewError("observation must be a mapping")
    keys = set(observation)
    if keys not in ({"job"}, {"job", "result"}):
        raise ObservationViewError(
            f"unsupported observation keys {sorted(map(str, keys))}; expected job[, result]"
        )
    try:
        # Validation builds new model objects; the caller's mapping is only read.
        job = Job.model_validate(observation["job"])
        result = Result.model_validate(observation["result"]) if "result" in keys else None
    except ValidationError as exc:
        raise ObservationViewError(
            "observation does not match the current Job/Result contract "
            f"({exc.error_count()} errors)"
        ) from exc
    if result is not None:
        if (
            job.status != "completed"
            or job.superseded_by_revision is not None
            or job.delivery is None
            or job.run_id != result.run_id
            or job.delivery.source_job_id != result.source_job_id
            or job.operation != result.operation
            or job.input_fingerprint != result.input_fingerprint
            or result.input_snapshot_ref != _job_ref(job)
        ):
            raise ObservationViewError(
                "an attached Result must belong to this completed, non-superseded Job"
            )
    elif validated:
        raise ObservationViewError("no Result is attached, so none was validated at delivery")
    return job, result


# --------------------------------------------------------------------------- building


def _ref(ref: ScenarioRef) -> dict:
    return {"scenario_id": ref.scenario_id, "revision": ref.revision, "scope": ref.scope}


def _job_ref(job: Job) -> ScenarioRef:
    return ScenarioRef(scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope)


def _job_view(job: Job, has_result: bool) -> dict:
    # Only the contract's own status and the orthogonal superseded_by_revision marker are
    # shown (CONTRACTS, BUILD D04); no derived state that could hide supersession.
    view = {
        "job_id": job.job_id,
        "operation": job.operation,
        "status": job.status,
        "result_attached": has_result,
        "scenario_ref": _ref(_job_ref(job)),
        "input_fingerprint": job.input_fingerprint,
        "view_slot": job.view_slot,
        "selection_seq": job.selection_seq,
        "run_id": job.run_id,
        "superseded_by_revision": job.superseded_by_revision,
        "cancel_requested": job.cancel_requested,
    }
    if job.delivery is not None:
        view["delivery"] = {
            "execution_mode": job.delivery.execution_mode,
            "source_job_id": job.delivery.source_job_id,
        }
    if job.progress is not None:
        view["progress"] = job.progress.model_dump(mode="json")
    if job.error is not None:
        view["error"] = {
            "code": job.error.code,
            "message": job.error.message,
            "retryable": job.error.retryable,
            "field_errors": [e.model_dump(mode="json") for e in job.error.field_errors],
            "details": dict(sorted(job.error.details.items())),
        }
    return view


def _omitted(path: str, count: int, reason: str, holder: dict) -> dict:
    return {"path": path, "count": count, "reason": reason, "authoritative": holder}


def _add(omitted: list, path: str, count: int, reason: str, holder: dict) -> None:
    if count:
        omitted.append(_omitted(path, count, reason, holder))


def _build(job: Job, result: Result | None, level: str, validated: bool) -> dict:
    view: dict[str, Any] = {
        "view": VIEW_SCHEMA,
        "level": level,
        "authority": AUTHORITY,
        "job": _job_view(job, result is not None),
    }
    omitted: list = []
    bookkeeping = [job.schema_version, job.request_id, job.created_at_utc]
    bookkeeping += [job.started_at_utc, job.finished_at_utc]
    if job.delivery is not None:
        bookkeeping += [job.delivery.delivered_at_utc]
    _add(
        omitted,
        "job.schema_version, job.request_id, job timestamps, job.delivery.delivered_at_utc",
        sum(value is not None for value in bookkeeping),
        "schema, request and timing bookkeeping",
        {"job_id": job.job_id},
    )
    if job.delivery is not None:
        _add(
            omitted,
            "job.delivery job_id/run_id/scenario/input_fingerprint/view_slot/selection_seq",
            8,
            "delivery identity fields that repeat the job identity shown above",
            {"job_id": job.job_id},
        )
    if result is not None:
        view["conventions"] = CONVENTIONS
        view["result"] = _result_view(result, level, validated, omitted)
    view["omitted"] = omitted
    return view


def _focus_layouts(result: Result) -> set:
    """Selected layouts; when none is selected every layout is equally in focus."""
    selected = [e for e in result.layouts if e.selected]
    return {(e.scenario_ref, e.layout.layout_id) for e in (selected or result.layouts)}


def _quantity(m) -> tuple:
    """Everything that identifies one physical quantity, apart from its target."""
    return (
        m.scenario_ref,
        m.layout_id,
        m.metric_id,
        m.case_id,
        m.horizon_years,
        m.unit,
        m.quantity_kind,
        m.weighting,
        m.area_basis,
        m.aggregation_basis,
    )


def _result_view(result: Result, level: str, validated: bool, omitted: list) -> dict:
    holder = {"run_id": result.run_id}
    default = result.input_snapshot_ref
    focus = _focus_layouts(result)
    by_instance = {m.metric_instance_id: m for m in result.metrics}
    p = result.provenance

    def ref_or_none(ref: ScenarioRef):
        return None if ref == default else _ref(ref)

    view: dict[str, Any] = {
        "run_id": result.run_id,
        "source_job_id": result.source_job_id,
        "operation": result.operation,
        "arguments": result.arguments.model_dump(mode="json"),
        "analytical_outcome": result.analytical_outcome,
        "scenario_ref": _ref(default),
        "input_fingerprint": result.input_fingerprint,
        "currentness": "validated_at_delivery" if validated else "not_validated_by_caller",
        # The current delivery mode is job.delivery.execution_mode (CONTRACTS: a cache hit
        # must not look live); this is only the source computation's original mode.
        "provenance": {
            "source_execution_mode": p.execution_mode,
            "tool_version": p.tool_version,
            "evaluator_version": p.evaluator_version,
            "search_version": p.search_version,
            "solar_version": p.solar_version,
            "seed": p.seed,
        },
        "source_ids": list(result.source_ids),
        "limitations": list(result.limitations),
    }
    if result.finite_model_proof is not None:
        view["finite_model_proof"] = result.finite_model_proof.model_dump(mode="json")
    provenance_bookkeeping = [
        result.schema_version,
        *(e.layout.schema_version for e in result.layouts),
        p.schema_version,
        p.created_at_utc,
        p.compute_started_at_utc,
        p.compute_finished_at_utc,
        p.physics_device,
        p.inference_device,
        *p.timings_s,
    ]
    _add(
        omitted,
        "result.schema_version, layouts[].layout.schema_version, "
        "result.provenance schema/timestamps/devices/timings_s",
        sum(value is not None for value in provenance_bookkeeping),
        "schema and compute bookkeeping",
        holder,
    )

    # Layouts: descriptor always; placements for focus layouts (all layouts at full level).
    layouts, hidden_placements = [], 0
    for e in result.layouts:
        item = {
            "layout_id": e.layout.layout_id,
            "revision": e.layout.revision,
            "kind": e.layout.kind,
            "role": e.role,
            "selected": e.selected,
            "feasibility": e.feasibility,
            "reasons": list(e.reasons),
            "cost_pence": e.cost_pence,
            "tree_count": e.tree_count,
        }
        if level == "full" or (e.scenario_ref, e.layout.layout_id) in focus:
            item["placements"] = [
                {
                    "placement_id": pl.placement_id,
                    "candidate_id": pl.candidate_id,
                    "location_id": pl.location_id,
                    "position_enu_m": list(pl.position_enu_m),
                    "profile_id": pl.profile_id,
                    "pinned": pl.pinned,
                }
                for pl in e.layout.placements
            ]
        else:
            hidden_placements += len(e.layout.placements)
        if e.scenario_ref != default:
            item["scenario_ref"] = _ref(e.scenario_ref)
        layouts.append(item)
    view["layouts"] = layouts
    _add(
        omitted,
        "result.layouts[].layout.placements (layouts not in focus)",
        hidden_placements,
        "placement detail of layouts that are not selected",
        holder,
    )

    # Metrics: full keeps all; reduced drops target-level rows of non-focus layouts;
    # essential keeps focus layouts only, and drops a focus target row only when the very
    # same quantity has an aggregate (target_id null) row.
    aggregates = {_quantity(m) for m in result.metrics if m.target_id is None}
    rows, dropped_non_focus, dropped_target = [], 0, 0
    for m in result.metrics:
        in_focus = (m.scenario_ref, m.layout_id) in focus
        if level == "reduced" and not in_focus and m.target_id is not None:
            dropped_non_focus += 1
            continue
        if level == "essential":
            if not in_focus:
                dropped_non_focus += 1
                continue
            if m.target_id is not None and _quantity(m) in aggregates:
                dropped_target += 1
                continue
        row = [m.layout_id, m.metric_id, m.case_id, m.target_id, m.horizon_years, m.value]
        row += [m.unit, m.quantity_kind, m.weighting, m.area_basis, m.aggregation_basis]
        if m.scenario_ref != default:
            row.append(_ref(m.scenario_ref))
        rows.append(row)
    view["metrics"] = {"columns": list(_METRIC_COLUMNS), "rows": rows}
    _add(
        omitted,
        "result.metrics[].metric_instance_id (shown rows)",
        len(rows),
        "instance identifiers; comparison deltas below are resolved to metric fields",
        holder,
    )
    _add(
        omitted,
        "result.metrics (layouts not in focus)",
        dropped_non_focus,
        "computed metrics of layouts that are not selected"
        + (" (target-level rows only)" if level == "reduced" else ""),
        holder,
    )
    _add(
        omitted,
        "result.metrics (target-level rows of focus layouts)",
        dropped_target,
        "per-target breakdown; the aggregate row for the same quantity is shown",
        holder,
    )

    view["missing_metrics"] = []
    for mm in result.missing_metrics:
        item = {
            "layout_id": mm.layout_id,
            "case_id": mm.case_id,
            "metric_id": mm.metric_id,
            "reason": mm.reason,
        }
        if mm.scenario_ref != default:
            item["scenario_ref"] = _ref(mm.scenario_ref)
        view["missing_metrics"].append(item)

    # Constraints: every non-pass record is always kept; pass records are kept at full
    # level and counted per layout otherwise.
    constraint_rows, pass_counts = [], {}
    for c in result.constraints:
        if c.status == "pass" and level != "full":
            label = c.layout_id
            if c.scenario_ref != default:
                label += f"@{c.scenario_ref.scenario_id}:{c.scenario_ref.revision}"
            pass_counts[label] = pass_counts.get(label, 0) + 1
            continue
        row = [c.layout_id, c.case_id, c.rule, c.status, c.observed_value, c.limit, c.unit]
        row.append(list(c.evidence))
        if c.scenario_ref != default:
            row.append(_ref(c.scenario_ref))
        constraint_rows.append(row)
    view["constraints"] = {
        "columns": list(_CONSTRAINT_COLUMNS),
        "rows": constraint_rows,
        "status_counts": {
            status: sum(c.status == status for c in result.constraints)
            for status in ("pass", "fail", "unknown")
        },
    }
    if pass_counts:
        view["constraints"]["passed_not_listed_by_layout"] = pass_counts
    _add(
        omitted,
        "result.constraints (status pass)",
        sum(pass_counts.values()),
        "passed constraint records; counts per layout are shown",
        holder,
    )

    if result.comparison is not None:
        deltas = []
        for d in result.comparison.deltas:
            a = by_instance.get(d.base_metric_instance_id)
            b = by_instance.get(d.alternative_metric_instance_id)
            if a is None or b is None:
                raise ObservationViewError("comparison delta references a missing metric")
            # The contract makes both sides agree on metric, case, target, horizon, quantity
            # kind, weighting and area basis; aggregation basis is not forced, so show both.
            deltas.append(
                [a.metric_id, a.case_id, a.target_id, a.horizon_years]
                + [a.quantity_kind, a.weighting, a.area_basis]
                + [a.aggregation_basis, b.aggregation_basis]
                + [a.layout_id, ref_or_none(a.scenario_ref)]
                + [b.layout_id, ref_or_none(b.scenario_ref)]
                + [a.value, b.value, d.value, d.unit]
            )
        view["comparison"] = {
            "mode": result.comparison.mode,
            "changed_inputs": list(result.comparison.changed_inputs),
            "deltas": {"columns": list(_DELTA_COLUMNS), "rows": deltas},
        }
        _add(
            omitted,
            "result.comparison.deltas[] base/alternative_metric_instance_id, mode, changed_inputs",
            len(result.comparison.deltas),
            "instance IDs (resolved into each row) and per-delta mode/changed_inputs, which the "
            "contract requires to equal the comparison-level values shown",
            holder,
        )

    if level == "full":
        view["assumptions"] = list(result.assumptions)
        view["provenance"]["source_hashes"] = dict(sorted(p.source_hashes.items()))
    else:
        _add(
            omitted,
            "result.assumptions, result.provenance.source_hashes",
            len(result.assumptions) + len(p.source_hashes),
            "declared assumptions and source file hashes",
            holder,
        )
    return view
