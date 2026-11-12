"""Result schemas validate serialization and internal consistency, not physical truth."""

from typing import Literal

from pydantic import model_validator

from .base import (
    Array,
    ContractModel,
    Hash,
    ID,
    Map,
    Nonnegative,
    NonnegativeInt,
    Revision,
    UTC,
    unique,
)
from .operations import (
    AsyncOperation,
    CompareLocationsArguments,
    CompareScenariosArguments,
    EvaluateLayoutArguments,
    SearchLayoutsArguments,
    operation_slot,
)
from .profiles import Layout
from .scenario import AreaBasis, QuantityKind, ScenarioRef, Scope, Unit

ExecutionMode = Literal["live", "cached", "recorded", "fixture"]
ViewSlot = Literal["evaluation", "search", "comparison"]
ErrorCode = Literal[
    "INVALID_INPUT",
    "UNKNOWN_REVISION",
    "REVISION_CONFLICT",
    "RIGHTS_RESTRICTED",
    "RIGHTS_UNKNOWN",
    "SITE_NOT_READY",
    "UNSUPPORTED_OPERATION",
    "TOOL_UNAVAILABLE",
    "NUMERICAL_FAILURE",
    "RESULT_VALIDATION_FAILED",
    "WORKER_INTERRUPTED",
    "DEADLINE_EXCEEDED",
    "CANCELLED",
]


class FieldError(ContractModel):
    field: ID
    message: ID


class ContractError(ContractModel):
    code: ErrorCode
    message: ID
    retryable: bool
    field_errors: Array[FieldError]
    # Display-safe strings supplied by error mapper, never arbitrary exception data.
    details: Map[ID, str]


class Progress(ContractModel):
    completed: NonnegativeInt
    total: NonnegativeInt
    phase: ID
    unit: ID

    @model_validator(mode="after")
    def bounded(self):
        if self.completed > self.total:
            raise ValueError("completed work exceeds total")
        return self


class Delivery(ContractModel):
    job_id: ID
    run_id: ID
    source_job_id: ID
    scenario_id: ID
    scenario_revision: Revision
    scope: Scope
    input_fingerprint: Hash
    view_slot: ViewSlot
    selection_seq: Revision
    execution_mode: ExecutionMode
    delivered_at_utc: UTC

    @model_validator(mode="after")
    def live_source(self):
        if self.execution_mode == "live" and self.job_id != self.source_job_id:
            raise ValueError("live delivery must bind requesting and source job")
        return self


class Selection(ContractModel):
    scenario_ref: ScenarioRef
    view_slot: ViewSlot
    selection_seq: Revision
    accepted_job_id: ID


