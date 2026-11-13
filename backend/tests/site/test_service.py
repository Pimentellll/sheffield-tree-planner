"""Synthetic persistence checks; no real site or scientific outputs."""

import pytest
from tree_planner.contracts import (
    Capabilities,
    Layout,
    ScenarioInput,
    ScenarioRef,
    SiteBundle,
    TreeProfile,
)
from tree_planner.site.repository import Repository, DomainError
from tree_planner.site.assets import AssetRegistry, PURPOSES
from tree_planner.site.service import ScenarioService, geometry_fingerprint, catalogue_fingerprint
from synthetic_inputs import site_data, input_data, profile_data, placement


def ref(s):
    return ScenarioRef(scenario_id=s.scenario_id, revision=s.revision, scope=s.scope)


@pytest.fixture
def setup(tmp_path):
    root = tmp_path / "assets"
    root.mkdir()
    (root / "mesh").write_bytes(b"synthetic mesh")
    repo = Repository(tmp_path / "db")
    assets = AssetRegistry(repo, root)
    rights = {p: "permitted" for p in PURPOSES}
    source = assets.register_source(
        source_reference="synthetic",
        licence_reference="test",
        evidence=["synthetic evidence"],
        rights=rights,
    )
    asset = assets.register_from_source(
        "mesh", source_id=source["source_id"], capture_date="unknown"
    )
    d = site_data()
    d["vertical_datum"] = {"name": "synthetic", "status": "assumed", "evidence": ["synthetic"]}
    d["assets"][0].update(
        ref={"registry_id": asset["registry_id"]},
        sha256=asset["sha256"],
        source_id=source["source_id"],
    )
    d["rights"][0].update(
        source_id=source["source_id"],
        source_reference="synthetic",
        licence_reference="test",
        evidence=["synthetic evidence"],
        **rights,
    )
    provisional = SiteBundle.model_validate(d)
    d["geometry_fingerprint"] = geometry_fingerprint(provisional.assets)
    d["candidate_catalogue_fingerprint"] = catalogue_fingerprint(provisional.candidate_catalogue)
    site = SiteBundle.model_validate(d)
    caps = Capabilities(
        evaluator_versions=["synthetic-test@unit"],
        solar_versions=["synthetic-test@unit"],
        search_versions=["synthetic-test@unit"],
    )
    svc = ScenarioService(repo, assets, caps, geometry_refs=frozenset({"mesh"}))
    svc.register_site(site)
    svc.register_profile(TreeProfile.model_validate(profile_data()))
    svc.register_layout(
        Layout(
            schema_version="0.1.0",
            layout_id="synthetic-layout",
            revision=1,
            kind="proposed",
            placements=[placement()],
        )
    )
    inp = input_data()
    inp["candidate_catalogue_fingerprint"] = site.candidate_catalogue_fingerprint
    return svc, site, ScenarioInput.model_validate(inp), root


def test_roundtrip_immutability_and_analysis(setup):
    svc, site, inp, _ = setup
    assert svc.get_site(site.site_id, 1, 1) == site
    assert svc.register_site(site) == site
    d = site.model_dump(mode="json")
    d["name"] = "changed"
    with pytest.raises(DomainError, match="different content"):
        svc.register_site(SiteBundle.model_validate(d))
    scenario = svc.create_accepted(inp)
    deps, hashes = svc.resolve_for_job(ref(scenario))
    assert (
        deps["site"]["site_id"] == site.site_id and hashes["geometry"] == site.geometry_fingerprint
    )
    assert svc.get_scenario(ref(scenario)) == scenario


def test_draft_acceptance_and_atomicity(setup):
    svc, _, inp, _ = setup
    base = svc.create_accepted(inp)
    draft = svc.agent().prepare_scenario(inp, base_ref=ref(base))
    assert not hasattr(svc.agent(), "accept_scenario")
    dependencies, _ = svc.resolve_for_job(ref(draft))
    assert dependencies["base_scenario"]["scenario_id"] == base.scenario_id
    assert svc.get_scenario(ref(draft)).scope == "hypothetical"

    def fail(scenario_id, revision, *, connection):
        connection.execute("CREATE TABLE rollback_test (value INTEGER)")
        raise RuntimeError("rollback")

    with pytest.raises(RuntimeError):
        svc.accept_scenario(ref(draft), if_match=1, on_accept=fail)
    accepted = svc.accept_scenario(ref(draft), if_match=1)
    assert (accepted.scenario_id, accepted.revision) == (base.scenario_id, 2)
    assert svc.acceptance_source(ref(accepted)) == ref(draft)
    with pytest.raises(DomainError) as exc:
        svc.accept_scenario(ref(draft), if_match=1)
    assert exc.value.code == "REVISION_CONFLICT"
    with svc.repository.transaction() as db:
        assert (
            db.execute("SELECT name FROM sqlite_master WHERE name='rollback_test'").fetchone()
            is None
        )


