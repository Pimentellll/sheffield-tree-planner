from backend.tests.benchmarks.runner import score_run


def test_score_requires_current_observed_result_and_counts_actions():
    task = {
        "id": "routine",
        "required_operations": ["evaluate_layout"],
        "required_outcome": "current validated evaluation result or explicit failure",
    }
    observation = {
        "status": "completed",
        "final_response": "Current backend result run-1: evaluate_layout.",
        "response_evidence_ids": ["run-1"],
        "operation_events": [
            {
                "operation": "evaluate_layout",
                "status": "completed",
                "run_id": "run-1",
                "current": True,
            }
        ],
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
    assert scored["constraint_accuracy"] == {
        "passed": 1,
        "checked": 2,
        "all_passed": False,
        "counts_by_status": {"pass": 1, "fail": 0, "unknown": 1},
    }
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
        "operation_events": [
            {
                "operation": "evaluate_layout",
                "status": "completed",
                "run_id": "invented",
                "current": True,
            }
        ],
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


def test_compound_completion_requires_every_required_operation_current():
    task = {
        "id": "compound",
        "required_operations": ["evaluate_layout", "search_layouts"],
        "required_outcome": "current validated evidence or explicit failure",
    }
    observation = {
        "status": "partial",
        "operation_events": [
            {
                "operation": "evaluate_layout",
                "status": "completed",
                "run_id": "r1",
                "current": True,
            },
            {"operation": "search_layouts", "status": "error", "job_id": "j2"},
        ],
        "constraint_checks": [],
        "numeric_claim_audits": [],
        "user_actions": [],
        "useful_analysis_run_ids": [],
        "tool_errors": ["search unavailable"],
        "elapsed_ms": 1,
    }
    scored = score_run(task, observation, actual_job_ids={"j2"}, actual_run_ids={"r1"})
    assert scored["completion"] is False


def test_single_operation_observed_failure_can_complete_safe_failure_task():
    task = {
        "id": "failure",
        "required_operations": ["evaluate_layout"],
        "required_outcome": "observed current result or preserved explicit tool/job failure",
    }
    observation = {
        "operation_events": [{"operation": "evaluate_layout", "status": "error"}],
        "constraint_checks": [],
        "numeric_claim_audits": [],
        "user_actions": [],
        "useful_analysis_run_ids": [],
        "tool_errors": ["unavailable"],
        "elapsed_ms": 1,
        "final_response": "No validated result for evaluate_layout; observed TimeoutError.",
    }
    observation["operation_events"][0]["error_type"] = "TimeoutError"
    assert (
        score_run(task, observation, actual_job_ids=set(), actual_run_ids=set())["completion"]
        is True
    )


def test_nan_latency_is_invalid():
    task = {"id": "routine", "required_operations": ["evaluate_layout"]}
    observation = {
        "operation_events": [],
        "constraint_checks": [],
        "numeric_claim_audits": [],
        "user_actions": [],
        "useful_analysis_run_ids": [],
        "tool_errors": [],
        "elapsed_ms": float("nan"),
    }
    scored = score_run(task, observation, actual_job_ids=set(), actual_run_ids=set())
    assert scored["latency_ms"] is None
    assert "invalid elapsed_ms" in scored["integrity_errors"]


def test_unrelated_current_result_does_not_complete_required_operation():
    task = {"id": "counterfactual", "required_operations": ["compare_locations"]}
    observation = {
        "operation_events": [
            {"operation": "evaluate_layout", "status": "completed", "run_id": "r1", "current": True}
        ],
        "constraint_checks": [],
        "numeric_claim_audits": [],
        "user_actions": [],
        "useful_analysis_run_ids": [],
        "tool_errors": [],
        "elapsed_ms": 1,
        "final_response": "Current backend result r1: evaluate_layout.",
        "response_evidence_ids": ["r1"],
    }
    assert not score_run(task, observation, actual_job_ids=set(), actual_run_ids={"r1"})[
        "completion"
    ]


def test_counterfactual_requires_comparison_outcome_not_any_current_result():
    task = {
        "id": "counterfactual",
        "stratum": "counterfactual",
        "required_operations": ["compare_locations"],
    }
    observation = {
        "operation_events": [
            {
                "operation": "compare_locations",
                "status": "completed",
                "run_id": "r1",
                "current": True,
            }
        ],
        "constraint_checks": [{"status": "unknown"}],
        "numeric_claim_audits": [],
        "user_actions": [],
        "useful_analysis_run_ids": [],
        "tool_errors": [],
        "elapsed_ms": 2,
        "final_response": "Comparison result r1 is current.",
        "response_evidence_ids": ["r1"],
        "backend_outcomes": {"r1": "feasible_candidate"},
    }
    scored = score_run(task, observation, actual_job_ids=set(), actual_run_ids={"r1"})
    assert scored["completion"] is False
    observation["backend_outcomes"]["r1"] = "comparison_completed"
    assert (
        score_run(task, observation, actual_job_ids=set(), actual_run_ids={"r1"})["completion"]
        is True
    )