class Job(ContractModel):
    schema_version: Literal["0.1.0"]
    job_id: ID
    request_id: ID
    operation: AsyncOperation
    scenario_id: ID
    scenario_revision: Revision
    scope: Scope
    input_fingerprint: Hash
    view_slot: ViewSlot
    selection_seq: Revision
    status: Literal["queued", "running", "completed", "failed", "cancelled"]
    run_id: ID | None
    delivery: Delivery | None
    progress: Progress | None
    created_at_utc: UTC
    started_at_utc: UTC | None
    finished_at_utc: UTC | None
    error: ContractError | None
    cancel_requested: bool
    superseded_by_revision: Revision | None

    @model_validator(mode="after")
    def consistent(self):
        from datetime import datetime

        if operation_slot(self.operation) != self.view_slot:
            raise ValueError("operation/view slot mismatch")
        terminal = self.status in {"completed", "failed", "cancelled"}
        if terminal != (self.finished_at_utc is not None):
            raise ValueError("only terminal jobs require finished_at_utc")
        if self.status == "queued" and self.started_at_utc is not None:
            raise ValueError("queued job cannot have started timestamp")
        if self.status in {"running", "completed"} and self.started_at_utc is None:
            raise ValueError("running/completed job requires started timestamp")
        stamps = [
            s
            for s in (self.created_at_utc, self.started_at_utc, self.finished_at_utc)
            if s is not None
        ]
        parsed = [datetime.fromisoformat(s.replace("Z", "+00:00")) for s in stamps]
        if parsed != sorted(parsed):
            raise ValueError("job timestamps out of order")
        if self.status == "completed":
            if self.run_id is None or self.delivery is None or self.error is not None:
                raise ValueError("completed job requires delivery/run and no error")
        elif self.run_id is not None or self.delivery is not None:
            raise ValueError("noncompleted job cannot expose a final run/delivery")
        if self.status == "failed" and (self.error is None or self.error.code == "CANCELLED"):
            raise ValueError("failed job requires noncancel error")
        if self.status == "cancelled" and self.error is not None and self.error.code != "CANCELLED":
            raise ValueError("cancelled job has incompatible error")
        if self.status in {"queued", "running"} and self.error is not None:
            raise ValueError("nonterminal job cannot expose terminal error")
        if self.delivery is not None:
            d = self.delivery
            if (
                d.job_id,
                d.run_id,
                d.scenario_id,
                d.scenario_revision,
                d.scope,
                d.input_fingerprint,
                d.view_slot,
                d.selection_seq,
            ) != (
                self.job_id,
                self.run_id,
                self.scenario_id,
                self.scenario_revision,
                self.scope,
                self.input_fingerprint,
                self.view_slot,
                self.selection_seq,
            ):
                raise ValueError("delivery/requesting job identity mismatch")
        return self


class Metric(ContractModel):
    metric_instance_id: ID
    metric_id: Literal[
        "additional_shade",
        "weighted_shade_utility",
        "winter_sun_loss",
        "direct_incident_energy_change",
    ]
    scenario_ref: ScenarioRef
    value: float
    unit: Unit
    layout_id: ID
    case_id: ID
    target_id: ID | None
    horizon_years: Nonnegative
    weighting: ID
    quantity_kind: QuantityKind
    area_basis: AreaBasis | None = None
    aggregation_basis: ID | None = None

    @model_validator(mode="after")
    def registry_pair(self):
        if self.metric_id in {"additional_shade", "winter_sun_loss"}:
            valid = (
                self.unit == "m2_h"
                and self.quantity_kind in {"geometric", "blocking_equivalent"}
                and self.weighting == "unweighted"
            )
        elif self.metric_id == "weighted_shade_utility":
            valid = (
                self.unit == "weighted_m2_h"
                and self.quantity_kind == "weighted_utility"
                and self.weighting != "unweighted"
            )
        else:
            valid = (
                self.unit in {"kWh", "kWh_per_m2"}
                and self.quantity_kind == "direct_incident_energy"
                and self.area_basis is not None
                and self.aggregation_basis is not None
            )
        if not valid:
            raise ValueError("metric/unit/quantity/weighting/basis mismatch")
        return self


def validate_metric_set(metrics: tuple[Metric, ...]) -> None:
    """Weighted utility always retains a separately labelled physical counterpart."""
    unique([m.metric_instance_id for m in metrics], "metric_instance_id")

    def key(metric):
        return (
            metric.scenario_ref,
            metric.layout_id,
            metric.case_id,
            metric.target_id,
            metric.horizon_years,
        )

    physical = {key(m) for m in metrics if m.metric_id == "additional_shade"}
    if any(key(m) not in physical for m in metrics if m.metric_id == "weighted_shade_utility"):
        raise ValueError("weighted utility requires matching unweighted additional_shade")


class ConstraintRecord(ContractModel):
    scenario_ref: ScenarioRef
    layout_id: ID
    case_id: ID | None
    rule: ID
    limit: float | None
    observed_value: float | None
    unit: Unit | None
    status: Literal["pass", "fail", "unknown"]
    evidence: Array[ID]

    @model_validator(mode="after")
    def unknown_evidence(self):
        if self.status == "pass" and not self.evidence:
            raise ValueError("passed constraint requires evidence")
        return self


