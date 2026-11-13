"""Validate the agent-eval harness itself with a labelled SYNTHETIC protocol fixture.

Scripted replies stand in for the model so every scoring branch is deterministic. Jobs,
Results and failures come from the real physical runtime over real loopback HTTP. Nothing
here is model evidence; genuine runs use the CLI against a real local model.
"""

from __future__ import annotations

import copy
import json

import httpx
import pytest

from backend.tests.agents.test_runs import ScriptedModel, call, final, observed_run_id
from backend.tests.benchmarks.agent_eval import (
    DEFAULT_TASKS,
    _reason_class,
    aggregate,
    load_tasks,
    run_case,
    run_suite,
    score_case,
)

SETTINGS = dict(model_base_url="http://127.0.0.1:9/v1", model="fixture-model")
PACK = load_tasks(DEFAULT_TASKS)
TASKS = {t["id"]: t for t in PACK["tasks"]}
LAYOUT = json.dumps({"layout_ref": {"layout_id": "one-tree", "revision": 1}})
EVALUATE = "protocol-evaluate-proposal"
SEARCH = "selection-search-options"
FAULT = "failure-changed-source"


def cite(body):
    return final(json.dumps({"narrative": "UNTRUSTED", "evidence_ids": [observed_run_id(body)]}))


def run(task_id, script, tmp_path, transport=None):
    task = TASKS[task_id]
    inner = transport or httpx.MockTransport(ScriptedModel(script))
    record = run_case(task, tmp_path, SETTINGS, model_inner=inner)
    return task, record, score_case(task, record)


def good_evaluate(body, n):
    return call("evaluate_layout", LAYOUT) if n == 1 else cite(body)


def test_pack_is_a_labelled_three_case_ladder_and_not_the_b11_holdout():
    assert [t["id"] for t in PACK["tasks"]] == [EVALUATE, SEARCH, FAULT]
    assert "SYNTHETIC" in PACK["label"] and "Not the frozen B11 holdout" in PACK["label"]
    assert PACK["schema"] != "canopy-b11-heldout-v1"


def test_ordinary_case_is_met_only_by_a_valid_call_and_a_model_cited_current_run(tmp_path):
    task, record, score = run(EVALUATE, good_evaluate, tmp_path)
    assert score["expectation_met"] and score["status"] == "completed"
    assert score["completed_with_required_evidence"] and score["completed_without_format_repair"]
    assert score["failed_closed_on_fault"] is None
    assert score["tool_correctness"]["correct"] and score["tool_correctness"]["calls"] == 1
    evidence = score["evidence_integrity"]
    assert evidence["ok"] and not evidence["violations"] and not evidence["weak_citations"]
    assert evidence["model_cited_run_ids"] == record["run"]["evidence_ids"]
    assert score["failure_handling"]["terminal_class"] == "evidence"
    lat = score["latency"]
    assert len(lat["model_turns"]) == 2 and len(lat["tool_phase_s"]) == 1
    assert lat["total_s"] >= lat["tool_phase_s"][0] > 0
    # The scorer is a pure function of the saved record (JSON round trip gives the same score).
    assert score_case(task, json.loads(json.dumps(record))) == score


def test_format_repair_is_reported_separately_from_first_pass_success(tmp_path):
    def script(body, n):
        if n == 1:
            return call("evaluate_layout", LAYOUT)
        return final("Markdown prose, not JSON") if n == 2 else cite(body)

    _, _, score = run(EVALUATE, script, tmp_path)
    assert score["completed_with_required_evidence"] is True
    assert score["completed_without_format_repair"] is False
    assert score["failure_handling"]["format_repairs_used"] == 1


def test_job_id_only_citation_is_weak_and_does_not_complete_the_task(tmp_path):
    def script(body, n):
        if n == 1:
            return call("evaluate_layout", LAYOUT)
        job_id = json.loads(body["messages"][-1]["content"])["job"]["job_id"]
        return final(json.dumps({"narrative": "x", "evidence_ids": [job_id]}))

    _, record, score = run(EVALUATE, script, tmp_path)
    assert record["run"]["status"] == "completed" and record["run"]["cited_run_ids"] == []
    assert not score["expectation_met"] and not score["completed_with_required_evidence"]
    evidence = score["evidence_integrity"]
    assert evidence["ok"] and evidence["model_cited_run_ids"] == []
    assert "cited a job id" in evidence["weak_citations"][0]
    assert "did not cite a run of every required operation" in score["notes"][0]


