"""Unit lifecycle/schema tests. No hand-authored successful evaluator Result."""

import json

import pytest
from pydantic import ValidationError

from tree_planner.contracts import (
    ContractError,
    Job,
    Metric,
    OperationEnvelope,
    validate_job_transition,
)

REF = dict(scenario_id="synthetic", revision=1, scope="accepted")


def job_data():
    return dict(
        schema_version="0.1.0",
        job_id="unit-job",
        request_id="unit-request",
        operation="evaluate_layout",
        scenario_id="synthetic",
        scenario_revision=1,
        scope="accepted",
        input_fingerprint="a" * 64,
        view_slot="evaluation",
        selection_seq=1,
        status="queued",
        run_id=None,
        delivery=None,
        progress=None,
        created_at_utc="2026-11-12T12:00:00Z",
        started_at_utc=None,
        finished_at_utc=None,
        error=None,
        cancel_requested=False,
        superseded_by_revision=None,
    )


def metric_data():
    return dict(
        metric_instance_id="unit-metric",
        metric_id="additional_shade",
        scenario_ref=REF,
        value=0,
        unit="m2_h",
        layout_id="unit-layout",
        case_id="unit-case",
        target_id=None,
        horizon_years=20,
        weighting="unweighted",
        quantity_kind="geometric",
    )


def test_metric_zero_is_schema_value_not_physical_execution():
    assert Metric.model_validate_json(json.dumps(metric_data())).value == 0


@pytest.mark.parametrize(
    "change",
    [
        {"unit": "weighted_m2_h"},
        {"quantity_kind": "weighted_utility"},
        {"metric_id": "weighted_shade_utility"},
        {"value": float("nan")},
        {"value": True},
        {"metric_id": "temperature"},
        {"extra": 1},
    ],
)
def test_wrong_metric_units_quantities_and_types(change):
    with pytest.raises(ValidationError):
        Metric.model_validate({**metric_data(), **change})


def test_job_error_terminal_and_no_restart():
    queued = Job.model_validate(job_data())
    running = Job.model_validate(
        {**job_data(), "status": "running", "started_at_utc": "2026-11-12T12:00:01Z"}
    )
    validate_job_transition(queued, running)
    for code in ("WORKER_INTERRUPTED", "DEADLINE_EXCEEDED"):
        failed = Job.model_validate(
            {
                **running.model_dump(mode="json"),
                "status": "failed",
                "finished_at_utc": "2026-11-12T12:00:02Z",
                "error": dict(
                    code=code,
                    message="controlled unit failure",
                    retryable=False,
                    field_errors=[],
                    details={},
                ),
            }
        )
        validate_job_transition(running, failed)
        with pytest.raises(ValueError):
            validate_job_transition(failed, running)


@pytest.mark.parametrize(
    "change",
    [
        {"status": "completed"},
        {"status": "paused"},
        {"view_slot": "search"},
        {"selection_seq": True},
        {"progress": {"completed": 2, "total": 1, "phase": "unit", "unit": "items"}},
    ],
)
def test_invalid_job(change):
    with pytest.raises(ValidationError):
        Job.model_validate({**job_data(), **change})


def test_operation_dispatch_shape_and_boolean():
    request = dict(
        request_id="unit-request",
        scenario_ref=REF,
        operation="evaluate_layout",
        arguments={"layout_ref": {"layout_id": "unit-layout", "revision": 1}},
    )
    assert (
        OperationEnvelope.model_validate_json(json.dumps(request)).root.operation
        == "evaluate_layout"
    )
    request["arguments"]["approval"] = True
    with pytest.raises(ValidationError):
        OperationEnvelope.model_validate(request)


def test_error_details_only_safe_structured_strings():
    with pytest.raises(ValidationError):
        ContractError(
            code="INVALID_INPUT", message="unit", retryable=1, field_errors=[], details={}
        )
