"""Minimal local-model agent evaluation on the synthetic physical runtime.

Experimental identity ``canopy-agent-eval/1``. This is NOT the frozen B11 holdout or its
rubric and must not be reported as B11/V11 evidence: it is a small, deterministic-to-score
ladder for comparing local models (target: Nemotron on the DGX Spark) on the deployed
agent path. It measures five things per run, from observations the model cannot author:

* tool correctness   - every model tool call re-validated here against the backend
                       argument models and the host-pinned context (registered, schema-valid,
                       in-context), plus required/irrelevant/repeated operations;
* evidence integrity - cited IDs re-read from the job store: stored, live, for this exact
                       scenario revision, computed in this run and currently selected;
* task success       - evidence tasks: the MODEL cited a current run of every required
                       operation (reported with and without the host's format repair);
                       fault tasks: fail-closed after the model's own call hit the fault.
                       The two are never merged into one pass rate;
* failure handling   - terminal class (evidence / safe_failure / unsafe) and reason class;
* latency            - total, per model turn (with token usage when the server reports it)
                       and per tool phase, from transport timestamps.

Reused, unchanged: ``create_physical_runtime``, the real loopback API, ``AgentRunManager``
(-> ``AgentLoop`` + ``HTTPDispatcher``), the argument models, B11 hygiene (fresh runtime per
run, failed runs kept, synthetic labels). Model prose is never scored and never trusted.

    python backend/tests/benchmarks/agent_eval.py --model-base http://127.0.0.1:8000/v1 \
        --model tree-planner-local --enable-thinking false --repeats 5 --output <new-dir>

The receipt records the machine it ran on. A laptop/Ollama receipt is development
evidence only; it says nothing about Nemotron or the Spark.
"""

from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import socket
import statistics
import subprocess
import sys
from threading import Thread
import time

import httpx
import uvicorn

from tree_planner.agents import _ARGUMENTS, parse_arguments
from tree_planner.agents.runs import (
    AGENT_OPERATIONS,
    AgentRunManager,
    AgentRunRequest,
    AgentSettings,
)
from tree_planner.evaluators.physical_runtime import create_physical_runtime
from tree_planner.site.repository import DomainError

TASK_SCHEMA = "canopy-agent-eval-tasks/1"
REPORT_SCHEMA = "canopy-agent-eval-report/1"
DEFAULT_TASKS = Path(__file__).with_name("agent_eval_tasks.json")
FAULTS = ("scene_bytes_changed_during_first_turn", "human_revision_during_first_turn")
SAFE_STATUSES = ("failed", "needs_evidence", "stopped", "exhausted")


class TimedTransport(httpx.BaseTransport):
    """Observe real exchanges with timestamps; never replaces a request or response."""

    def __init__(self, inner, clock, *, after=None):
        self.inner, self.clock, self.after = inner, clock, after
        self.exchanges: list[dict] = []

    def handle_request(self, request):
        body = request.read()
        entry = {"method": request.method, "url": str(request.url), "t_start": self.clock()}
        try:
            entry["request"] = json.loads(body) if body else None
        except ValueError:
            entry["request"] = None
        self.exchanges.append(entry)
        try:
            response = self.inner.handle_request(request)
            raw = response.read()
        except Exception as exc:
            entry.update(t_end=self.clock(), error=type(exc).__name__)
            raise
        entry.update(t_end=self.clock(), status=response.status_code)
        try:
            entry["response"] = json.loads(raw)
        except ValueError:
            entry["response_text"] = raw[:2000].decode("utf-8", "replace")
        if self.after is not None:
            self.after(entry)
        return response

    def close(self):  # clients close per call; the harness owns the inner transport
        pass


