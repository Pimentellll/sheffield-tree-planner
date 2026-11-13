"""Agent-run service over the real physical runtime and real loopback TCP API.

The *model* side here is a labelled SYNTHETIC OpenAI-protocol fixture (scripted
replies), exactly like test_protocol.py. It exercises host safety/lifecycle rules;
it is never model evidence. Every job, Result and metric comes from the actual
CPU runtime. Genuine local-model runs live in the opt-in live tests.
"""

from __future__ import annotations

import json
import socket
from threading import Event, Thread
from time import monotonic, sleep

import httpx
import pytest
import uvicorn

from tree_planner.agents.runs import (
    AgentRunManager,
    AgentSettings,
    _awaiting_final,
    install,
)
from tree_planner.evaluators.physical_runtime import create_physical_runtime

MODEL_BASE = "http://127.0.0.1:9/v1"  # never contacted: the fixture transport answers


class ScriptedModel:
    """SYNTHETIC protocol fixture. ``script`` maps the request (decoded) to a reply."""

    def __init__(self, script, *, models=("fixture-model",), gate: Event | None = None):
        self.script, self.models, self.gate = script, models, gate
        self.requests: list[dict] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/models"):
            return httpx.Response(200, json={"data": [{"id": m} for m in self.models]})
        body = json.loads(request.read())
        self.requests.append(body)
        if self.gate is not None:
            self.gate.wait(10)
        message, finish = self.script(body, len(self.requests))
        return httpx.Response(
            200,
            json={"choices": [{"index": 0, "finish_reason": finish, "message": message}]},
        )


def call(name, arguments, ident="call-1"):
    return (
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": ident,
                    "type": "function",
                    "function": {"name": name, "arguments": arguments},
                }
            ],
        },
        "tool_calls",
    )


def final(content):
    return {"role": "assistant", "content": content}, "stop"


def observed_run_id(body):
    for message in reversed(body["messages"]):
        if message["role"] == "tool":
            return json.loads(message["content"])["result"]["run_id"]
    raise AssertionError("no observation")


@pytest.fixture
def served(tmp_path):
    runtime = create_physical_runtime(tmp_path / "runtime", winter=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    base = f"http://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(uvicorn.Config(runtime.app, log_level="warning"))
    thread = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=True)
    thread.start()
    deadline = monotonic() + 20
    while not server.started:
        assert thread.is_alive() and monotonic() < deadline
        sleep(0.02)
    client = httpx.Client(base_url=base + "/api/v1", headers={"Origin": base}, trust_env=False)
    try:
        yield runtime, base + "/api/v1", client
    finally:
        client.close()
        server.should_exit = True
        thread.join(20)
        sock.close()
        assert not thread.is_alive()


def configure(runtime, api, model, **overrides):
    settings = AgentSettings(
        model_base_url=MODEL_BASE, model="fixture-model", api_base_url=api, **overrides
    )
    manager = AgentRunManager(
        runtime.app.state.service, settings, model_transport=httpx.MockTransport(model)
    )
    runtime.app.state.agent_runs = manager
    return manager


def ref_json(runtime):
    return runtime.scenario_ref.model_dump(mode="json")


def start(client, runtime, goal="Evaluate the proposed layout.", **extra):
    return client.post(
        "/agent/runs", json={"scenario_ref": ref_json(runtime), "goal": goal, **extra}
    )


def wait(client, run_id, timeout=60):
    end = monotonic() + timeout
    while monotonic() < end:
        run = client.get(f"/agent/runs/{run_id}").json()
        if run["status"] != "running":
            return run
        sleep(0.05)
    raise AssertionError("agent run did not finish")


def evaluate_args(runtime):
    service = runtime.app.state.service
    layout = service.scenarios.get_scenario(runtime.scenario_ref).input.proposed_layout_ref
    return json.dumps({"layout_ref": layout.model_dump(mode="json")})


def test_unconfigured_agent_fails_closed_and_manual_workflow_still_runs(served):
    runtime, _, client = served
    status = client.get("/agent/status").json()
    assert status["configured"] is False and status["model"] is None
    assert "evaluate_layout" in status["allowed_operations"]
    response = start(client, runtime)
    assert response.status_code == 503 and response.json()["code"] == "TOOL_UNAVAILABLE"
    # Deterministic manual evaluation is independent of any model.
    layout = json.loads(evaluate_args(runtime))
    job = client.post(
        "/operations",
        json={
            "request_id": "manual-1",
            "operation": "evaluate_layout",
            "arguments": layout,
            "scenario_ref": ref_json(runtime),
        },
    )
    assert job.status_code == 202, job.text


