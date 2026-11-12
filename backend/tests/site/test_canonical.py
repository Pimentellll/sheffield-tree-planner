"""Exact, finite JSON identity is shared by persistence, jobs and caches."""

from __future__ import annotations

import hashlib

import pytest


def test_identity_ignores_only_object_key_order() -> None:
    from tree_planner.canonical import canonical_bytes, content_hash

    first = {"scope": "accepted", "input": {"budget_pence": 100, "points": [1.0, 2.0]}}
    second = {"input": {"points": [1.0, 2.0], "budget_pence": 100}, "scope": "accepted"}
    assert canonical_bytes(first) == canonical_bytes(second)
    assert content_hash(first) == hashlib.sha256(canonical_bytes(second)).hexdigest()
    assert content_hash(first) != content_hash({**first, "scope": "hypothetical"})
    assert content_hash(first) != content_hash({**first, "revision": 2})


def test_exact_identifiers_and_unicode_are_not_rewritten() -> None:
    from tree_planner.canonical import canonical_bytes

    assert (
        canonical_bytes({"id": "Tree-01", "label": "é"}) == '{"id":"Tree-01","label":"é"}'.encode()
    )
    assert canonical_bytes({"id": "Tree-01"}) != canonical_bytes({"id": "tree-01"})
    assert canonical_bytes({"value": 1}) != canonical_bytes({"value": 1.0})


@pytest.mark.parametrize(
    "value", [float("nan"), float("inf"), float("-inf"), {"nested": [float("nan")]}]
)
def test_nonfinite_values_are_not_hashable_snapshots(value: object) -> None:
    from tree_planner.canonical import canonical_bytes

    with pytest.raises(ValueError, match="finite"):
        canonical_bytes(value)


@pytest.mark.parametrize(
    "value", [{1: "not a JSON object key"}, (1, 2), {"x": object()}, {"bytes": b"x"}]
)
def test_non_json_values_are_rejected_without_coercion(value: object) -> None:
    from tree_planner.canonical import canonical_bytes

    with pytest.raises(ValueError, match="JSON"):
        canonical_bytes(value)


def test_full_run_key_binds_request_identity_and_referenced_content() -> None:
    from tree_planner.canonical import content_hash

    payload = {
        "scenario_ref": {"scenario_id": "s1", "revision": 1, "scope": "accepted"},
        "snapshot": {"budget_pence": 1000},
        "operation": "evaluate_layout",
        "arguments": {"layout_id": "l1", "revision": 1},
        "source_hashes": {"mesh": "a" * 64},
        "versions": {"schema": "0.1.0", "evaluator": "reference-1"},
    }
    original = content_hash(payload)
    for key, changed in [
        ("scenario_ref", {"scenario_id": "s1", "revision": 2, "scope": "accepted"}),
        ("snapshot", {"budget_pence": 999}),
        ("source_hashes", {"mesh": "b" * 64}),
        ("operation", "search_layouts"),
        ("versions", {"schema": "0.1.0", "evaluator": "reference-2"}),
    ]:
        assert content_hash({**payload, key: changed}) != original
