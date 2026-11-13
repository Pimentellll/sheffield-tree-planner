from backend.tests.benchmarks.runner import score_run


def test_score_requires_current_observed_result_and_counts_actions():
    task = {
        "id": "routine",
        "required_operations": ["evaluate_layout"],
        "required_outcome": "current validated evaluation result or explicit failure",
    }
    observation = {
        "status": "completed",
        "operation_events": [{"operation": "evaluate_layout", "status": "completed", "run_id": "run-1", "current": True}],
        "constraint_checks": [{"status": "pass"}, {"status": "unknown"}],
        "numeric_claim_audits": [{"supported": True}, {"supported": False}],
        "claim_audit_complete": True,
        "user_actions": [{"kind": "edit"}, {"kind": "correction"}],
        "useful_analysis_run_ids": ["run-1"],
        "tool_errors": [],
        "elapsed_ms": 20,
    }
    scored = score_run(task, observation, actual_job_ids={"job-1"}, actual_run_ids={"run-1"})
    assert scored["completion"] is True
    assert scored["constraint_accuracy"] == {"passed": 1, "checked": 2, "all_passed": False}
    assert scored["unsupported_claims"] == 1
    assert scored["claim_audit_complete"] is True
    assert scored["human_actions"] == 2
    assert scored["human_corrections"] == 1
    assert scored["useful_analyses"] == 1
    assert scored["latency_ms"] == 20


def test_score_rejects_adapter_claimed_result_not_seen_by_backend():
    task = {"id": "routine", "required_operations": ["evaluate_layout"]}
    observation = {
        "status": "completed",
        "operation_events": [{"operation": "evaluate_layout", "status": "completed", "run_id": "invented", "current": True}],
        "constraint_checks": [],
        "numeric_claim_audits": [],
        "user_actions": [],
        "useful_analysis_run_ids": [],
        "tool_errors": [],
        "elapsed_ms": 1,
    }
    scored = score_run(task, observation, actual_job_ids=set(), actual_run_ids=set())
    assert scored["completion"] is False
    assert scored["integrity_errors"] == ["unobserved run id: invented"]