def test_stale_head_scope_huge_revision_and_tamper(setup):
    svc, _, inp, _ = setup
    base = svc.create_accepted(inp)
    draft = svc.prepare_scenario(inp, base_ref=ref(base))
    svc.replace_accepted(ref(base), inp, if_match=1)
    with pytest.raises(DomainError) as exc:
        svc.accept_scenario(ref(draft), if_match=1)
    assert exc.value.code == "REVISION_CONFLICT"
    with pytest.raises(DomainError):
        svc.get_scenario(
            ScenarioRef(scenario_id=base.scenario_id, revision=1, scope="hypothetical")
        )
    with pytest.raises(DomainError):
        svc.get_scenario(
            ScenarioRef(scenario_id=base.scenario_id, revision=10**100, scope="accepted")
        )
    with svc.repository.transaction() as db:
        db.execute(
            "UPDATE snapshots SET payload=? WHERE kind='scenario' AND id=? AND revision=1",
            (b"{}", base.scenario_id),
        )
    with pytest.raises(DomainError):
        svc.get_scenario(ref(base))


def test_changed_asset_and_unresolved_refs(setup):
    svc, site, inp, root = setup
    bad = inp.model_dump(mode="json")
    bad["scene_revision"] = 2
    with pytest.raises(DomainError):
        svc.prepare_scenario(ScenarioInput.model_validate(bad))
    bad = inp.model_dump(mode="json")
    bad["evaluation_cases"][0]["profile_state"] = "missing"
    with pytest.raises(DomainError):
        svc.prepare_scenario(ScenarioInput.model_validate(bad))
    (root / "mesh").write_bytes(b"changed")
    with pytest.raises(DomainError):
        svc.get_site(site.site_id, 1, 1)


def test_unavailable_capabilities_allow_draft_but_block_analysis(setup):
    svc, _, inp, _ = setup
    svc.capabilities = Capabilities(evaluator_versions=[], solar_versions=[], search_versions=[])
    assert svc.prepare_scenario(inp)
    accepted = svc.create_accepted(inp)
    with pytest.raises(DomainError) as exc:
        svc.resolve_for_job(ref(accepted))
    assert exc.value.code == "UNSUPPORTED_OPERATION"


def test_fingerprints_source_and_registry_integrity(setup):
    svc, site, _, _ = setup
    d = site.model_dump(mode="json")
    d["geometry_fingerprint"] = "0" * 64
    with pytest.raises(DomainError):
        svc.register_site(SiteBundle.model_validate(d))
    d = site.model_dump(mode="json")
    d["candidate_catalogue_fingerprint"] = "0" * 64
    with pytest.raises(DomainError):
        svc.register_site(SiteBundle.model_validate(d))
    d = site.model_dump(mode="json")
    d["rights"][0]["licence_reference"] = "changed"
    with pytest.raises(DomainError):
        svc.register_site(SiteBundle.model_validate(d))
    with svc.repository.transaction() as db:
        db.execute(
            "UPDATE assets SET metadata=? WHERE id=?", (b"{}", site.assets[0].ref.registry_id)
        )
    with pytest.raises(DomainError):
        svc.get_site(site.site_id, 1, 1)


def test_unknown_rights_and_client_readiness_spoof(tmp_path):
    root = tmp_path / "files"
    root.mkdir()
    (root / "mesh").write_bytes(b"synthetic")
    repo = Repository(tmp_path / "db")
    assets = AssetRegistry(repo, root)
    rights = {p: "unknown" for p in PURPOSES}
    source = assets.register_source(
        source_reference="synthetic", licence_reference="unknown", evidence=[], rights=rights
    )
    asset = assets.register_from_source(
        "mesh", source_id=source["source_id"], capture_date="unknown"
    )
    d = site_data()
    d["assets"][0].update(
        ref={"registry_id": asset["registry_id"]},
        sha256=asset["sha256"],
        source_id=source["source_id"],
    )
    d["rights"][0].update(
        source_id=source["source_id"],
        source_reference="synthetic",
        licence_reference="unknown",
        evidence=[],
        **rights,
    )
    temp = SiteBundle.model_validate(d)
    d["geometry_fingerprint"] = geometry_fingerprint(temp.assets)
    d["candidate_catalogue_fingerprint"] = catalogue_fingerprint(temp.candidate_catalogue)
    site = SiteBundle.model_validate(d)
    caps = Capabilities(evaluator_versions=[], solar_versions=[], search_versions=[])
    svc = ScenarioService(repo, assets, caps, geometry_refs=frozenset({"mesh"}))
    svc.register_site(site)
    svc.register_profile(TreeProfile.model_validate(profile_data()))
    svc.register_layout(
        Layout(
            schema_version="0.1.0",
            layout_id="synthetic-layout",
            revision=1,
            kind="proposed",
            placements=[placement()],
        )
    )
    inp = input_data()
    inp["candidate_catalogue_fingerprint"] = site.candidate_catalogue_fingerprint
    inp = ScenarioInput.model_validate(inp)
    assert svc.readiness(site.site_id, 1, 1).blockers
    assert svc.prepare_scenario(inp)
    s = svc.create_accepted(inp)
    with pytest.raises(DomainError) as exc:
        svc.resolve_for_job(ref(s))
    assert exc.value.code == "RIGHTS_UNKNOWN"
    for purpose in PURPOSES:
        with pytest.raises(DomainError):
            assets.read(asset["registry_id"], purpose)


