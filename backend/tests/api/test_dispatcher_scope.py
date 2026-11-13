"""A model-facing dispatcher is bound to a human-selected accepted task."""

from __future__ import annotations

import pytest

import test_app as app_fixtures
from test_app import seed

from tree_planner.api.service import AgentDispatcher
from tree_planner.contracts import ScenarioRef
from tree_planner.site.repository import DomainError

setup = app_fixtures.setup


def ref(scenario: dict) -> ScenarioRef:
    return ScenarioRef.model_validate(
        {
            "scenario_id": scenario["scenario_id"],
            "revision": scenario["revision"],
            "scope": scenario["scope"],
        }
    )


def inspect_request(site: dict) -> dict:
    return {
        "request_id": "inspect",
        "operation": "inspect_site",
        "arguments": {"site_id": site["site_id"], "scene_revision": site["scene_revision"]},
    }


def test_inspection_uses_the_task_semantic_revision_not_latest(setup):
    app, client = setup
    data = seed(client)
    accepted = client.post("/api/v1/scenarios", json=data).json()
    bound = AgentDispatcher(app.state.service, accepted_ref=ref(accepted))
    observation = bound.dispatch(inspect_request(data))
    assert observation.site_id == data["site_id"]
    assert observation.semantic_revision == data["semantic_revision"]
    assert observation.site_kind == "synthetic_test"
    assert "evaluate_layout" in observation.registered_operations
    assert not hasattr(bound, "accept_scenario")
    wrong = inspect_request({**data, "site_id": "other"})
    with pytest.raises(DomainError) as exc:
        bound.dispatch(wrong)
    assert exc.value.code == "REVISION_CONFLICT"


def test_old_task_cannot_continue_after_human_accepts_a_new_revision(setup):
    app, client = setup
    data = seed(client)
    accepted = client.post("/api/v1/scenarios", json=data).json()
    bound = AgentDispatcher(app.state.service, accepted_ref=ref(accepted))
    updated = client.put(
        "/api/v1/scenarios/" + accepted["scenario_id"], json=data, headers={"If-Match": '"1"'}
    )
    assert updated.status_code == 200
    with pytest.raises(DomainError) as exc:
        bound.dispatch(inspect_request(data))
    assert exc.value.code == "REVISION_CONFLICT"


def test_relaxation_can_be_prepared_but_not_silently_analysed(setup):
    app, client = setup
    data = seed(client)
    accepted = client.post("/api/v1/scenarios", json=data).json()
    bound = AgentDispatcher(app.state.service, accepted_ref=ref(accepted))
    proposed = {
        **data,
        "constraints": {
            **data["constraints"],
            "budget_pence": data["constraints"]["budget_pence"] + 1,
        },
    }
    draft = bound.dispatch(
        {
            "request_id": "prepare",
            "operation": "prepare_scenario",
            "arguments": {
                "base_scenario_ref": ref(accepted).model_dump(mode="json"),
                "proposed_edits": proposed,
            },
        }
    )
    assert draft.scope == "hypothetical"
    with pytest.raises(DomainError) as exc:
        bound.dispatch(
            {
                "request_id": "evaluate",
                "operation": "evaluate_layout",
                "scenario_ref": {
                    "scenario_id": draft.scenario_id,
                    "revision": draft.revision,
                    "scope": "hypothetical",
                },
                "arguments": {"layout_ref": data["proposed_layout_ref"]},
            }
        )
    assert exc.value.code == "REVISION_CONFLICT"
    assert (
        app.state.service.scenarios.get_scenario(ref(accepted)).input.constraints.budget_pence
        == data["constraints"]["budget_pence"]
    )


def test_unbound_dispatcher_does_not_infer_semantic_or_task_authority(setup):
    app, client = setup
    data = seed(client)
    with pytest.raises(DomainError):
        AgentDispatcher(app.state.service).dispatch(inspect_request(data))