def test_scorer_detects_tampered_evidence_independently_of_the_host(tmp_path):
    task, record, _ = run(EVALUATE, good_evaluate, tmp_path)
    rid = record["run"]["evidence_ids"][0]
    for mutate, needle in (
        (lambda r: r["stored_results"].pop(rid), "neither a stored run nor a job"),
        (lambda r: r["stored_results"][rid].update(execution_mode="cached"), "not a live"),
        (
            lambda r: r["stored_results"][rid]["input_snapshot_ref"].update(revision=9),
            "another scenario",
        ),
        (lambda r: r.update(current_run_ids=[]), "not the current selection"),
        (lambda r: r["run"].update(computed_run_ids=[]), "not computed in this run"),
        (lambda r: r["run"].update(evidence_verified=False), "host evidence verification"),
        (lambda r: r["run"].update(evidence_ids=[]), "host reports a cited run the model did not"),
    ):
        tampered = copy.deepcopy(record)
        mutate(tampered)
        rescored = score_case(task, tampered)
        assert not rescored["evidence_integrity"]["ok"] and not rescored["expectation_met"]
        assert any(needle in v for v in rescored["evidence_integrity"]["violations"]), needle
        assert rescored["failure_handling"]["terminal_class"] == "unsafe"


@pytest.mark.parametrize(
    "arguments,problem,reason,blame",
    [
        ("{bad json", "schema_invalid", "invalid_tool_use", "model_output"),
        (
            json.dumps({"layout_ref": {"layout_id": "one-tree"}}),
            "schema_invalid",
            "invalid_tool_use_or_backend_contract",
            "model_output",
        ),
        (
            json.dumps({"layout_ref": {"layout_id": "other-layout", "revision": 1}}),
            "out_of_context:layout_ref",
            "domain:UNKNOWN_REVISION",
            "host_or_backend",
        ),
        (
            "",
            "provider_format:empty_arguments",
            "provider_format:tool_arguments",
            "serving_or_provider",
        ),
    ],
)
def test_invalid_arguments_fail_tool_correctness_safely_with_attribution(
    tmp_path, arguments, problem, reason, blame
):
    _, _, score = run(EVALUATE, lambda body, n: call("evaluate_layout", arguments), tmp_path)
    tool = score["tool_correctness"]
    assert not score["expectation_met"] and not tool["correct"] and tool["valid_calls"] == 0
    assert any(problem in p for c in tool["invalid_calls"] for p in c["problems"])
    assert score["evidence_integrity"]["ok"]  # nothing cited, nothing fabricated
    assert score["failure_handling"]["terminal_class"] == "safe_failure"
    assert score["failure_handling"]["reason_class"] == reason
    assert score["failure_handling"]["attributed_to"] == blame


def test_invented_citation_is_a_safe_failure_and_computed_run_is_not_evidence(tmp_path):
    _, record, score = run(
        EVALUATE,
        lambda body, n: (
            call("evaluate_layout", LAYOUT)
            if n == 1
            else final(json.dumps({"narrative": "x", "evidence_ids": ["invented"]}))
        ),
        tmp_path,
    )
    assert not score["expectation_met"] and score["tool_correctness"]["correct"]
    assert score["evidence_integrity"]["ok"] and record["run"]["computed_run_ids"]
    assert score["evidence_integrity"]["model_cited_run_ids"] == []
    assert score["failure_handling"]["reason_class"] == "final_format"
    assert score["failure_handling"]["format_repairs_used"] == 1


def test_serving_failures_are_not_attributed_to_the_model(tmp_path):
    def truncated(body, n):  # e.g. reasoning consumed max_tokens
        return {"role": "assistant", "content": "partial"}, "length"

    _, _, score = run(EVALUATE, truncated, tmp_path / "length")
    handling = score["failure_handling"]
    assert handling["reason_class"] == "serving:truncated_at_max_tokens"
    assert handling["attributed_to"] == "serving_or_provider"
    assert handling["inference_detail"]["finish_reason"] == "length"

    def overflow(request):  # shape of an OpenAI-compatible context-length rejection
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": "fixture-model"}]})
        return httpx.Response(
            400,
            json={"error": {"message": "maximum context length is 8192 tokens", "code": 400}},
        )

    _, _, score = run(
        EVALUATE, None, tmp_path / "overflow", transport=httpx.MockTransport(overflow)
    )
    handling = score["failure_handling"]
    assert handling["reason_class"] == "serving:context_overflow"
    assert handling["attributed_to"] == "serving_or_provider"
    assert score["status"] == "failed" and score["evidence_integrity"]["ok"]


