from concurrent.futures import ThreadPoolExecutor
import pytest
from tree_planner.site.repository import Repository, DomainError


def test_roundtrip_revision_restart_and_conflict(tmp_path):
    repo = Repository(tmp_path)
    payload = {"nested": [1, {"n": 10**40}], "label": "synthetic"}
    a = repo.create("site", payload)
    payload["nested"][1]["n"] = 2
    assert repo.get(a["ref"])["value"]["nested"][1]["n"] == 10**40
    assert Repository(tmp_path).get(a["ref"]) == a
    b = repo.replace(a["ref"], {"nested": [], "label": "synthetic"}, if_match=a["content_hash"])
    with pytest.raises(DomainError) as e:
        repo.replace(a["ref"], {}, if_match=a["content_hash"])
    assert e.value.code == "REVISION_CONFLICT"
    assert repo.get(b["ref"]) == b
    with pytest.raises(DomainError):
        repo.get({**a["ref"], "revision": 999999999999999999999999999})


def test_same_base_concurrent_writes(tmp_path):
    repo = Repository(tmp_path)
    a = repo.create("layout", {"v": 0})

    def change(i):
        try:
            return Repository(tmp_path).replace(a["ref"], {"v": i}, if_match=a["content_hash"])
        except DomainError as exc:
            return exc.code

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(change, (1, 2)))
    assert sum(isinstance(x, dict) for x in outcomes) == 1
    assert "REVISION_CONFLICT" in outcomes


def test_scope_and_human_acceptance(tmp_path):
    repo = Repository(tmp_path)
    h = repo.prepare_scenario({"synthetic": True})
    with pytest.raises(DomainError):
        repo.get({**h["ref"], "scope": "accepted"})
    assert not hasattr(repo.agent(), "accept_scenario")
    accepted = repo.accept_scenario(h["ref"])
    assert accepted["ref"]["scope"] == "accepted"
    assert accepted["source_ref"] == h["ref"]
    assert repo.get(h["ref"]) == h


def test_deterministic_content_identity(tmp_path):
    repo = Repository(tmp_path)
    assert (
        repo.create("profile", {"b": 1, "a": [2]})["content_hash"]
        == repo.create("profile", {"a": [2], "b": 1})["content_hash"]
    )


def test_invalid_reference_cannot_leak_sqlite_integer_error(tmp_path):
    repo = Repository(tmp_path)
    for revision in (10**100, -1, True):
        with pytest.raises(DomainError) as exc:
            repo.get({"kind": "site", "id": "unknown", "revision": revision})
        assert exc.value.code == "UNKNOWN_REVISION"


def test_unknown_and_hypothetical_bases_are_rejected(tmp_path):
    repo = Repository(tmp_path)
    h = repo.prepare_scenario({"synthetic": True})
    with pytest.raises(DomainError):
        repo.prepare_scenario({}, base_ref=h["ref"])
    with pytest.raises(DomainError):
        repo.prepare_scenario({}, base_ref={**h["ref"], "revision": 70, "scope": "accepted"})
