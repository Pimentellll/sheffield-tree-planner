"""Accepted-task authority is independent of model prompts and proposed edits."""

from __future__ import annotations

import pytest

from test_protocol import _accepted
from tree_planner.contracts import ScenarioInput


def changed(base: ScenarioInput, **updates) -> ScenarioInput:
    return ScenarioInput.model_validate({**base.model_dump(mode="json"), **updates})


def test_preparation_can_propose_but_not_analyse_a_budget_relaxation() -> None:
    from tree_planner.agents.policy import validate_analysis, validate_preparation

    base = _accepted()
    constraints = base.input.constraints.model_dump(mode="json")
    proposal = changed(
        base.input, constraints={**constraints, "budget_pence": constraints["budget_pence"] + 1}
    )
    validate_preparation(base, proposal)
    with pytest.raises(ValueError, match="budget"):
        validate_analysis(base, proposal)
    assert base.input.constraints.budget_pence == constraints["budget_pence"]


def test_same_task_and_stricter_budget_remain_in_scope() -> None:
    from tree_planner.agents.policy import validate_analysis

    base = _accepted()
    constraints = base.input.constraints.model_dump(mode="json")
    validate_analysis(base, base.input)
    validate_analysis(base, changed(base.input, constraints={**constraints, "budget_pence": 0}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("site_id", "other"),
        ("scene_revision", 2),
        ("semantic_revision", 2),
        ("profile_library_revision", 2),
        ("candidate_catalogue_revision", 2),
        ("candidate_catalogue_fingerprint", "f" * 64),
    ],
)
def test_model_cannot_rebind_the_source_graph(field: str, value: object) -> None:
    from tree_planner.agents.policy import validate_preparation

    base = _accepted()
    with pytest.raises(ValueError, match="source graph"):
        validate_preparation(base, changed(base.input, **{field: value}))


def test_task_scope_does_not_allow_surveys_or_case_objectives_to_disappear() -> None:
    from tree_planner.agents.policy import validate_analysis, validate_preparation

    base = _accepted()
    constraints = base.input.constraints.model_dump(mode="json")
    with pytest.raises(ValueError, match="survey"):
        validate_preparation(
            base,
            changed(
                base.input,
                constraints={**constraints, "survey_requirements": ["new-status-not-authorised"]},
            ),
        )
    cases = base.input.model_dump(mode="json")["evaluation_cases"]
    cases[0]["time_bins"][0]["duration_h"] /= 2
    with pytest.raises(ValueError, match="task field"):
        validate_analysis(base, changed(base.input, evaluation_cases=cases))


def test_model_cannot_increase_tree_count_or_extend_execution_deadline() -> None:
    from datetime import datetime, timedelta
    from tree_planner.agents.policy import validate_analysis

    base = _accepted()
    constraints = base.input.constraints.model_dump(mode="json")
    constraints["max_tree_count"] = 1
    base = base.model_copy(update={"input": changed(base.input, constraints=constraints)})
    with pytest.raises(ValueError, match="tree count"):
        validate_analysis(
            base,
            changed(
                base.input,
                constraints={**constraints, "max_tree_count": constraints["max_tree_count"] + 1},
            ),
        )
    search = base.input.search.model_dump(mode="json")
    later = datetime.fromisoformat(search["deadline_utc"].replace("Z", "+00:00")) + timedelta(
        seconds=1
    )
    with pytest.raises(ValueError, match="deadline"):
        validate_analysis(
            base,
            changed(
                base.input,
                search={**search, "deadline_utc": later.isoformat().replace("+00:00", "Z")},
            ),
        )
