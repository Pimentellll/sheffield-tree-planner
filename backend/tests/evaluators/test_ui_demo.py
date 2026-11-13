"""The local UI harness exposes real input bindings, never invented results."""

import os
from pathlib import Path
from time import monotonic, sleep

from fastapi.testclient import TestClient
import pytest


@pytest.fixture
def ui(tmp_path):
    source = os.environ.get("CANOPY_NUMERICS_SOURCE")
    if not source:
        pytest.skip("explicit pinned numerical checkout required")
    from tree_planner.evaluators.ui_demo import create_ui_app

    front = tmp_path / "frontend-dist"
    front.mkdir()
    (front / "index.html").write_text("<html><body>M2 test frontend</body></html>")
    workspace = tmp_path / "runtime"
    app = create_ui_app(workspace, numerical_source=Path(source), frontend_dist=front)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        yield client, workspace


def test_bootstrap_binds_actual_synthetic_inputs_and_routes(ui):
    from tree_planner.contracts import M2Session

    client, _ = ui
    response = client.get("/m2/session")
    assert response.status_code == 200
    data = M2Session.model_validate(response.json())
    assert data.mode == "synthetic_one_tree_reference"
    assert data.scenario.scope == "accepted"
    assert data.layout.layout_id == data.scenario.input.proposed_layout_ref.layout_id
    assert data.source_asset_sha256 == data.site.assets[0].sha256
    assert data.scene.receiver_area_m2 == 2.0
    assert data.scene.sun_direction == (0.0, -(2**-0.5), 2**-0.5)
    assert "metrics" not in response.json() and "result" not in response.json()
    assert client.get("/").text == "<html><body>M2 test frontend</body></html>"
    assert client.get("/api/v1/health").json()["available_operations"] == ["evaluate_layout"]
    assert client.get("/inputs/synthetic-reference.json").status_code == 404


def test_bootstrap_tracks_real_human_revision_and_calculation(ui):
    client, _ = ui
    before = client.get("/m2/session").json()
    layout = before["layout"]
    layout["revision"] += 1
    layout["placements"][0]["position_enu_m"] = [3.0, -1.0, 0.0]
    registered = client.post("/api/v1/layouts", json=layout, headers={"Origin": "http://127.0.0.1"})
    assert registered.status_code == 201, registered.text
    inp = before["scenario"]["input"]
    inp["proposed_layout_ref"] = {"layout_id": layout["layout_id"], "revision": layout["revision"]}
    scenario_id = before["scenario"]["scenario_id"]
    updated = client.put(
        "/api/v1/scenarios/" + scenario_id,
        json=inp,
        headers={"Origin": "http://127.0.0.1", "If-Match": '"1"'},
    )
    assert updated.status_code == 200, updated.text
    current = client.get("/m2/session").json()
    assert current["session_id"] == before["session_id"]
    assert current["scenario"]["revision"] == 2
    assert current["layout"]["placements"][0]["position_enu_m"] == [3.0, -1.0, 0.0]
    submitted = client.post(
        "/api/v1/jobs",
        json={
            "request_id": "m2-zero-proof",
            "operation": "evaluate_layout",
            "scenario_ref": {"scenario_id": scenario_id, "revision": 2, "scope": "accepted"},
            "arguments": {"layout_ref": current["scenario"]["input"]["proposed_layout_ref"]},
        },
        headers={"Origin": "http://127.0.0.1"},
    )
    assert submitted.status_code == 202, submitted.text
    job = submitted.json()
    deadline = monotonic() + 10
    while job["status"] in {"queued", "running"} and monotonic() < deadline:
        sleep(0.02)
        job = client.get("/api/v1/jobs/" + job["job_id"]).json()
    assert job["status"] == "completed", job
    result = client.get("/api/v1/results/" + job["run_id"]).json()
    physical = [m for m in result["metrics"] if m["metric_id"] == "additional_shade"]
    assert len(physical) == 1 and physical[0]["value"] == 0.0


def test_corrupted_asset_never_bootstraps_a_trusted_view(ui):
    client, workspace = ui
    asset = workspace / "inputs/synthetic-reference.json"
    original = asset.read_bytes()
    try:
        asset.write_bytes(b"changed declared inputs")
        response = client.get("/m2/session")
        assert response.status_code == 409
        assert response.json()["code"] == "REVISION_CONFLICT"
        assert "scene" not in response.json()
    finally:
        asset.write_bytes(original)
    assert client.get("/m2/session").status_code == 200


def test_private_workspace_cannot_live_under_public_frontend(tmp_path):
    from tree_planner.evaluators.ui_demo import create_ui_app

    front = tmp_path / "dist"
    front.mkdir()
    (front / "index.html").write_text("<html>frontend</html>")
    with pytest.raises(ValueError, match="public frontend"):
        create_ui_app(
            front / "private-runtime", numerical_source=tmp_path / "unused", frontend_dist=front
        )
    assert not (front / "private-runtime").exists()