def test_unreachable_model_reports_unavailable_without_starting(served):
    runtime, api, client = served

    def down(request):
        raise httpx.ConnectError("refused", request=request)

    runtime.app.state.agent_runs = AgentRunManager(
        runtime.app.state.service,
        AgentSettings(model_base_url=MODEL_BASE, model="fixture-model", api_base_url=api),
        model_transport=httpx.MockTransport(down),
    )
    status = client.get("/agent/status").json()
    assert status["configured"] is True and status["reachable"] is False
    response = start(client, runtime)
    assert response.status_code == 503 and response.json()["code"] == "TOOL_UNAVAILABLE"
    assert runtime.app.state.agent_runs._active_id() is None


def test_unlisted_model_alias_is_not_started(served):
    runtime, api, client = served
    configure(runtime, api, ScriptedModel(lambda b, n: final("{}"), models=("other",)))
    status = client.get("/agent/status").json()
    assert status["reachable"] is True and status["model_listed"] is False
    assert start(client, runtime).status_code == 503


def test_tool_call_real_result_then_one_format_repair_with_verified_evidence(served):
    runtime, api, client = served

    def script(body, n):
        if n == 1:
            return call("evaluate_layout", evaluate_args(runtime))
        if n == 2:
            return final("Here is a **Markdown** summary, not JSON.")
        assert body["messages"][-1]["role"] == "user"  # the host repair turn
        return final(
            json.dumps({"narrative": "UNTRUSTED prose", "evidence_ids": [observed_run_id(body)]})
        )

    model = ScriptedModel(script)
    configure(runtime, api, model)
    accepted = client.post("/agent/runs", json={"scenario_ref": ref_json(runtime), "goal": "x"})
    assert accepted.status_code == 202, accepted.text
    run = wait(client, accepted.json()["run_id"])
    assert run["status"] == "completed", run
    assert run["format_repairs_used"] == 1 and run["model_completions"] == 3
    assert run["evidence_verified"] is True and run["rejected_model_reply"] is None
    assert run["evidence_ids"] == run["cited_run_ids"] == run["computed_run_ids"]
    assert len(run["cited_run_ids"]) == 1
    stored = client.get(f"/results/{run['cited_run_ids'][0]}").json()
    assert stored["input_snapshot_ref"] == ref_json(runtime)
    assert stored["operation"] == "evaluate_layout"
    # Authoritative prose is backend-generated from the stored Result, not model text.
    shade = next(m for m in stored["metrics"] if m["metric_id"] == "additional_shade")
    assert f"{shade['value']:g} {shade['unit']}" in run["authoritative_summary"]
    assert "UNTRUSTED" not in run["authoritative_summary"]
    assert run["untrusted_model_narrative"] == "UNTRUSTED prose"
    assert run["tool_calls"][0]["executed"] and run["tool_calls"][0]["job_status"] == "completed"
    assert run["tool_calls"][0]["run_id"] == stored["run_id"]
    # The model saw schemas only for host-exposed operations.
    names = {t["function"]["name"] for t in model.requests[0]["tools"]}
    assert names == set(run["operations"]) and "prepare_scenario" not in names


def test_repair_exhausted_with_invented_evidence_fails_without_citations(served):
    runtime, api, client = served

    def script(body, n):
        if n == 1:
            return call("evaluate_layout", evaluate_args(runtime))
        return final(json.dumps({"narrative": "x", "evidence_ids": ["invented-run"]}))

    configure(runtime, api, ScriptedModel(script))
    run = wait(client, start(client, runtime).json()["run_id"])
    assert run["status"] == "failed" and run["format_repairs_used"] == 1
    assert run["evidence_ids"] == [] and run["authoritative_summary"] is None
    assert "malformed evidence" in run["reason"]
    # Regression: a computed result is not a citation when the final answer is rejected.
    assert run["cited_run_ids"] == [] and run["evidence_verified"] is None
    assert len(run["computed_run_ids"]) == 1
    assert run["tool_calls"][0]["run_id"] == run["computed_run_ids"][0]
    assert "invented-run" in run["rejected_model_reply"]
    assert run["untrusted_model_narrative"] is None


def test_malformed_tool_arguments_are_not_repaired(served):
    runtime, api, client = served
    configure(runtime, api, ScriptedModel(lambda b, n: call("evaluate_layout", "{bad json")))
    run = wait(client, start(client, runtime).json()["run_id"])
    assert run["status"] == "failed" and run["format_repairs_used"] == 0
    assert run["tool_calls"][0]["executed"] is False


def test_prohibited_tool_cannot_accept_or_change_the_task(served):
    runtime, api, client = served
    before = client.get(f"/scenarios/{runtime.scenario_ref.scenario_id}?revision=1").json()
    configure(runtime, api, ScriptedModel(lambda b, n: call("accept_scenario", "{}")))
    run = wait(client, start(client, runtime).json()["run_id"])
    assert run["status"] == "failed" and "prohibited" in run["reason"]
    service = runtime.app.state.service
    assert service.scenarios.current_accepted_ref(before["scenario_id"]) == runtime.scenario_ref


