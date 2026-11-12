"""Server-owned investigation scope; model proposals are never approvals."""

from __future__ import annotations

from datetime import datetime

from tree_planner.contracts import Scenario, ScenarioInput

_SOURCE_FIELDS = (
    "site_id",
    "scene_revision",
    "semantic_revision",
    "profile_library_revision",
    "candidate_catalogue_revision",
    "candidate_catalogue_fingerprint",
)


def validate_preparation(accepted: Scenario, proposed: ScenarioInput) -> None:
    """Permit a labelled proposal without granting new evidence or survey status."""
    if accepted.scope != "accepted":
        raise ValueError("An accepted task is required")
    for field in _SOURCE_FIELDS:
        if getattr(accepted.input, field) != getattr(proposed, field):
            raise ValueError("A model cannot rebind the accepted source graph")
    if proposed.constraints.survey_requirements != accepted.input.constraints.survey_requirements:
        raise ValueError("A model cannot change survey requirements")
    if not set(accepted.input.assumptions).issubset(proposed.assumptions):
        raise ValueError("A model cannot remove accepted uncertainty declarations")


def validate_analysis(accepted: Scenario, proposed: ScenarioInput) -> None:
    """Default task policy permits only conservative bounded what-if analyses.

    Relaxations can be prepared for human review, but require a new accepted task
    before computation. Layout choice and seed may change; the evidence graph,
    cases, numerical definitions and all other hard constraints remain pinned.
    """
    validate_preparation(accepted, proposed)
    original = accepted.input.model_dump(mode="json")
    candidate = proposed.model_dump(mode="json")
    for field in original:
        if (
            field not in {"constraints", "proposed_layout_ref", "search", "assumptions"}
            and original[field] != candidate[field]
        ):
            raise ValueError("Analysis changes an accepted task field")
    before = original["constraints"]
    after = candidate["constraints"]
    if after["budget_pence"] > before["budget_pence"]:
        raise ValueError("Analysis exceeds the accepted budget")
    old_count, new_count = before["max_tree_count"], after["max_tree_count"]
    if old_count is not None and (new_count is None or new_count > old_count):
        raise ValueError("Analysis exceeds the accepted tree count")
    for field in before:
        if field not in {"budget_pence", "max_tree_count"} and before[field] != after[field]:
            raise ValueError("Analysis changes an accepted hard constraint")
    for field in original["search"]:
        if (
            field not in {"seed", "deadline_utc"}
            and original["search"][field] != candidate["search"][field]
        ):
            raise ValueError("Analysis changes an accepted search policy")
    old_deadline = datetime.fromisoformat(original["search"]["deadline_utc"].replace("Z", "+00:00"))
    new_deadline = datetime.fromisoformat(
        candidate["search"]["deadline_utc"].replace("Z", "+00:00")
    )
    if new_deadline > old_deadline:
        raise ValueError("Analysis extends the accepted execution deadline")
