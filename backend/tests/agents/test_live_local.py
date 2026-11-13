"""Opt-in real local model -> TCP domain API proofs; never mocked model output.

Set CANOPY_LOCAL_MODEL_BASE, CANOPY_LOCAL_MODEL and CANOPY_NUMERICS_SOURCE.
Raw synthetic-only receipts are saved only with explicit CANOPY_LIVE_PROOF_DIR.
"""

from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict
import os
import logging
from pathlib import Path
import socket
from threading import Event, Thread
from time import monotonic, sleep

import pytest
import httpx
import uvicorn

from tree_planner.agents import AgentLoop, ClientConfig, LocalClient
from tree_planner.agents.http import HTTPDispatcher
from tree_planner.evaluators.runtime import create_reference_runtime


class RecordingTransport(httpx.BaseTransport):
    """Observe actual local HTTP bytes without replacing requests or responses."""

    def __init__(self):
        self.inner = httpx.HTTPTransport()
        self.exchanges = []

    def handle_request(self, request):
        exchange = {"url": str(request.url), "request": json.loads(request.read())}
        self.exchanges.append(exchange)
        response = self.inner.handle_request(request)
        exchange["status"] = response.status_code
        exchange["response_text"] = response.read().decode("utf-8")
        return response

    def close(self):
        self.inner.close()


class RecordingClient(LocalClient):
    """Keep complete responses, including finals omitted from loop.messages."""

    def __init__(self, config):
        self.recording = RecordingTransport()
        super().__init__(config, transport=self.recording)
        self.completions = []

    def complete(self, messages, tools, *, timeout_s=None):
        record = {"messages": deepcopy(messages), "tools": deepcopy(tools)}
        self.completions.append(record)
        try:
            message = super().complete(messages, tools, timeout_s=timeout_s)
        except Exception as exc:
            record["error"] = f"{type(exc).__name__}: {exc}"
            raise
        record["message"] = deepcopy(message)
        try:
            with httpx.Client(trust_env=False, timeout=5) as observer:
                record["runtime_ps"] = observer.get(
                    self.config.base_url.removesuffix("/v1") + "/api/ps"
                ).json()
        except httpx.HTTPError as exc:
            record["runtime_observation_error"] = type(exc).__name__
        return message


