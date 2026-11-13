"""The formatter consumes actual Metric fields, not invented composite keys."""

import os
from pathlib import Path
from threading import Event
from time import monotonic

import pytest

from tree_planner.agents import AgentLoop
from tree_planner.evaluators.runtime import create_reference_runtime


def test_summary_preserves_actual_numerics_and_unknown_physical_scope(tmp_path):
    source = os.environ.get("CANOPY_NUMERICS_SOURCE")
    if not source:
        pytest.skip("pinned real numerical source not configured")
    runtime = create_reference_runtime(
        tmp_path / "runtime", numerical_source=Path(source), start_worker=False
    )
    job = runtime.app.state.service.submit(runtime.request("summary-regression"))
    completed = runtime.app.state.service.run_one()
    assert completed.job_id == job.job_id and completed.status == "completed"
    result = runtime.app.state.service.jobs.read_run(completed.run_id)
    loop = object.__new__(AgentLoop)
    loop.jobs = [completed]
    interpretation = "Untrusted model interpretation, not the authoritative metric."
    outcome = loop._conclusion(
        {"narrative": interpretation, "evidence_ids": [result.run_id]}, (result,)
    )
    metric = result.metrics[0]
    assert outcome.status == "completed"
    assert f"{metric.case_id}/{metric.target_id}/{metric.layout_id}" in outcome.narrative
    assert f"{metric.value:g} {metric.unit}" in outcome.narrative
    assert "not_evaluated" in outcome.narrative
    assert all(limit in outcome.narrative for limit in result.limitations)
    assert outcome.untrusted_model_narrative == interpretation
    assert outcome.narrative != interpretation


def test_final_evidence_recheck_uses_canonical_selection_and_cached_origin(tmp_path):
    from tree_planner.api.service import AgentDispatcher

    source = os.environ.get("CANOPY_NUMERICS_SOURCE")
    if not source:
        pytest.skip("pinned real numerical source not configured")
    runtime = create_reference_runtime(
        tmp_path / "runtime", numerical_source=Path(source), start_worker=False
    )
    service = runtime.app.state.service
    first = service.submit(runtime.request("first-current"))
    completed = service.run_one()
    result = service.jobs.read_run(completed.run_id)
    accepted = service.scenarios.get_scenario(runtime.scenario_ref)
    loop = AgentLoop(
        object(),
        AgentDispatcher(service, accepted_ref=runtime.scenario_ref),
        accepted,
        {"evaluate_layout"},
        deadline=monotonic() + 20,
        stop=Event(),
        poll_interval_s=0.05,
    )
    loop.jobs = [completed]
    loop.results = [result]
    assert loop._current_results() == (result,)
    second = service.submit(runtime.request("second-current"))
    assert second.status == "queued"
    assert loop._current_results() == ()
    # Cache choice is an explicit trusted controller action, not auto-selection.
    assert service.jobs.deliver_cached(second.job_id, result.run_id)
    delivered = service.jobs.get_job(second.job_id)
    assert delivered.status == "completed" and delivered.run_id == result.run_id
    assert delivered.job_id != first.job_id and delivered.delivery.source_job_id == first.job_id
    assert delivered.delivery.execution_mode == "cached"
    loop.jobs = [delivered]
    assert loop._current_results() == (result,)