class EvaluatedLayout(ContractModel):
    layout: Layout
    scenario_ref: ScenarioRef
    role: Literal["baseline", "reference", "alternative"]
    cost_pence: NonnegativeInt
    tree_count: NonnegativeInt
    feasibility: Literal["feasible", "infeasible", "not_evaluated"]
    reasons: Array[ID]
    selected: bool

    @model_validator(mode="after")
    def selection(self):
        if self.tree_count != len(self.layout.placements):
            raise ValueError("tree_count differs from exact evaluated layout")
        if self.selected and self.feasibility != "feasible":
            raise ValueError("selected layout must be model-feasible")
        if self.feasibility != "feasible" and not self.reasons:
            raise ValueError("non-feasible layout requires reasons")
        return self


class MetricDelta(ContractModel):
    base_metric_instance_id: ID
    alternative_metric_instance_id: ID
    value: float
    unit: Unit
    mode: Literal["fixed_layout", "redesign"]
    changed_inputs: Array[ID]


class ComparisonMetadata(ContractModel):
    mode: Literal["fixed_layout", "redesign"]
    changed_inputs: Array[ID]
    deltas: Array[MetricDelta]


class DeviceDetails(ContractModel):
    name: ID
    backend: ID
    version: ID


class Provenance(ContractModel):
    tool_version: ID
    evaluator_version: ID
    search_version: ID
    solar_version: ID
    schema_version: Literal["0.1.0"]
    seed: int
    created_at_utc: UTC
    compute_started_at_utc: UTC
    compute_finished_at_utc: UTC
    timings_s: Map[ID, Nonnegative]
    physics_device: DeviceDetails | None
    inference_device: DeviceDetails | None
    source_hashes: Map[ID, Hash]
    execution_mode: ExecutionMode

    @model_validator(mode="after")
    def timestamp_order(self):
        from datetime import datetime

        def parse(value):
            return datetime.fromisoformat(value.replace("Z", "+00:00"))

        if (
            not parse(self.compute_started_at_utc)
            <= parse(self.compute_finished_at_utc)
            <= parse(self.created_at_utc)
        ):
            raise ValueError("provenance compute/create timestamps out of order")
        return self


class MissingMetric(ContractModel):
    scenario_ref: ScenarioRef
    layout_id: ID
    case_id: ID
    metric_id: ID
    reason: ID


class FiniteModelProof(ContractModel):
    method: ID
    model_fingerprint: Hash
    evidence_ref: ID


