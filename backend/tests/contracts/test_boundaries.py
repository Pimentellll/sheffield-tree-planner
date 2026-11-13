"""Controlled unit identities and invalid inputs; no evaluator response fixture."""

from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from tree_planner.contracts import (
    Delivery,
    Job,
    OperationEnvelope,
    ReferenceValidationError,
    Result,
    ScenarioRef,
    Selection,
    validate_delivery_currentness,
    validate_operation_supported,
)
from test_jobs_metrics import job_data


def test_result_preserves_documented_operation_and_arguments():
    assert "operation" in Result.model_fields
    assert "arguments" in Result.model_fields


def test_unsupported_operation_is_not_enabled_by_serializable_schema():
    request = OperationEnvelope.model_validate(
        dict(
            request_id="unit",
            operation="search_layouts",
            scenario_ref=dict(scenario_id="unit", revision=1, scope="accepted"),
            arguments={},
        )
    )
    with pytest.raises(ReferenceValidationError) as error:
        validate_operation_supported(
            request, supported_operations=frozenset({"inspect_site", "evaluate_layout"})
        )
    assert error.value.code == "UNSUPPORTED_OPERATION"


def test_live_and_cached_delivery_identity_and_staleness():
    data = job_data()
    # Controlled unit job/delivery metadata only, no numerical response is constructed.
    delivery = dict(
        job_id=data["job_id"],
        run_id="unit-run",
        source_job_id="original-unit-job",
        scenario_id=data["scenario_id"],
        scenario_revision=1,
        scope="accepted",
        input_fingerprint=data["input_fingerprint"],
        view_slot="evaluation",
        selection_seq=1,
        execution_mode="cached",
        delivered_at_utc="2026-11-12T12:00:03Z",
    )
    job = Job.model_validate(
        {
            **data,
            "status": "completed",
            "run_id": "unit-run",
            "delivery": delivery,
            "started_at_utc": "2026-11-12T12:00:01Z",
            "finished_at_utc": "2026-11-12T12:00:02Z",
        }
    )
    ref = ScenarioRef(scenario_id=data["scenario_id"], revision=1, scope="accepted")
    selection = Selection(
        scenario_ref=ref, view_slot="evaluation", selection_seq=1, accepted_job_id=job.job_id
    )
    metadata = SimpleNamespace(
        run_id="unit-run",
        source_job_id="original-unit-job",
        input_snapshot_ref=ref,
        input_fingerprint=data["input_fingerprint"],
    )
    validate_delivery_currentness(job, metadata, selection)
    with pytest.raises(ValueError):
        validate_delivery_currentness(job, metadata, selection, draft=True)
    for change in (
        {"selection_seq": 2},
        {"accepted_job_id": "newer"},
        {"view_slot": "search"},
        {"scenario_ref": dict(scenario_id=data["scenario_id"], revision=1, scope="hypothetical")},
    ):
        newer = Selection.model_validate({**selection.model_dump(mode="json"), **change})
        with pytest.raises(ValueError):
            validate_delivery_currentness(job, metadata, newer)
    metadata.input_fingerprint = "b" * 64
    with pytest.raises(ValueError):
        validate_delivery_currentness(job, metadata, selection)
    with pytest.raises(ValidationError):
        Delivery.model_validate({**delivery, "execution_mode": "live"})


def test_all_result_nested_objects_forbid_unknown_fields():
    schema = Result.model_json_schema()
    for name, model in schema["$defs"].items():
        if model.get("type") == "object" and "properties" in model:
            assert model.get("additionalProperties") is False, name