def test_serving_stack_final_answer_shapes_are_not_model_format_errors(tmp_path):
    def reasoning_only(body, n):  # answer left in a reasoning field, content null
        if n == 1:
            return call("evaluate_layout", LAYOUT)
        return {"role": "assistant", "content": None, "reasoning_content": "the answer"}, "stop"

    _, _, score = run(EVALUATE, reasoning_only, tmp_path / "reasoning")
    handling = score["failure_handling"]
    assert handling["reason_class"] == "provider_format:answer_in_reasoning_field"
    assert handling["attributed_to"] == "serving_or_provider"

    def unparsed(body, n):  # the server's parser left a tool call as plain text
        return final('<tool_call>{"name": "evaluate_layout", "arguments": {}}</tool_call>')

    _, _, score = run(EVALUATE, unparsed, tmp_path / "unparsed")
    handling = score["failure_handling"]
    assert handling["reason_class"] == "provider_format:unparsed_tool_call_in_content"
    assert handling["attributed_to"] == "serving_or_provider"
    assert not score["expectation_met"] and score["evidence_integrity"]["ok"]


def test_selection_case_requires_the_search_run_to_be_cited_by_the_model(tmp_path):
    def good(body, n):
        return call("search_layouts", "{}") if n == 1 else cite(body)

    _, _, score = run(SEARCH, good, tmp_path / "good")
    assert score["expectation_met"] and score["tool_correctness"]["correct"]

    # A valid, executed, cited evaluation is still not the task.
    _, _, score = run(SEARCH, good_evaluate, tmp_path / "wrong")
    assert score["status"] == "completed" and score["evidence_integrity"]["ok"]
    assert not score["expectation_met"] and not score["tool_correctness"]["correct"]
    assert not score["tool_correctness"]["required_attempted"]

    def cites_other_run(body, n):  # ran the search but cited only the evaluation
        if n == 1:
            return call("evaluate_layout", LAYOUT)
        if n == 2:
            return call("search_layouts", "{}", "call-2")
        first = json.loads(next(m for m in body["messages"] if m["role"] == "tool")["content"])
        return final(json.dumps({"narrative": "x", "evidence_ids": [first["result"]["run_id"]]}))

    _, record, score = run(SEARCH, cites_other_run, tmp_path / "uncited")
    assert record["run"]["status"] == "completed" and len(record["run"]["computed_run_ids"]) == 2
    assert score["tool_correctness"]["correct"] and not score["expectation_met"]
    assert "did not cite a run of every required operation" in score["notes"][0]

    def irrelevant(body, n):
        if n == 1:
            return call(
                "compare_locations",
                json.dumps(
                    {
                        "layout_ref": {"layout_id": "one-tree", "revision": 1},
                        "placement_id": "tree-1",
                        "alternative_position_enu_m": [2.0, 0.0, 0.0],
                    }
                ),
            )
        return call("search_layouts", "{}", "call-2") if n == 2 else cite(body)

    _, _, score = run(SEARCH, irrelevant, tmp_path / "irrelevant")
    assert score["tool_correctness"]["irrelevant_operations"] == ["compare_locations"]
    assert not score["tool_correctness"]["correct"]
    assert score["evidence_integrity"]["ok"]  # backend-accepted calls are never "unsafe"


