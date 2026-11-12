"""A host-pinned HTTP investigation may not silently follow a new acceptance."""

import test_app as app_fixtures
from test_app import seed

setup = app_fixtures.setup


def test_operation_task_headers_are_current_and_atomic(setup):
    _, client = setup
    inp = seed(client)
    accepted = client.post("/api/v1/scenarios", json=inp).json()
    body = {
        "request_id": "inspect-http",
        "operation": "inspect_site",
        "arguments": {"site_id": inp["site_id"], "scene_revision": inp["scene_revision"]},
    }
    headers = {"X-Canopy-Scenario-Id": accepted["scenario_id"], "X-Canopy-Scenario-Revision": "1"}
    assert client.post("/api/v1/operations", json=body, headers=headers).status_code == 200
    assert (
        client.put(
            "/api/v1/scenarios/" + accepted["scenario_id"], json=inp, headers={"If-Match": '"1"'}
        ).status_code
        == 200
    )
    stale = client.post("/api/v1/operations", json=body, headers=headers)
    assert stale.status_code == 409, stale.text
    assert stale.json()["code"] == "REVISION_CONFLICT"
    partial = client.post(
        "/api/v1/operations", json=body, headers={"X-Canopy-Scenario-Id": accepted["scenario_id"]}
    )
    assert partial.status_code == 422
    assert partial.json()["code"] == "INVALID_INPUT"
