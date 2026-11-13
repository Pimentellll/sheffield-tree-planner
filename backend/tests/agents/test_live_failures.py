"""Opt-in genuine local failure traces, using synthetic inputs only."""

import hashlib
import json
import os
import socket
from dataclasses import asdict
from pathlib import Path
from threading import Event
from time import monotonic

import httpx

import test_live_local as live
from tree_planner.agents import AgentLoop, ClientConfig
from tree_planner.agents.http import HTTPDispatcher
from tree_planner.contracts import EvaluateLayoutArguments

live_runtime = live.live_runtime


def save(name, data):
    output = os.environ.get("CANOPY_LIVE_PROOF_DIR")
    if output:
        dest = Path(output)
        dest.mkdir(parents=True, exist_ok=True)
        (dest / (name + ".json")).write_text(
            json.dumps(
                data, indent=2, allow_nan=False, default=lambda x: x.model_dump(mode="json")
            ),
            encoding="utf-8",
        )


def exercise(runtime, api, model_base, model, name, context):
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
    client = live.RecordingClient(config)
    started = monotonic()
    with HTTPDispatcher(
        api, accepted_ref=runtime.scenario_ref, timeout_s=15, max_response_bytes=1048576
    ) as dispatcher:
        loop = AgentLoop(
            client,
            dispatcher,
            accepted,
            {"evaluate_layout"},
            deadline=monotonic() + 120,
            stop=Event(),
            poll_interval_s=0.05,
        )
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
        outcome = None
        try:
            outcome = loop.run(prompt)
            return outcome, dispatcher.trace, loop.used_operations, client
        finally:
            save(
                name,
                {
                    "scope": "synthetic negative trace; no successful computation claimed",
                    "context": context,
                    "accepted_ref": runtime.scenario_ref.model_dump(mode="json"),
                    "client_config": asdict(config),
                    "elapsed_s": monotonic() - started,
                    "outcome": asdict(outcome) if outcome else None,
                    "messages": loop.messages,
                    "http": dispatcher.trace,
                    "completions": client.completions,
                    "model_http": client.recording.exchanges,
                },
            )


def assert_native_evaluation_selected(client, expected_layout):
    """Inspect genuine inference calls; a rejected call is not a used operation."""
    calls = [
        call
        for completion in client.completions
        for call in completion.get("message", {}).get("tool_calls", [])
        if call.get("function", {}).get("name") == "evaluate_layout"
    ]
    assert len(calls) == 1
    args = EvaluateLayoutArguments.model_validate(json.loads(calls[0]["function"]["arguments"]))
    assert args.layout_ref == expected_layout


def test_real_inference_stale_accepted_task_rejected(live_runtime):
    runtime, api, base, model = live_runtime
    ref = runtime.scenario_ref
    old = runtime.app.state.service.scenarios.get_scenario(ref)
    origin = api.removesuffix("/api/v1")
    with httpx.Client(trust_env=False, timeout=15, headers={"Origin": origin}) as http:
        response = http.put(
            f"{api}/scenarios/{ref.scenario_id}",
            json=old.input.model_dump(mode="json"),
            headers={"If-Match": f'"{ref.revision}"'},
        )
        context = {"human_put_status": response.status_code, "human_put": response.json()}
        assert response.status_code == 200, context
        new = response.json()
        assert new["revision"] == ref.revision + 1 and new["scope"] == "accepted"
        snapshot = http.get(
            f"{api}/scenarios/{ref.scenario_id}",
            params={"revision": ref.revision, "scope": "accepted"},
        )
        context.update(old_get_status=snapshot.status_code, old_snapshot=snapshot.json())
        assert snapshot.status_code == 200 and snapshot.json() == old.model_dump(mode="json")
        outcome, trace, used, client = exercise(
            runtime, api, base, model, "stale_revision", context
        )
        states = [
            http.get(
                f"{api}/scenarios/{ref.scenario_id}/selections",
                params={"revision": revision, "scope": "accepted"},
            ).json()
            for revision in (ref.revision, new["revision"])
        ]
        context["selections"] = states
        save("stale_revision_state", context)
    assert_native_evaluation_selected(client, old.input.proposed_layout_ref)
    assert not used
    assert any(
        t["method"] == "POST"
        and t["path"] == "operations"
        and t["status"] == 409
        and t["response"]["code"] == "REVISION_CONFLICT"
        for t in trace
    )
    assert outcome.status == "failed" and "REVISION_CONFLICT" in outcome.reason
    assert not outcome.jobs and not outcome.results and not outcome.evidence_ids
    assert all(
        s["evaluation"]["selection"] is None and s["evaluation"]["current_job"] is None
        for s in states
    )


def test_real_inference_changed_synthetic_asset_fails_closed(live_runtime):
    runtime, api, base, model = live_runtime
    svc = runtime.app.state.service
    accepted = svc.scenarios.get_scenario(runtime.scenario_ref)
    site = svc.scenarios.get_site(
        accepted.input.site_id, accepted.input.scene_revision, accepted.input.semantic_revision
    )
    registry = svc.assets.get(site.assets[0].ref.registry_id)
    path = svc.assets.root / registry["relative_path"]
    assert path.resolve().is_relative_to(svc.assets.root)
    original = path.read_bytes()
    assert hashlib.sha256(original).hexdigest() == registry["sha256"]
    path.write_bytes(original + b"\nsynthetic deliberate fault injection\n")
    context = {
        "asset_registry_id": registry["registry_id"],
        "relative_path": registry["relative_path"],
        "registered_sha256": registry["sha256"],
        "fault_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    try:
        outcome, trace, used, client = exercise(runtime, api, base, model, "changed_asset", context)
        selection = svc.jobs.selection(
            runtime.scenario_ref.scenario_id,
            runtime.scenario_ref.revision,
            runtime.scenario_ref.scope,
            "evaluation",
        )
        current = svc.jobs.current(
            runtime.scenario_ref.scenario_id,
            runtime.scenario_ref.revision,
            runtime.scenario_ref.scope,
            "evaluation",
        )
        save("changed_asset_state", {"selection": selection, "current_job": current})
        assert_native_evaluation_selected(client, accepted.input.proposed_layout_ref)
        assert not used
        errors = [t for t in trace if t["path"] == "operations" and t["status"] >= 400]
        failed_jobs = [j for j in outcome.jobs if j.status == "failed"]
        assert errors or failed_jobs, (outcome, trace)
        assert all(t["response"].get("code") for t in errors)
        assert outcome.status != "completed" and not outcome.results and not outcome.evidence_ids
        assert current is None
    finally:
        path.write_bytes(original)


def test_unavailable_local_runtime_transport_fails_without_dispatch(live_runtime):
    runtime, api, _, model = live_runtime
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.bind(("127.0.0.1", 0))  # bound, deliberately never listening
        unavailable = f"http://127.0.0.1:{sock.getsockname()[1]}/v1"
        outcome, trace, used, client = exercise(
            runtime,
            api,
            unavailable,
            model,
            "unavailable_runtime",
            {"socket_bound_not_listening": True},
        )
        assert outcome.status == "failed" and not outcome.jobs and not outcome.results
        assert not outcome.evidence_ids and not used and not trace
        assert len(client.completions) == 1 and "error" in client.completions[0]
        assert len(client.recording.exchanges) == 1
        assert client.recording.exchanges[0]["url"].startswith(unavailable + "/")
        assert "status" not in client.recording.exchanges[0]
    finally:
        sock.close()