class Result(ContractModel):
    schema_version: Literal["0.1.0"]
    run_id: ID
    source_job_id: ID
    scenario_id: ID
    scenario_revision: Revision
    scope: Scope
    input_fingerprint: Hash
    input_snapshot_ref: ScenarioRef
    operation: AsyncOperation
    arguments: (
        EvaluateLayoutArguments
        | SearchLayoutsArguments
        | CompareLocationsArguments
        | CompareScenariosArguments
    )
    analytical_outcome: Literal[
        "comparison_completed",
        "feasible_candidate",
        "feasible_zero_planting",
        "no_eligible_candidates",
        "search_exhausted_without_target",
        "proven_infeasible_finite_model",
    ]
    layouts: Array[EvaluatedLayout]
    metrics: Array[Metric]
    missing_metrics: Array[MissingMetric]
    comparison: ComparisonMetadata | None
    constraints: Array[ConstraintRecord]
    assumptions: Array[ID]
    limitations: Array[ID]
    source_ids: Array[ID]
    provenance: Provenance
    finite_model_proof: FiniteModelProof | None = None

    @model_validator(mode="after")
    def internal_references(self):
        identity = ScenarioRef(
            scenario_id=self.scenario_id, revision=self.scenario_revision, scope=self.scope
        )
        if self.input_snapshot_ref != identity:
            raise ValueError("result snapshot identity mismatch")
        expected = {
            "evaluate_layout": EvaluateLayoutArguments,
            "search_layouts": SearchLayoutsArguments,
            "compare_locations": CompareLocationsArguments,
            "compare_scenarios": CompareScenariosArguments,
        }
        if type(self.arguments) is not expected[self.operation]:
            raise ValueError("result operation/arguments mismatch")
        validate_metric_set(self.metrics)
        entries = {(e.scenario_ref, e.layout.layout_id): e for e in self.layouts}
        if len(entries) != len(self.layouts):
            raise ValueError("duplicate evaluated layout identity")
        for item in (*self.metrics, *self.missing_metrics, *self.constraints):
            if (item.scenario_ref, item.layout_id) not in entries:
                raise ValueError("result item references unevaluated layout/scenario")
        for e in self.layouts:
            records = [
                c
                for c in self.constraints
                if c.scenario_ref == e.scenario_ref and c.layout_id == e.layout.layout_id
            ]
            if e.feasibility == "feasible" and any(c.status == "fail" for c in records):
                raise ValueError("model-feasible layout contains failed constraint")
        selected = [e for e in self.layouts if e.selected]
        if self.analytical_outcome in {"feasible_candidate", "feasible_zero_planting"}:
            if not selected or any(not self.metrics and not self.missing_metrics for _ in selected):
                raise ValueError("feasible outcome needs selected layout and reported metrics")
            if self.analytical_outcome == "feasible_zero_planting" and any(
                e.tree_count for e in selected
            ):
                raise ValueError("zero-planting outcome must select empty layout")
            if self.analytical_outcome == "feasible_candidate" and any(
                e.tree_count == 0 for e in selected
            ):
                raise ValueError("planting candidate must contain planting")
        elif self.analytical_outcome != "comparison_completed" and selected:
            raise ValueError("unsuccessful search cannot select a recommendation")
        if (
            self.analytical_outcome == "proven_infeasible_finite_model"
            and self.finite_model_proof is None
        ):
            raise ValueError("finite-model infeasibility requires explicit proof")
        metrics = {m.metric_instance_id: m for m in self.metrics}
        if self.comparison is not None:
            for delta in self.comparison.deltas:
                a = metrics.get(delta.base_metric_instance_id)
                b = metrics.get(delta.alternative_metric_instance_id)
                if a is None or b is None or a.unit != b.unit or a.unit != delta.unit:
                    raise ValueError("comparison delta references missing/incompatible metrics")
        return self


def validate_job_transition(previous: Job, next_job: Job) -> None:
    allowed = {
        "queued": {"running", "failed", "cancelled"},
        "running": {"completed", "failed", "cancelled"},
        "completed": set(),
        "failed": set(),
        "cancelled": set(),
    }
    immutable = (
        "job_id",
        "request_id",
        "operation",
        "scenario_id",
        "scenario_revision",
        "scope",
        "input_fingerprint",
        "view_slot",
        "selection_seq",
        "created_at_utc",
    )
    if any(getattr(previous, f) != getattr(next_job, f) for f in immutable):
        raise ValueError("transition changes immutable job identity")
    if next_job.status not in allowed[previous.status]:
        raise ValueError("illegal job transition; retry requires new job/request")


def validate_delivery_currentness(
    job: Job, result: Result, selection: Selection, *, draft: bool = False
) -> None:
    """Raise on stale/unresolved binding; the server must supply latest selection."""
    ref = ScenarioRef(scenario_id=job.scenario_id, revision=job.scenario_revision, scope=job.scope)
    if (
        draft
        or job.status != "completed"
        or job.superseded_by_revision is not None
        or selection.scenario_ref != ref
        or selection.accepted_job_id != job.job_id
        or selection.selection_seq != job.selection_seq
        or selection.view_slot != job.view_slot
    ):
        raise ValueError("delivery is stale or no current completed selection")
    d = job.delivery
    if d is None or (
        result.run_id,
        result.source_job_id,
        result.input_snapshot_ref,
        result.input_fingerprint,
    ) != (d.run_id, d.source_job_id, ref, d.input_fingerprint):
        raise ValueError("result/delivery identity unresolved")
