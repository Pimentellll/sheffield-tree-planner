"""Execution configuration belongs to authoritative job/cache identity."""

from __future__ import annotations

import test_app as app_fixtures
from test_app import seed

setup = app_fixtures.setup


def request_for(scenario: dict, inp: dict, request_id: str) -> dict:
    return {
        "request_id": request_id,
        "operation": "evaluate_layout",
        "scenario_ref": {
            "scenario_id": scenario["scenario_id"],
            "revision": scenario["revision"],
            "scope": scenario["scope"],
        },
        "arguments": {"layout_ref": inp["proposed_layout_ref"]},
    }


def test_provider_code_or_input_hash_changes_the_admitted_fingerprint(setup, monkeypatch):
    app, client = setup
    inp = seed(client)
    scenario = client.post("/api/v1/scenarios", json=inp).json()
    configuration = {"provider-code": "a" * 64, "numerical-inputs": "b" * 64}
    handler = app.state.service.handlers["evaluate_layout"]
    monkeypatch.setattr(
        handler, "execution_hashes", lambda deps, *, operation: dict(configuration), raising=False
    )
    first = client.post("/api/v1/jobs", json=request_for(scenario, inp, "identity-one"))
    assert first.status_code == 202, first.text
    configuration["numerical-inputs"] = "c" * 64
    second = client.post("/api/v1/jobs", json=request_for(scenario, inp, "identity-two"))
    assert second.status_code == 202, second.text
    assert first.json()["input_fingerprint"] != second.json()["input_fingerprint"]
    configuration["provider-code"] = "d" * 64
    third = client.post("/api/v1/jobs", json=request_for(scenario, inp, "identity-three"))
    assert third.status_code == 202, third.text
    assert third.json()["input_fingerprint"] != second.json()["input_fingerprint"]
    _, hashes = app.state.service.resolve_for_execution(
        app.state.service.jobs.active_ref(), operation="evaluate_layout"
    )
    assert hashes["execution:provider-code"] == configuration["provider-code"]


def test_invalid_server_execution_hash_never_admits_a_job(setup, monkeypatch):
    app, client = setup
    inp = seed(client)
    scenario = client.post("/api/v1/scenarios", json=inp).json()
    monkeypatch.setattr(
        app.state.service.handlers["evaluate_layout"],
        "execution_hashes",
        lambda deps, *, operation: {"unverified": "not-a-hash"},
        raising=False,
    )
    response = client.post("/api/v1/jobs", json=request_for(scenario, inp, "invalid-provider"))
    assert response.status_code == 503, response.text
    assert response.json()["code"] == "TOOL_UNAVAILABLE"