def test_human_revision_during_run_rejects_the_stale_tool_call(served):
    runtime, api, client = served
    service = runtime.app.state.service
    args = evaluate_args(runtime)

    def script(body, n):
        if n == 1:  # a human accepts a new revision while the model is thinking
            current = service.scenarios.get_scenario(runtime.scenario_ref)
            changed = current.input.model_copy(
                update={"search": current.input.search.model_copy(update={"seed": 99})}
            )
            service.replace_accepted(current.scenario_id, changed, current.revision)
            return call("evaluate_layout", args)
        return final(json.dumps({"narrative": "x", "evidence_ids": []}))

    configure(runtime, api, ScriptedModel(script))
    run = wait(client, start(client, runtime).json()["run_id"])
    assert run["status"] == "failed" and "REVISION_CONFLICT" in run["reason"]
    assert run["evidence_ids"] == [] and run["cited_run_ids"] == []
    # And a new run against the superseded revision is refused up front.
    again = start(client, runtime)
    assert again.status_code == 409 and again.json()["code"] == "REVISION_CONFLICT"


def test_single_active_run_and_cooperative_stop(served):
    runtime, api, client = served
    gate = Event()
    configure(runtime, api, ScriptedModel(lambda b, n: final("{}"), gate=gate))
    first = start(client, runtime)
    assert first.status_code == 202
    run_id = first.json()["run_id"]
    assert client.get("/agent/status").json()["active_run_id"] == run_id
    second = start(client, runtime)
    assert second.status_code == 409
    stopped = client.post(f"/agent/runs/{run_id}/stop").json()
    assert stopped["stop_requested"] is True and stopped["status"] == "running"
    gate.set()  # the in-flight completion returns; the loop then observes stop
    run = wait(client, run_id)
    assert run["status"] == "stopped" and run["evidence_ids"] == []
    assert client.get("/agent/status").json()["active_run_id"] is None


def test_request_validation_and_operation_allowlist(served):
    runtime, api, client = served
    configure(runtime, api, ScriptedModel(lambda b, n: final("{}")))
    assert start(client, runtime, goal="   ").status_code == 422
    assert start(client, runtime, goal="x" * 601).status_code == 422
    bad = start(client, runtime, operations=["prepare_scenario"])
    assert bad.status_code == 422 and bad.json()["code"] == "UNSUPPORTED_OPERATION"
    hypothetical = client.post(
        "/agent/runs",
        json={"scenario_ref": {**ref_json(runtime), "scope": "hypothetical"}, "goal": "x"},
    )
    assert hypothetical.status_code == 409
    assert client.get("/agent/runs/unknown").status_code == 404
    no_origin = httpx.post(
        api + "/agent/runs", json={"scenario_ref": ref_json(runtime), "goal": "x"}
    )
    assert no_origin.status_code == 403


def test_settings_require_loopback_and_env_keys(tmp_path):
    with pytest.raises(ValueError):
        AgentSettings(model_base_url="http://10.0.0.5:8000/v1", model="m", api_base_url="x")
    with pytest.raises(ValueError):
        AgentSettings.from_env(
            "a", {"LLM_BASE_URL": MODEL_BASE, "LLM_MODEL": "m", "LLM_ENABLE_THINKING": "maybe"}
        )
    assert AgentSettings.from_env("a", {}) is None
    settings = AgentSettings.from_env(
        "a", {"LLM_BASE_URL": MODEL_BASE, "LLM_MODEL": "m", "LLM_ENABLE_THINKING": "false"}
    )
    assert settings.client_config().chat_template_kwargs == {"enable_thinking": False}
    runtime = create_physical_runtime(tmp_path / "rt", start_worker=False)
    before = runtime.app.state.agent_runs
    assert install(runtime.app, "http://127.0.0.1:1/api/v1", env={}) is None
    assert runtime.app.state.agent_runs is before


def test_every_exposable_operation_has_host_guidance():
    from tree_planner.agents.runs import AGENT_OPERATIONS, TOOL_GUIDE

    assert set(TOOL_GUIDE) == set(AGENT_OPERATIONS)


def test_awaiting_final_only_when_every_tool_call_answered():
    asked = {"role": "assistant", "tool_calls": [{"id": "a"}, {"id": "b"}]}
    assert not _awaiting_final([asked, {"role": "tool", "tool_call_id": "a"}])
    assert _awaiting_final(
        [asked, {"role": "tool", "tool_call_id": "a"}, {"role": "tool", "tool_call_id": "b"}]
    )