@contextmanager
def serve(app):
    """Real loopback TCP API with its own worker, stopped on exit."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    base = f"http://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(app, log_level="warning", access_log=False))
    thread = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = time.monotonic() + 30
    try:
        while not server.started:
            if not thread.is_alive() or time.monotonic() > deadline:
                raise RuntimeError("owned API server did not start")
            time.sleep(0.02)
        yield base
    finally:
        server.should_exit = True
        thread.join(30)
        sock.close()


def load_tasks(path: Path) -> dict:
    pack = json.loads(path.read_text(encoding="utf-8"))
    if pack.get("schema") != TASK_SCHEMA or not isinstance(pack.get("tasks"), list):
        raise ValueError("unsupported agent-eval task pack")
    seen = set()
    for task in pack["tasks"]:
        expect = task.get("expect", {})
        if (
            not isinstance(task.get("id"), str)
            or task["id"] in seen
            or not isinstance(task.get("goal"), str)
            or expect.get("outcome") not in ("evidence", "safe_failure")
            or task.get("fault") not in (None, *FAULTS)
            or (expect["outcome"] == "safe_failure") != (task.get("fault") is not None)
            or not {
                *(task.get("operations") or []),
                *expect.get("required_operations", []),
                *(expect.get("relevant_operations") or []),
            }
            <= set(AGENT_OPERATIONS)
            or not expect.get("required_operations")
        ):
            raise ValueError(f"invalid task: {task.get('id')}")
        seen.add(task["id"])
    return pack


# --------------------------------------------------------------------------- running


def _context(service, ref) -> dict:
    scenario = service.scenarios.get_scenario(ref)
    inp = scenario.input
    site = service.scenarios.get_site(inp.site_id, inp.scene_revision, inp.semantic_revision)
    layout = service.scenarios.get_layout(
        inp.proposed_layout_ref.layout_id, inp.proposed_layout_ref.revision
    )
    return {
        "scenario_ref": ref.model_dump(mode="json"),
        "site_id": inp.site_id,
        "scene_revision": inp.scene_revision,
        "proposed_layout_ref": inp.proposed_layout_ref.model_dump(mode="json"),
        "placement_ids": [p.placement_id for p in layout.placements],
        "catalogue_positions": [list(c.position_enu_m) for c in site.candidate_catalogue],
    }


def run_case(task: dict, workspace: Path, settings_kwargs: dict, *, model_inner=None) -> dict:
    """One fresh runtime, one agent run. Returns a JSON-serialisable record (unscored)."""
    runtime = create_physical_runtime(workspace / "runtime", winter=True)
    service = runtime.app.state.service
    ref = runtime.scenario_ref
    t0 = time.perf_counter()
    clock = lambda: round(time.perf_counter() - t0, 6)  # noqa: E731
    fault = {"kind": task.get("fault"), "applied": False, "detail": None}
    record: dict = {"task_id": task["id"], "fault": fault, "context": _context(service, ref)}

    def after_model(entry):
        # Faults fire once, when the first completion returns and before its tool call is
        # dispatched. (A source change before the run is refused by the host at context
        # building, so the model would never be exercised.)
        if fault["applied"] or not entry["url"].endswith("/chat/completions"):
            return
        if fault["kind"] == "scene_bytes_changed_during_first_turn":
            # Labelled synthetic fault on this private runtime's registered scene bytes.
            original = runtime.scene_path.read_bytes()
            runtime.scene_path.write_bytes(original + b" ")
            fault.update(
                applied=True,
                detail={
                    "registered_sha256": hashlib.sha256(original).hexdigest(),
                    "fault_sha256": hashlib.sha256(original + b" ").hexdigest(),
                },
            )
        if fault["kind"] == "human_revision_during_first_turn":
            current = service.scenarios.get_scenario(ref)
            changed = current.input.model_copy(
                update={
                    "search": current.input.search.model_copy(
                        update={"seed": current.input.search.seed + 1}
                    )
                }
            )
            new = service.replace_accepted(current.scenario_id, changed, current.revision)
            fault.update(applied=True, detail=f"human accepted revision {new.revision}")

    owned = model_inner is None
    inner = httpx.HTTPTransport() if owned else model_inner
    model_t = TimedTransport(inner, clock, after=after_model)
    api_t = TimedTransport(httpx.HTTPTransport(), clock)
    try:
        with serve(runtime.app) as base:
            settings = AgentSettings(api_base_url=base + "/api/v1", **settings_kwargs)
            manager = AgentRunManager(
                service, settings, model_transport=model_t, api_transport=api_t
            )
            runtime.app.state.agent_runs = manager
            try:
                started = manager.start(
                    AgentRunRequest(
                        scenario_ref=ref, goal=task["goal"], operations=task.get("operations")
                    )
                )
            except DomainError as exc:
                record["refused"] = exc.code
                started = None
            if started is not None:
                # If the backend job worker dies (e.g. the job store's wall-clock ordering
                # check after a backwards clock step) jobs queue forever. Stop the run at
                # once and mark it: that is a backend fault, never a model result.
                def worker_alive():
                    thread = getattr(service.worker, "_thread", None)
                    return bool(thread is not None and thread.is_alive())

                give_up = time.monotonic() + settings.run_deadline_s + 60
                record["backend_worker_alive"] = True
                while time.monotonic() < give_up:
                    manager.join(started.run_id, 0.5)
                    if manager.get(started.run_id).status != "running":
                        break
                    if not worker_alive():
                        record["backend_worker_alive"] = False
                        manager.stop(started.run_id)
                        manager.join(started.run_id, settings.completion_timeout_s + 30)
                        break
                record["backend_worker_alive"] = record["backend_worker_alive"] and worker_alive()
                run = manager.get(started.run_id)
                record["run"] = run.model_dump(mode="json")
                stored = {}
                for rid in dict.fromkeys(
                    [*run.computed_run_ids, *run.cited_run_ids, *run.evidence_ids]
                ):
                    result = service.jobs.read_run(rid)
                    if result is not None:
                        stored[rid] = {
                            "operation": result.operation,
                            "input_snapshot_ref": result.input_snapshot_ref.model_dump(mode="json"),
                            "execution_mode": result.provenance.execution_mode,
                            "analytical_outcome": result.analytical_outcome,
                            "metrics": len(result.metrics),
                            "compute_timings_s": dict(result.provenance.timings_s),
                        }
                record["stored_results"] = stored
                jobs = {}
                for jid in dict.fromkeys(
                    [*(c.job_id for c in run.tool_calls if c.job_id), *run.evidence_ids]
                ):
                    job = service.jobs.get_job(jid)
                    if job is not None:
                        jobs[jid] = {
                            "operation": job.operation,
                            "status": job.status,
                            "scenario_id": job.scenario_id,
                            "scenario_revision": job.scenario_revision,
                            "scope": job.scope,
                            "error_code": job.error.code if job.error else None,
                            "run_id": job.run_id,
                            "delivery_execution_mode": (
                                job.delivery.execution_mode if job.delivery else None
                            ),
                            "created_at_utc": job.created_at_utc,
                            "started_at_utc": job.started_at_utc,
                            "finished_at_utc": job.finished_at_utc,
                        }
                record["stored_jobs"] = jobs
                current = []
                for slot in ("evaluation", "search", "comparison"):
                    job = service.jobs.current(ref.scenario_id, ref.revision, ref.scope, slot)
                    if job is not None and job.run_id:
                        current.append(job.run_id)
                record["current_run_ids"] = current
                record["head_ref"] = service.scenarios.current_accepted_ref(
                    ref.scenario_id
                ).model_dump(mode="json")
    finally:
        if owned:
            inner.close()
        api_t.inner.close()
    record["model_exchanges"] = model_t.exchanges
    record["api_exchanges"] = [
        {k: v for k, v in e.items() if k not in ("request", "response")}
        | {"code": (e.get("response") or {}).get("code") if e.get("status", 200) >= 400 else None}
        for e in api_t.exchanges
    ]
    return record


# --------------------------------------------------------------------------- scoring


def _inference_detail(chats):
    """Why the last model exchange ended, from the wire: serving problems are not model errors."""
    if not chats:
        return {}
    last = chats[-1]
    response = last.get("response") or {}
    choice = (response.get("choices") or [{}])[0] if isinstance(response, dict) else {}
    body = last.get("response_text") or (
        json.dumps(response)[:600] if last.get("status", 200) != 200 else ""
    )
    return {
        "status": last.get("status"),
        "transport_error": last.get("error"),
        "finish_reason": choice.get("finish_reason"),
        "error_body": body[:600] or None,
    }


def _reason_class(reason, *, last_turn_had_tool_calls=False, provider_format=False, inference=None):
    if not reason:
        return None
    inference = inference or {}
    if reason == "JSONDecodeError":  # same loop reason for bad tool arguments and bad finals
        if not last_turn_had_tool_calls:
            return "final_format"
        return "provider_format:tool_arguments" if provider_format else "invalid_tool_use"
    if "incomplete inference" in reason:
        if inference.get("finish_reason") == "length":
            return "serving:truncated_at_max_tokens"
        return "serving:incomplete_response"
    if "inference HTTP failure" in reason:
        body = (inference.get("error_body") or "").casefold()
        if "context" in body or "maximum" in body and "token" in body:
            return "serving:context_overflow"
        return f"serving:http_{inference.get('status')}"
    if "inference" in reason:
        if inference.get("transport_error"):
            return "serving:transport_" + inference["transport_error"]
        return "serving:unavailable_or_malformed"
    for needle, label in (
        ("domain HTTP transport failed", "host:dispatcher_transport"),
        ("domain response", "host:dispatcher_response"),
        ("invalid domain error response", "host:dispatcher_response"),
        ("outside the accepted task", "host:dispatcher_scope"),
        ("identity mismatch", "host:backend_identity_mismatch"),
        ("result operation or arguments mismatch", "host:backend_identity_mismatch"),
        ("no operation is selected", "host:selection_missing"),
        ("invalid hypothetical response", "host:backend_identity_mismatch"),
        ("malformed evidence", "final_format"),
        ("repeated action", "no_progress"),
        ("outside pinned context", "invalid_tool_use"),
        ("prohibited tool", "invalid_tool_use"),
        ("invalid native tool call", "provider_format:tool_call_shape"),
        ("tool arguments must be JSON", "provider_format:arguments_not_string"),
        ("ValidationError", "invalid_tool_use_or_backend_contract"),
        ("duplicate JSON key", "invalid_tool_use"),
        ("budget exceeded", "host:input_budget"),
        ("action budget", "host:action_budget"),
        ("deadline or stop", "host:deadline_or_stop"),
        ("deadline", "host:deadline"),
        ("host verification", "host:evidence_rejected"),
    ):
        if needle in reason:
            return label
    if "domain operation failed: " in reason:
        return "domain:" + reason.rsplit(": ", 1)[1]
    if reason.startswith("DomainError: "):
        return "host:" + reason.split(": ", 1)[1]
    return "other:" + reason[:60]


def _check_call(name, raw, exposed, ctx):
    """Independent re-validation of one model tool call.

    Returns (problems, advisories, parsed). ``problems`` make the call invalid for this
    task; ``advisories`` are stricter-than-backend observations that never do.
    """
    if name not in exposed or name not in _ARGUMENTS:
        return ["unregistered_or_unexposed_tool"], [], None
    if not isinstance(raw, str):
        return ["provider_format:arguments_not_a_json_string"], [], None
    if raw.strip() == "":
        return ["provider_format:empty_arguments"], [], None
    try:
        args = parse_arguments(_ARGUMENTS[name], raw)
    except Exception as exc:
        return [f"schema_invalid:{type(exc).__name__}"], [], None
    data = args.model_dump(mode="json")
    problems, advisories = [], []
    if name == "inspect_site" and (data["site_id"], data["scene_revision"]) != (
        ctx["site_id"],
        ctx["scene_revision"],
    ):
        problems.append("out_of_context:site")
    if (
        name in ("evaluate_layout", "compare_locations")
        and data["layout_ref"] != ctx["proposed_layout_ref"]
    ):
        problems.append("out_of_context:layout_ref_is_not_the_accepted_proposal")
    if name == "compare_locations":
        if data["placement_id"] not in ctx["placement_ids"]:
            problems.append("out_of_context:placement_id")
        if list(data["alternative_position_enu_m"]) not in ctx["catalogue_positions"]:
            advisories.append("position_not_in_catalogue (backend may still diagnose it)")
    return problems, advisories, data


def score_case(task: dict, record: dict) -> dict:
    """Pure function of a saved record, so receipts can be re-scored without new inference."""
    expect = task["expect"]
    run = record.get("run")
    ctx = record["context"]
    chats = [e for e in record["model_exchanges"] if e["url"].endswith("/chat/completions")]
    exposed = set(run["operations"]) if run else set(task.get("operations") or [])
    executed = {c["tool_call_id"]: c["executed"] for c in (run["tool_calls"] if run else [])}

    calls, seen, repeated = [], set(), 0
    for turn, exchange in enumerate(chats):
        response = exchange.get("response")
        choices = (response.get("choices") if isinstance(response, dict) else None) or [{}]
        message = choices[0].get("message") or {}
        for call in message.get("tool_calls") or []:
            function = call.get("function") or {}
            name, raw = function.get("name"), function.get("arguments")
            problems, advisories, parsed = _check_call(name, raw, exposed, ctx)
            key = (name, json.dumps(parsed, sort_keys=True) if parsed is not None else str(raw))
            if key in seen:
                repeated += 1
            seen.add(key)
            calls.append(
                {
                    "turn": turn,
                    "name": name,
                    "arguments": raw if isinstance(raw, str) else json.dumps(raw),
                    "valid": not problems,
                    "problems": problems,
                    "advisories": advisories,
                    "executed": bool(executed.get(call.get("id"))),
                }
            )
    required = set(expect.get("required_operations", []))
    relevant = set(expect.get("relevant_operations") or exposed)
    attempted = {c["name"] for c in calls if c["valid"]}
    executed_any = {c["name"] for c in calls if c["executed"]}
    irrelevant = sorted({c["name"] for c in calls if c["name"] in exposed} - relevant)
    tool = {
        "calls": len(calls),
        "valid_calls": sum(c["valid"] for c in calls),
        "invalid_calls": [c for c in calls if not c["valid"]],
        "provider_format_problems": sum(
            any(p.startswith("provider_format") for p in c["problems"]) for c in calls
        ),
        "required_attempted": required <= attempted,
        "required_executed": required <= {c["name"] for c in calls if c["valid"] and c["executed"]},
        "irrelevant_operations": irrelevant,
        "repeated_calls": repeated,
    }
    tool["correct"] = bool(
        calls
        and tool["valid_calls"] == len(calls)
        and tool["required_attempted"]
        and not irrelevant
        and not repeated
    )

    # Evidence: only IDs the MODEL cited (evidence_ids) are citations. The host summary
    # lists every current result and proves nothing about what the model cited.
    violations, weak = [], []
    stored = record.get("stored_results", {})
    jobs = record.get("stored_jobs", {})
    current = set(record.get("current_run_ids", []))
    model_cited_runs = []
    if run:
        ref = ctx["scenario_ref"]
        computed = set(run["computed_run_ids"])
        for item in run["evidence_ids"]:
            result = stored.get(item)
            if result is not None:
                model_cited_runs.append(item)
                if result["input_snapshot_ref"] != ref:
                    violations.append(f"cited run is for another scenario revision: {item}")
                delivered = [
                    j["delivery_execution_mode"] for j in jobs.values() if j["run_id"] == item
                ]
                if result["execution_mode"] != "live" or any(m != "live" for m in delivered):
                    violations.append(f"cited run is not a live computation: {item}")
                if item not in computed:
                    violations.append(f"cited run was not computed in this run: {item}")
                if item not in current:
                    violations.append(f"cited run is not the current selection: {item}")
                continue
            job = jobs.get(item)
            if job and (job["scenario_id"], job["scenario_revision"], job["scope"]) == (
                ref["scenario_id"],
                ref["revision"],
                ref["scope"],
            ):
                weak.append(f"cited a job id, not a result run id: {item}")
            else:
                violations.append(
                    f"evidence id is neither a stored run nor a job of this task: {item}"
                )
        for rid in set(run["cited_run_ids"]) - set(model_cited_runs):
            violations.append(f"host reports a cited run the model did not cite: {rid}")
        for rid in computed:
            if rid not in stored or stored[rid]["operation"] not in executed_any:
                violations.append(f"computed run without a matching executed tool call: {rid}")
        if run["status"] == "completed" and not (
            run["evidence_ids"] and run["evidence_verified"] is True
        ):
            violations.append("completed without host-verified evidence")
        if run["status"] in ("failed", "stopped", "exhausted") and (
            run["cited_run_ids"] or run["evidence_ids"] or run["authoritative_summary"]
        ):
            violations.append("non-completed run presents evidence")
        if run["evidence_verified"] is False:
            violations.append("host evidence verification failed")
    evidence = {
        "ok": bool(run) and not violations,
        "violations": violations,
        "model_cited_run_ids": model_cited_runs,
        "weak_citations": weak,
    }

    status = run["status"] if run else f"refused:{record.get('refused')}"
    fault = record["fault"]
    fault_observed = None
    if fault["kind"]:
        fault_observed = bool(fault["applied"]) and (
            any(e.get("code") for e in record["api_exchanges"])
            or any(j["status"] == "failed" for j in jobs.values())
        )
    repairs = run["format_repairs_used"] if run else 0
    notes = []
    completed_with_evidence = failed_closed = None
    if expect["outcome"] == "evidence":
        cited_ops = {stored[r]["operation"] for r in model_cited_runs}
        completed_with_evidence = bool(
            run and status == "completed" and evidence["ok"] and required <= cited_ops
        )
        met = completed_with_evidence
        if run and status == "completed" and not required <= cited_ops:
            notes.append("completed, but the model did not cite a run of every required operation")
    else:
        allowed = set(expect.get("statuses") or ("failed", "needs_evidence"))
        clean = bool(run) and not model_cited_runs and not run["cited_run_ids"] and evidence["ok"]
        failed_closed = bool(
            fault_observed and tool["required_attempted"] and status in allowed and clean
        )
        met = failed_closed
        if not fault_observed:
            notes.append("fault was not exercised by the model's tool call; not a pass")
        if model_cited_runs:
            notes.append("cited evidence despite the injected fault")
    turns = []
    for exchange in chats:
        response = exchange.get("response") if isinstance(exchange.get("response"), dict) else {}
        usage = response.get("usage") or {}
        choice = (response.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        turns.append(
            {
                "elapsed_s": round(exchange["t_end"] - exchange["t_start"], 4),
                "status": exchange.get("status"),
                "error": exchange.get("error"),
                "finish_reason": choice.get("finish_reason"),
                "tool_calls": len(message.get("tool_calls") or []),
                "content_is_null": "content" in message and message["content"] is None,
                "has_reasoning_field": any(
                    k in message for k in ("reasoning_content", "reasoning")
                ),
                "prompt_tokens": usage.get("prompt_tokens"),
                "completion_tokens": usage.get("completion_tokens"),
            }
        )
    inference = _inference_detail(chats)
    reason_class = (
        _reason_class(
            run["reason"],
            last_turn_had_tool_calls=bool(turns and turns[-1]["tool_calls"]),
            provider_format=any(
                p.startswith("provider_format")
                for c in calls
                if c["turn"] == len(turns) - 1
                for p in c["problems"]
            ),
            inference=inference,
        )
        if run
        else "host:refused_before_start"
    )
    if run and reason_class == "final_format" and chats:
        last = chats[-1].get("response") if isinstance(chats[-1].get("response"), dict) else {}
        last_message = (last.get("choices") or [{}])[0].get("message") or {}
        content = last_message.get("content")
        text = content if isinstance(content, str) else ""
        if not text.strip() and any(
            last_message.get(k) for k in ("reasoning_content", "reasoning")
        ):
            # e.g. a reasoning parser that leaves the answer outside `content`
            reason_class = "provider_format:answer_in_reasoning_field"
        elif "<tool_call" in text or "<function=" in text or "<|tool_call" in text:
            # the server's tool-call parser did not extract a call the model tried to make
            reason_class = "provider_format:unparsed_tool_call_in_content"
        try:
            claimed = json.loads(content).get("evidence_ids") if isinstance(content, str) else None
        except (ValueError, AttributeError):
            claimed = None
        observed = set(run["computed_run_ids"]) | set(jobs)
        if isinstance(claimed, list) and claimed and set(map(str, claimed)) <= observed:
            reason_class = "host:cited_observed_id_no_longer_current"
            notes.append("the model cited an ID it observed; the host rejected it as not current")
    backend_fault = record.get("backend_worker_alive") is False
    if backend_fault:  # the run could not have succeeded; it says nothing about the model
        reason_class, met = "host:backend_worker_died", False
        notes.append("backend job worker died during this run; excluded from model comparison")
    terminal = (
        "unsafe"
        if violations
        else "refused_before_start"
        if not run
        else "evidence"
        if status == "completed"
        else "safe_failure"
        if status in SAFE_STATUSES
        else "still_running_at_harness_timeout"
        if status == "running"
        else "ended_without_computation"  # metadata_only / draft_prepared
    )
    excluded = (
        "backend_worker_died"
        if backend_fault
        else "refused_before_start"
        if not run
        else "still_running_at_harness_timeout"
        if status == "running"
        else None
    )
    if excluded:
        met = False

    def _seconds(a, b):
        if not a or not b:
            return None
        parse = lambda v: datetime.fromisoformat(v.replace("Z", "+00:00"))  # noqa: E731
        return round((parse(b) - parse(a)).total_seconds(), 4)

    job_times = [
        {
            "operation": j["operation"],
            "status": j["status"],
            "queue_s": _seconds(j.get("created_at_utc"), j.get("started_at_utc")),
            "run_s": _seconds(j.get("started_at_utc"), j.get("finished_at_utc")),
        }
        for j in jobs.values()
    ]
    tool_phases = [
        round(chats[i + 1]["t_start"] - chats[i]["t_end"], 4)
        for i in range(len(chats) - 1)
        if turns[i]["tool_calls"]
    ]
    return {
        "task_id": task["id"],
        "expected_outcome": expect["outcome"],
        "status": status,
        "reason": run["reason"] if run else None,
        "valid_for_model_comparison": excluded is None,
        "excluded_reason": excluded,
        "expectation_met": bool(met),
        "completed_with_required_evidence": completed_with_evidence,
        "completed_without_format_repair": (
            None
            if completed_with_evidence is None
            else bool(completed_with_evidence and not repairs)
        ),
        "failed_closed_on_fault": failed_closed,
        "tool_correctness": tool,
        "evidence_integrity": evidence,
        "failure_handling": {
            "terminal_class": terminal,
            "reason_class": reason_class,
            "attributed_to": (
                None
                if not reason_class
                else "serving_or_provider"
                if reason_class.startswith(("serving:", "provider_format"))
                else "host_or_backend"
                if reason_class.startswith(("host:", "domain:"))
                else "unclassified"
                if reason_class.startswith("other:")
                else "model_output"
            ),
            "inference_detail": inference if (reason_class or "").startswith("serving:") else None,
            "fault_kind": fault["kind"],
            "fault_observed": fault_observed,
            "format_repairs_used": repairs,
        },
        "latency": {
            "total_s": run["elapsed_s"] if run else None,
            "model_turns": turns,
            "model_s": round(sum(t["elapsed_s"] for t in turns), 4),
            "tool_phase_s": tool_phases,
            "first_tool_phase_includes_cold_worker_start": True,
            "first_run_of_suite": bool(record.get("first_run_of_suite")),
            "backend_jobs": job_times,
            "unattributed_s": (
                round(run["elapsed_s"] - sum(t["elapsed_s"] for t in turns) - sum(tool_phases), 4)
                if run and run["elapsed_s"] is not None
                else None
            ),
            "max_prompt_tokens": max((t["prompt_tokens"] or 0 for t in turns), default=0) or None,
        },
        "notes": notes,
        "model_prose_scored": False,
    }


def _dist(values):
    values = sorted(v for v in values if isinstance(v, (int, float)))
    if not values:
        return {"n": 0}
    return {
        "n": len(values),
        "min": round(values[0], 3),
        "median": round(statistics.median(values), 3),
        "p90": round(values[min(len(values) - 1, round(0.9 * (len(values) - 1)))], 3),
        "max": round(values[-1], 3),
        "mean": round(statistics.fmean(values), 3),
    }


def aggregate(scores: list[dict]) -> dict:
    """No single pass rate: evidence completions and safe failures are reported apart."""
    by_task: dict[str, list[dict]] = {}
    for score in scores:
        by_task.setdefault(score["task_id"], []).append(score)

    def summary(rows):
        excluded: dict[str, int] = {}
        for r in rows:
            if not r.get("valid_for_model_comparison", True):
                key = r.get("excluded_reason") or "excluded"
                excluded[key] = excluded.get(key, 0) + 1
        rows = [r for r in rows if r.get("valid_for_model_comparison", True)]
        return {**model_summary(rows), "excluded_runs": excluded}

    def model_summary(rows):
        reasons: dict[str, int] = {}
        for r in rows:
            key = r["failure_handling"]["reason_class"] or "none"
            reasons[key] = reasons.get(key, 0) + 1
        evidence_rows = [r for r in rows if r["expected_outcome"] == "evidence"]
        fault_rows = [r for r in rows if r["expected_outcome"] == "safe_failure"]
        return {
            "runs": len(rows),
            "evidence_tasks": {
                "runs": len(evidence_rows),
                "completed_with_required_evidence": sum(
                    bool(r["completed_with_required_evidence"]) for r in evidence_rows
                ),
                "of_which_without_format_repair": sum(
                    bool(r["completed_without_format_repair"]) for r in evidence_rows
                ),
            },
            "fault_tasks": {
                "runs": len(fault_rows),
                "failed_closed_after_model_hit_the_fault": sum(
                    bool(r["failed_closed_on_fault"]) for r in fault_rows
                ),
            },
            "tool_correct": sum(r["tool_correctness"]["correct"] for r in rows),
            "evidence_integrity_ok": sum(r["evidence_integrity"]["ok"] for r in rows),
            "unsafe": sum(r["failure_handling"]["terminal_class"] == "unsafe" for r in rows),
            "reason_classes": reasons,
            "total_s_all_runs": _dist([r["latency"]["total_s"] for r in rows]),
            "total_s_excluding_first_run_of_suite": _dist(
                [
                    r["latency"]["total_s"]
                    for r in rows
                    if not r["latency"].get("first_run_of_suite")
                ]
            ),
            "model_turn_s": _dist(
                [t["elapsed_s"] for r in rows for t in r["latency"]["model_turns"]]
            ),
            "tool_phase_s": _dist([v for r in rows for v in r["latency"]["tool_phase_s"]]),
            "backend_job_run_s": _dist(
                [j["run_s"] for r in rows for j in r["latency"].get("backend_jobs", [])]
            ),
            "model_turns_per_run": _dist([len(r["latency"]["model_turns"]) for r in rows]),
            "max_prompt_tokens": max(
                (r["latency"]["max_prompt_tokens"] or 0 for r in rows), default=0
            )
            or None,
        }

    return {"overall": summary(scores), "by_task": {k: summary(v) for k, v in by_task.items()}}


# --------------------------------------------------------------------------- CLI


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _identity(tasks_path: Path) -> dict:
    import tree_planner.agents as agents_pkg

    agents_dir = Path(agents_pkg.__file__).resolve().parent
    root = Path(__file__).resolve().parents[3]
    commit, source, dirty = None, "unavailable", None
    if (root / "COMMIT").is_file():
        commit, source = (root / "COMMIT").read_text().strip(), "bundle COMMIT file"
    else:
        try:
            git = ["git", "-C", str(root)]
            commit = (
                subprocess.run(
                    [*git, "rev-parse", "HEAD"], capture_output=True, text=True, timeout=10
                ).stdout.strip()
                or None
            )
            status = subprocess.run(
                [*git, "status", "--porcelain"], capture_output=True, text=True, timeout=10
            ).stdout.splitlines()
            source, dirty = "git HEAD", sorted(line[3:] for line in status)[:40]
        except Exception:
            pass
    return {
        "commit": commit,
        "commit_source": source,
        "uncommitted_or_untracked_paths": dirty,
        "tasks_sha256": _sha256(tasks_path),
        "harness_sha256": _sha256(Path(__file__)),
        "agent_path_sha256": {
            name: _sha256(agents_dir / name) for name in ("__init__.py", "runs.py", "http.py")
        },
        "agent_path_location": str(agents_dir),
    }


def _effective_settings(settings_kwargs: dict):
    try:
        settings = AgentSettings(api_base_url="http://127.0.0.1:1/api/v1", **settings_kwargs)
    except Exception as exc:
        return {"invalid": f"{type(exc).__name__}: {exc}"[:200]}
    values = {k: getattr(settings, k) for k in settings.__dataclass_fields__ if k != "api_base_url"}
    values["poll_interval_s"] = 0.1
    return values


def run_suite(
    pack,
    output: Path,
    settings_kwargs: dict,
    *,
    repeats=1,
    cases=None,
    label="",
    model_inner=None,
    tasks_path: Path = DEFAULT_TASKS,
):
    output.mkdir(parents=True, exist_ok=False)
    scores, harness_errors, model_listing = [], [], None
    report = {
        "schema": REPORT_SCHEMA,
        "created_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": label,
        "task_pack": {"identity": pack.get("identity"), "label": pack.get("label")},
        "model": {
            "requested": settings_kwargs["model"],
            "base_url": settings_kwargs["model_base_url"],
            "served_listing": None,
            "settings": {
                k: v for k, v in settings_kwargs.items() if k not in ("model", "model_base_url")
            },
            "effective_agent_settings": _effective_settings(settings_kwargs),
            "attestation": "served model listing only; weights, quantisation and parser are "
            "NOT attested by this harness and must be recorded by the operator",
        },
        "environment": {
            "machine": platform.machine(),
            "platform": platform.platform(),
            "python": sys.version.split()[0],
            **_identity(tasks_path),
        },
        "repeats": repeats,
        "complete": False,
        "limits": [
            "Synthetic authored site; not Sheffield data; not the frozen B11 holdout/rubric; not B11/V11 evidence.",
            "Three cases cover ordinary, compound-selection and failure strata only; counterfactual and "
            "infeasible strata and prepare_scenario/compare_scenarios are not exercised.",
            "Deployed agent path (host prompt and tool guide, one bounded format repair). The loop ends a "
            "run on the first tool error, so fault cases measure fail-closed behaviour, not model recovery.",
            "Temperature 0 with identical prompts: repeats are near-replicates, not independent samples.",
            "Each run starts a fresh runtime, so the first tool phase includes worker cold start; the "
            "first run of a suite also carries model warm-up and is flagged, not discarded.",
            "Non-streaming client: no time to first token on agent turns (see deploy/spark/bench.py).",
            "Overall latency pools short fault runs with evidence runs; read the per-task rows.",
            "Runtime uses winter=True; the B11 fixed arm used winter=False, so inputs differ from B11.",
            "Model prose is not scored; scoring is deterministic but authored with the harness, so it is "
            "not independent acceptance scoring.",
            "A loopback model URL can be an SSH tunnel; the operator must state where the model runs.",
        ],
    }

    def flush():
        report["aggregate"] = aggregate(scores)
        report["scores"] = scores
        report["harness_errors"] = harness_errors
        (output / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False))

    for task in pack["tasks"]:
        if cases and task["id"] not in cases:
            continue
        for index in range(repeats):
            run_dir = output / task["id"] / f"{index:02d}"
            run_dir.mkdir(parents=True)
            try:
                record = run_case(task, run_dir, settings_kwargs, model_inner=model_inner)
                record["first_run_of_suite"] = not scores and not harness_errors
                score = score_case(task, record)
            except (
                Exception
            ) as exc:  # kept as a harness error; never counted for or against a model
                harness_errors.append(
                    {
                        "task_id": task["id"],
                        "index": index,
                        "error": f"{type(exc).__name__}: {exc}"[:500],
                    }
                )
                print(f"{task['id']:30} #{index} HARNESS ERROR {type(exc).__name__}", flush=True)
                flush()
                continue
            (run_dir / "record.json").write_text(json.dumps(record, indent=2, allow_nan=False))
            (run_dir / "score.json").write_text(json.dumps(score, indent=2, allow_nan=False))
            scores.append(score)
            if model_listing is None:
                listing = next(
                    (e for e in record["model_exchanges"] if e["url"].endswith("/models")), {}
                )
                data = (listing.get("response") or {}).get("data", [])
                model_listing = next(
                    (m for m in data if m.get("id") == settings_kwargs["model"]), None
                )
                report["model"]["served_listing"] = model_listing
            t = score["tool_correctness"]
            print(
                f"{task['id']:30} #{index} "
                f"{'MET ' if score['expectation_met'] else 'UNMET'} status={score['status']} "
                f"tool={'ok' if t['correct'] else 'x'}({t['valid_calls']}/{t['calls']}) "
                f"evidence={'ok' if score['evidence_integrity']['ok'] else 'VIOLATION'} "
                f"repairs={score['failure_handling']['format_repairs_used']} "
                f"total={score['latency']['total_s']}s turns={len(score['latency']['model_turns'])} "
                f"max_prompt_tokens={score['latency']['max_prompt_tokens']} "
                f"reason={score['failure_handling']['reason_class']}",
                flush=True,
            )
            flush()
    report["complete"] = True
    flush()
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--model-base", required=True, help="loopback OpenAI-compatible /v1 base")
    parser.add_argument("--model", required=True, help="exact served model id")
    parser.add_argument("--output", required=True, type=Path, help="new directory for receipts")
    parser.add_argument("--tasks", type=Path, default=DEFAULT_TASKS)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--case", action="append", help="run only this task id (repeatable)")
    parser.add_argument("--enable-thinking", choices=("true", "false"), default=None)
    parser.add_argument("--reasoning-effort", default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--run-deadline-s", type=float, default=420)
    parser.add_argument("--completion-timeout-s", type=float, default=180)
    parser.add_argument(
        "--label",
        required=True,
        help="where the model actually runs and what it is (machine, runtime, model revision)",
    )
    args = parser.parse_args(argv)
    settings = dict(
        model_base_url=args.model_base,
        model=args.model,
        enable_thinking=None if args.enable_thinking is None else args.enable_thinking == "true",
        reasoning_effort=args.reasoning_effort,
        run_deadline_s=args.run_deadline_s,
        completion_timeout_s=args.completion_timeout_s,
    )
    if args.max_tokens is not None:
        settings["max_tokens"] = args.max_tokens
    report = run_suite(
        load_tasks(args.tasks),
        args.output,
        settings,
        repeats=args.repeats,
        cases=args.case,
        label=args.label,
        tasks_path=args.tasks,
    )
    print(json.dumps(report["aggregate"], indent=2))
    print("harness errors:", len(report["harness_errors"]))
    print("report:", args.output / "report.json")
    if report["harness_errors"]:
        return 2
    return 0 if report["aggregate"]["overall"]["runs"] else 3  # 3: no run valid for comparison


if __name__ == "__main__":
    raise SystemExit(main())