def test_fault_case_is_met_only_when_the_fault_is_hit_and_nothing_is_cited(tmp_path):
    def attempts(body, n):
        if n == 1:
            return call("evaluate_layout", LAYOUT)
        return final('{"narrative":"x","evidence_ids":[]}')

    _, record, score = run(FAULT, attempts, tmp_path / "hit")
    assert record["fault"]["applied"] and score["failure_handling"]["fault_observed"] is True
    assert score["expectation_met"] and score["failed_closed_on_fault"] is True
    assert score["completed_with_required_evidence"] is None  # never counted as a completion
    assert score["status"] in ("failed", "needs_evidence")
    assert not record["run"]["cited_run_ids"] and not record["run"]["authoritative_summary"]
    assert not record["stored_results"]
    assert score["failure_handling"]["terminal_class"] == "safe_failure"
    assert score["failure_handling"]["reason_class"] == "domain:REVISION_CONFLICT"

    # A model that never calls the tool has not handled the failure; that is not a pass.
    _, _, score = run(
        FAULT,
        lambda body, n: final('{"narrative":"all fine","evidence_ids":[]}'),
        tmp_path / "skip",
    )
    assert not score["expectation_met"] and score["failure_handling"]["fault_observed"] is False
    assert "fault was not exercised" in score["notes"][0]


def test_mid_run_human_revision_fault_rejects_the_stale_call(tmp_path):
    task = {
        "id": "stale",
        "goal": "Evaluate the current proposal.",
        "operations": ["evaluate_layout"],
        "fault": "human_revision_during_first_turn",
        "expect": {"outcome": "safe_failure", "required_operations": ["evaluate_layout"]},
    }
    script = ScriptedModel(lambda body, n: call("evaluate_layout", LAYOUT))
    record = run_case(task, tmp_path, SETTINGS, model_inner=httpx.MockTransport(script))
    score = score_case(task, record)
    assert record["fault"]["applied"] and record["head_ref"]["revision"] == 2
    assert score["expectation_met"]
    assert score["failure_handling"]["reason_class"] == "domain:REVISION_CONFLICT"


def test_suite_reports_evidence_and_fault_outcomes_apart_and_keeps_failures(tmp_path):
    def script(body, n):
        if not any(m["role"] == "tool" for m in body["messages"]):
            return call("evaluate_layout", LAYOUT)
        return cite(body)

    report = run_suite(
        PACK,
        tmp_path / "out",
        SETTINGS,
        repeats=1,
        label="pytest synthetic fixture; not model evidence",
        model_inner=httpx.MockTransport(ScriptedModel(script)),
    )
    overall = report["aggregate"]["overall"]
    # evaluate completes; the search task does not (wrong tool); the fault task fails closed.
    assert overall["runs"] == 3 and overall["unsafe"] == 0
    assert overall["evidence_tasks"] == {
        "runs": 2,
        "completed_with_required_evidence": 1,
        "of_which_without_format_repair": 1,
    }
    assert overall["fault_tasks"] == {"runs": 1, "failed_closed_after_model_hit_the_fault": 1}
    assert "success" not in overall  # no merged pass rate
    by_task = report["aggregate"]["by_task"]
    assert by_task[SEARCH]["evidence_tasks"]["completed_with_required_evidence"] == 0
    assert report["complete"] is True and report["harness_errors"] == []
    assert report["model"]["served_listing"] == {"id": "fixture-model"}
    env = report["environment"]
    assert len(env["tasks_sha256"]) == 64 and len(env["harness_sha256"]) == 64
    assert set(env["agent_path_sha256"]) == {"__init__.py", "runs.py", "http.py"}
    assert report["scores"][0]["model_prose_scored"] is False
    assert [x["latency"]["first_run_of_suite"] for x in report["scores"]] == [True, False, False]
    assert overall["total_s_excluding_first_run_of_suite"]["n"] == 2
    for task in PACK["tasks"]:
        assert (tmp_path / "out" / task["id"] / "00" / "record.json").is_file()
    assert aggregate(report["scores"]) == report["aggregate"]
    assert json.loads((tmp_path / "out" / "report.json").read_text())["complete"] is True
    with pytest.raises(FileExistsError):
        run_suite(PACK, tmp_path / "out", SETTINGS)


def test_backend_worker_death_is_excluded_from_model_comparison(tmp_path):
    task, record, score = run(EVALUATE, good_evaluate, tmp_path)
    assert record["backend_worker_alive"] is True and score["valid_for_model_comparison"]
    died = copy.deepcopy(record)
    died["backend_worker_alive"] = False
    rescored = score_case(task, died)
    assert not rescored["valid_for_model_comparison"] and not rescored["expectation_met"]
    assert rescored["failure_handling"]["reason_class"] == "host:backend_worker_died"
    assert rescored["failure_handling"]["attributed_to"] == "host_or_backend"
    summary = aggregate([score, rescored])["overall"]
    assert summary["runs"] == 1 and summary["excluded_runs"] == {"backend_worker_died": 1}
    assert summary["evidence_tasks"]["completed_with_required_evidence"] == 1


