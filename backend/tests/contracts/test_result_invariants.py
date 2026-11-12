"""Schema-only metric/provenance inputs, explicitly not computed result fixtures."""

import pytest
from pydantic import ValidationError

from tree_planner.contracts import Metric, Provenance, validate_metric_set
from test_jobs_metrics import metric_data


def test_weighted_utility_requires_matching_unweighted_metric():
    weighted = Metric.model_validate(
        {
            **metric_data(),
            "metric_instance_id": "weighted-unit",
            "metric_id": "weighted_shade_utility",
            "unit": "weighted_m2_h",
            "quantity_kind": "weighted_utility",
            "weighting": "synthetic explicit target weights",
        }
    )
    with pytest.raises(ValueError):
        validate_metric_set((weighted,))
    physical = Metric.model_validate(metric_data())
    validate_metric_set((physical, weighted))
    wrong_case = Metric.model_validate({**metric_data(), "case_id": "other"})
    with pytest.raises(ValueError):
        validate_metric_set((wrong_case, weighted))


def test_provenance_time_order_is_not_invented_or_repaired():
    data = dict(
        tool_version="synthetic-unit",
        evaluator_version="synthetic-unit",
        search_version="synthetic-unit",
        solar_version="synthetic-unit",
        schema_version="0.1.0",
        seed=0,
        created_at_utc="2026-11-12T12:00:03Z",
        compute_started_at_utc="2026-11-12T12:00:01Z",
        compute_finished_at_utc="2026-11-12T12:00:00Z",
        timings_s={},
        physics_device=None,
        inference_device=None,
        source_hashes={},
        execution_mode="fixture",
    )
    with pytest.raises(ValidationError):
        Provenance.model_validate(data)