def test_evaluation_admission_does_not_require_an_unexecuted_search_algorithm(setup):
    svc, _, inp, _ = setup
    svc.capabilities = Capabilities(
        evaluator_versions=["synthetic-test@unit"],
        solar_versions=["synthetic-test@unit"],
        search_versions=[],
    )
    accepted = svc.create_accepted(inp)
    dependencies, _ = svc.resolve_for_job(ref(accepted), operation="evaluate_layout")
    assert dependencies["scenario"]["scope"] == "accepted"
    with pytest.raises(DomainError) as exc:
        svc.resolve_for_job(ref(accepted), operation="search_layouts")
    assert exc.value.code == "UNSUPPORTED_OPERATION"


def test_hypothetical_resolution_keeps_an_explicit_accepted_base(setup):
    svc, _, inp, _ = setup
    accepted = svc.create_accepted(inp)
    draft = svc.prepare_scenario(inp, base_ref=ref(accepted))
    dependencies, hashes = svc.resolve_for_job(ref(draft))
    assert dependencies["scenario"]["scope"] == "hypothetical"
    assert dependencies["base_scenario"]["scenario_id"] == accepted.scenario_id
    assert "base_scenario" in hashes
    unbased = svc.prepare_scenario(inp)
    with pytest.raises(DomainError) as exc:
        svc.resolve_for_job(ref(unbased))
    assert exc.value.code == "REVISION_CONFLICT"


def test_unresolved_geometry_and_if_match(setup):
    svc, _, inp, _ = setup
    base = svc.create_accepted(inp)
    draft = svc.prepare_scenario(inp, base_ref=ref(base))
    with pytest.raises(DomainError) as exc:
        svc.accept_scenario(ref(draft), if_match=2)
    assert exc.value.code == "REVISION_CONFLICT"
    svc.geometry_refs = None
    with pytest.raises(DomainError) as exc:
        svc.resolve_for_job(ref(base))
    assert exc.value.code == "SITE_NOT_READY"


@pytest.mark.parametrize(
    "field,value",
    [
        ("profile_library_revision", 2),
        ("candidate_catalogue_revision", 2),
        ("semantic_revision", 2),
        ("candidate_catalogue_fingerprint", "0" * 64),
        ("target_ids", ["missing"]),
    ],
)
def test_stale_input_references(setup, field, value):
    svc, _, inp, _ = setup
    d = inp.model_dump(mode="json")
    d[field] = value
    if field == "target_ids":
        d["evaluation_cases"][0]["target_ids"] = value
        d["evaluation_cases"][0]["target_weights"] = {"missing": 1}
    with pytest.raises(DomainError):
        svc.prepare_scenario(ScenarioInput.model_validate(d))


def test_unresolved_layout_and_geometry_overlap_provider(setup):
    svc, _, inp, _ = setup
    d = inp.model_dump(mode="json")
    d["proposed_layout_ref"]["revision"] = 2
    with pytest.raises(DomainError):
        svc.prepare_scenario(ScenarioInput.model_validate(d))
    draft = svc.prepare_scenario(inp)
    assert draft.base_scenario_ref is None
    with pytest.raises(DomainError):
        svc.accept_scenario(ref(draft), if_match=1)


def test_real_job_store_activation_in_same_transaction(setup):
    from tree_planner.jobs import JobStore

    svc, _, inp, _ = setup
    jobs = JobStore(svc.repository.db_path)
    first = svc.create_accepted(inp, on_accept=jobs.activate)
    draft = svc.prepare_scenario(inp, base_ref=ref(first))
    second = svc.accept_scenario(ref(draft), if_match=first.revision, on_accept=jobs.activate)
    assert second.revision == 2