def test_unavailable_model_is_a_blocked_run_not_a_model_failure(tmp_path):
    def down(request):
        raise httpx.ConnectError("refused", request=request)

    task, record, score = run(EVALUATE, None, tmp_path, transport=httpx.MockTransport(down))
    assert record["refused"] == "TOOL_UNAVAILABLE" and "run" not in record
    assert score["status"] == "refused:TOOL_UNAVAILABLE"
    assert not score["valid_for_model_comparison"]
    assert score["excluded_reason"] == "refused_before_start"
    assert score["failure_handling"]["terminal_class"] == "refused_before_start"
    summary = aggregate([score])["overall"]
    assert summary["runs"] == 0 and summary["excluded_runs"] == {"refused_before_start": 1}
    assert summary["evidence_tasks"]["runs"] == 0


def test_correct_citation_rejected_as_not_current_is_not_charged_to_the_model(tmp_path):
    def script(body, n):
        if n == 1:
            return call("evaluate_layout", LAYOUT)
        return final(json.dumps({"narrative": "x", "evidence_ids": ["invented"]}))

    task, record, score = run(EVALUATE, script, tmp_path)
    assert score["failure_handling"]["reason_class"] == "final_format"
    assert score["failure_handling"]["attributed_to"] == "model_output"
    observed = copy.deepcopy(record)
    rid = observed["run"]["computed_run_ids"][0]
    chats = [e for e in observed["model_exchanges"] if e["url"].endswith("/chat/completions")]
    chats[-1]["response"]["choices"][0]["message"]["content"] = json.dumps(
        {"narrative": "x", "evidence_ids": [rid]}
    )
    rescored = score_case(task, observed)
    assert (
        rescored["failure_handling"]["reason_class"] == "host:cited_observed_id_no_longer_current"
    )
    assert rescored["failure_handling"]["attributed_to"] == "host_or_backend"


def test_dispatcher_and_unknown_failures_are_never_attributed_to_the_model():
    assert _reason_class("ProtocolError: domain HTTP transport failed").startswith("host:")
    assert _reason_class("ProtocolError: domain response byte limit").startswith("host:")
    assert _reason_class("ProtocolError: polled job identity mismatch").startswith("host:")
    assert _reason_class("ProtocolError: deadline or stop") == "host:deadline_or_stop"
    assert _reason_class("SomethingNew").startswith("other:")
    assert _reason_class("ProtocolError: repeated action made no progress") == "no_progress"


def test_task_pack_validation_rejects_unknown_operations(tmp_path):
    pack = json.loads(DEFAULT_TASKS.read_text())
    pack["tasks"][0]["expect"]["required_operations"] = ["evaluate_layouts"]  # misspelled
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps(pack))
    with pytest.raises(ValueError):
        load_tasks(bad)


def test_latency_separates_backend_job_time_and_reports_the_residual(tmp_path):
    _, record, score = run(EVALUATE, good_evaluate, tmp_path)
    lat = score["latency"]
    assert [j["operation"] for j in lat["backend_jobs"]] == ["evaluate_layout"]
    assert (
        lat["backend_jobs"][0]["run_s"] is not None
        and lat["backend_jobs"][0]["queue_s"] is not None
    )
    assert lat["unattributed_s"] is not None
    job = next(iter(record["stored_jobs"].values()))
    assert job["delivery_execution_mode"] == "live"
    cached = copy.deepcopy(record)
    next(iter(cached["stored_jobs"].values()))["delivery_execution_mode"] = "cached"
    assert any(
        "not a live" in v
        for v in score_case(TASKS[EVALUATE], cached)["evidence_integrity"]["violations"]
    )


def test_harness_errors_are_kept_and_never_scored_as_model_results(tmp_path):
    bad = dict(model_base_url="http://10.0.0.5:8000/v1", model="fixture-model")  # not loopback
    report = run_suite(PACK, tmp_path / "out", bad, repeats=1, label="pytest")
    assert report["scores"] == [] and len(report["harness_errors"]) == 3
    assert report["complete"] is True and report["aggregate"]["overall"]["runs"] == 0
    assert (tmp_path / "out" / "report.json").is_file()