@pytest.fixture
def live_runtime(tmp_path, request, caplog):
    model_base = os.environ.get("CANOPY_LOCAL_MODEL_BASE")
    model = os.environ.get("CANOPY_LOCAL_MODEL")
    numerical = os.environ.get("CANOPY_NUMERICS_SOURCE")
    if not (model_base and model and numerical):
        pytest.skip("explicit real local model and numerical source not configured")
    caplog.set_level(logging.INFO, logger="uvicorn")
    caplog.set_level(logging.INFO, logger="uvicorn.access")
    runtime = create_reference_runtime(tmp_path / "runtime", numerical_source=Path(numerical))
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    base = f"http://127.0.0.1:{sock.getsockname()[1]}"
    server = uvicorn.Server(
        uvicorn.Config(runtime.app, log_config=None, log_level="info", access_log=True)
    )
    thread = Thread(target=server.run, kwargs={"sockets": [sock]}, daemon=False)
    thread.start()
    try:
        deadline = monotonic() + 20
        while not server.started:
            assert thread.is_alive() and monotonic() < deadline, "real domain server startup failed"
            sleep(0.02)
        yield runtime, base + "/api/v1", model_base, model
    finally:
        server.should_exit = True
        thread.join(20)
        sock.close()
        assert not thread.is_alive(), "owned HTTP server did not stop"
        assert runtime.app.state.service.worker is None, "owned worker did not stop"
        output = os.environ.get("CANOPY_LIVE_PROOF_DIR")
        if output:
            dest = Path(output)
            dest.mkdir(parents=True, exist_ok=True)
            (dest / (request.node.name + ".cleanup.json")).write_text(
                json.dumps(
                    {
                        "server_thread_alive": thread.is_alive(),
                        "worker_is_none": runtime.app.state.service.worker is None,
                        "socket_closed": sock.fileno() == -1,
                        "logs": caplog.text,
                        "phase_logs": {
                            phase: [record.getMessage() for record in caplog.get_records(phase)]
                            for phase in ("setup", "call", "teardown")
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )


def run_actual_model(live_runtime, operation: str):
    runtime, api, model_base, model = live_runtime
    accepted = runtime.app.state.service.scenarios.get_scenario(runtime.scenario_ref)
    config = ClientConfig(
        model_base,
        model,
        timeout_s=90,
        max_input_bytes=65536,
        max_response_bytes=1048576,
        max_tokens=1024,
        reasoning_effort="none",
        temperature=0,
    )
    started = monotonic()
    client = RecordingClient(config)
    with HTTPDispatcher(
        api, accepted_ref=runtime.scenario_ref, timeout_s=15, max_response_bytes=1048576
    ) as dispatcher:
        loop = AgentLoop(
            client,
            dispatcher,
            accepted,
            {operation},
            deadline=monotonic() + 120,
            stop=Event(),
            poll_interval_s=0.05,
        )
        if operation == "inspect_site":
            prompt = (
                "Inspect this human-selected synthetic site using the supplied domain tool. "
                f"site_id={json.dumps(accepted.input.site_id)}, scene_revision={accepted.input.scene_revision} (integer). "
                "After its response, return only the required final JSON with narrative and evidence_ids=[]. "
                "This is metadata only; do not invent numerical results."
            )
        else:
            layout = accepted.input.proposed_layout_ref.model_dump(mode="json")
            prompt = (
                "This task has two stages. First, evaluate the pinned proposed layout once for this human-selected synthetic task using the supplied tool. "
                f"Use layout_ref={json.dumps(layout)}. "
                "Second, read the actual tool response. When job.status is completed and result is present, evaluation is done. "
                "Do not evaluate again. Write your own brief narrative based on that response. "
                "Your final answer must start with { and end with }, with exactly the keys narrative and evidence_ids. "
                "The narrative is a string and evidence_ids is an array containing the exact observed result.run_id. "
                "No Markdown or text outside the JSON. Do not invent evidence IDs. "
                "The calculation is a synthetic one-tree diagnostic, not proof of planting feasibility."
            )
        outcome = loop.run(prompt)
        output = os.environ.get("CANOPY_LIVE_PROOF_DIR")
        if output:
            dest = Path(output)
            dest.mkdir(parents=True, exist_ok=True)
            receipt = {
                "scope": "opt-in real local model and actual TCP API; synthetic one-tree inputs only",
                "operation": operation,
                "model": model,
                "elapsed_s": monotonic() - started,
                "client_config": asdict(config),
                "loop_budget": {"deadline_s": 120, "action_budget": loop.action_budget},
                "outcome": {
                    "status": outcome.status,
                    "reason": outcome.reason,
                    "narrative": outcome.narrative,
                    "untrusted_model_narrative": outcome.untrusted_model_narrative,
                    "evidence_ids": outcome.evidence_ids,
                    "jobs": [j.model_dump(mode="json") for j in outcome.jobs],
                    "results": [r.model_dump(mode="json") for r in outcome.results],
                },
                "messages": loop.messages,
                "http": dispatcher.trace,
                "completions": client.completions,
                "model_http": client.recording.exchanges,
                "accepted_ref": runtime.scenario_ref.model_dump(mode="json"),
            }
            (dest / (operation + ".json")).write_text(
                json.dumps(
                    receipt, indent=2, allow_nan=False, default=lambda x: x.model_dump(mode="json")
                ),
                encoding="utf-8",
            )
        assert operation in loop.used_operations, f"no model-selected domain call: {outcome}"
        assert any(
            t["method"] == "POST" and t["path"] == "operations" and t["status"] == 200
            if operation == "inspect_site"
            else t["method"] == "POST" and t["path"] == "operations" and t["status"] == 202
            for t in dispatcher.trace
        )
        assert outcome.status != "failed", outcome.reason
        return outcome


def test_real_model_selects_metadata_tool_over_actual_http(live_runtime):
    outcome = run_actual_model(live_runtime, "inspect_site")
    assert outcome.status == "metadata_only", outcome
    assert not outcome.jobs and not outcome.results


def test_real_model_selects_evaluator_and_cites_actual_current_run(live_runtime):
    outcome = run_actual_model(live_runtime, "evaluate_layout")
    assert outcome.status == "completed", outcome
    assert outcome.results and outcome.evidence_ids
    assert outcome.results[0].run_id in outcome.evidence_ids
    assert outcome.results[0].metrics[0].value == 2.0
    assert outcome.results[0].layouts[0].feasibility == "not_evaluated"
