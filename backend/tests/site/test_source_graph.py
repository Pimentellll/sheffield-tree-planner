"""Portable source admission proofs using synthetic inputs and real local storage."""

import pytest

from synthetic_inputs import placement, profile_data
import test_service as service_fixtures
from test_service import ref

from tree_planner.canonical import content_hash
from tree_planner.contracts import JobRequest, Layout, ScenarioInput, SiteBundle, TreeProfile
from tree_planner.site.assets import PURPOSES
from tree_planner.site.repository import DomainError
from tree_planner.site.service import catalogue_fingerprint

setup = service_fixtures.setup


PROVENANCE = (
    "target",
    "planting_regions",
    "exclusions",
    "existing_trees",
    "protected_surfaces",
    "candidate",
    "allowed_profile",
    "candidate_profile",
    "placed_profile",
    "case",
)


def source(svc, status="permitted", evidence=None):
    return svc.assets.register_source(
        source_reference="synthetic private measurements C:/private/measurements.csv",
        licence_reference="synthetic local declaration",
        evidence=["synthetic private permission receipt"] if evidence is None else evidence,
        rights={p: status for p in PURPOSES},
    )


def cite(svc, site, inp, where, source_ids, *, assumption_ids=(), record=None):
    """Persist exact declarations; never substitute guessed provenance."""
    data, request = site.model_dump(mode="json"), inp.model_dump(mode="json")
    revision = site.semantic_revision + 1
    provenance = dict(source_ids=source_ids, assumption_ids=list(assumption_ids))
    if where == "case":
        request["evaluation_cases"][0].update(provenance)
    elif where.endswith("_profile"):
        profile = profile_data()
        profile.update(profile_id=f"graph-profile-{revision}", **provenance)
        svc.register_profile(TreeProfile.model_validate(profile))
        if where == "candidate_profile":
            data["candidate_catalogue"] = [
                dict(
                    candidate_id="c",
                    location_id="l",
                    position_enu_m=[1, 0, 0],
                    profile_id=profile["profile_id"],
                    plantability_status="provisional",
                    source_ids=[],
                    assumption_ids=["synthetic candidate assumption"],
                )
            ]
        else:
            request["constraints"]["allowed_profile_ids"] = [profile["profile_id"]]
            if where == "placed_profile":
                placed = placement()
                placed["profile_id"] = profile["profile_id"]
                layout = Layout(
                    schema_version="0.1.0",
                    layout_id=f"graph-layout-{revision}",
                    revision=1,
                    kind="proposed",
                    placements=[placed],
                )
                svc.register_layout(layout)
                request["proposed_layout_ref"] = dict(layout_id=layout.layout_id, revision=1)
            else:
                # This profile participates solely through the allowed set.
                request["proposed_layout_ref"] = None
    elif where == "target":
        data["targets"][0].update(evidence_status="sourced", **provenance)
    elif where == "candidate":
        data["candidate_catalogue"] = [
            dict(
                candidate_id="c",
                location_id="l",
                position_enu_m=[1, 0, 0],
                profile_id="synthetic-profile",
                plantability_status="documented_model_region",
                **provenance,
            )
        ]
    elif where in ("asset", "rights_only"):
        right = dict(
            source_id=record["source_id"],
            source_reference=record["source_reference"],
            licence_reference=record["licence_reference"],
            evidence=record["evidence"],
            required_attribution="Synthetic only",
            **record["rights"],
        )
        if where == "asset":
            asset = svc.assets.register_from_source(
                "mesh", source_id=record["source_id"], capture_date="unknown"
            )
            data["assets"][0].update(
                ref={"registry_id": asset["registry_id"]},
                source_id=record["source_id"],
                sha256=asset["sha256"],
            )
            data["rights"] = [right]
        else:
            data["rights"].append(right)
    else:
        data[where] = [
            dict(feature_id=where, geometry_ref="mesh", evidence_status="sourced", **provenance)
        ]
    data["semantic_revision"] = revision
    provisional = SiteBundle.model_validate(data)
    data["candidate_catalogue_fingerprint"] = catalogue_fingerprint(provisional.candidate_catalogue)
    site = SiteBundle.model_validate(data)
    svc.register_site(site)
    request.update(
        semantic_revision=revision,
        candidate_catalogue_fingerprint=site.candidate_catalogue_fingerprint,
    )
    request["search"]["deadline_utc"] = "2099-01-01T00:00:00Z"
    return site, ScenarioInput.model_validate(request)


@pytest.mark.parametrize("where", PROVENANCE)
def test_analysis_rejects_unresolved_source_id(setup, where):
    svc, site, inp, _ = setup
    _, inp = cite(
        svc, site, inp, where, ["unregistered-source"], assumption_ids=["explicit assumption"]
    )
    # Unknown evidence remains ingestible/preparable, including accepted snapshots.
    assert svc.prepare_scenario(inp)
    scenario = svc.create_accepted(inp)
    with pytest.raises(DomainError) as exc:
        svc.resolve_for_job(ref(scenario), operation="evaluate_layout")
    assert exc.value.code == "UNKNOWN_REVISION"
    assert "unregistered-source" not in str(exc.value)
    assert svc.get_scenario(ref(scenario)).input == inp


@pytest.mark.parametrize("where", PROVENANCE + ("asset", "rights_only"))
@pytest.mark.parametrize(
    "status,evidence,code",
    [
        ("restricted", ["synthetic private receipt"], "RIGHTS_RESTRICTED"),
        ("unknown", ["synthetic private receipt"], "RIGHTS_UNKNOWN"),
        ("permitted", [], "RIGHTS_UNKNOWN"),
        ("permitted", ["synthetic private receipt"], None),
    ],
)
def test_complete_source_graph_local_permission(setup, where, status, evidence, code):
    svc, site, inp, _ = setup
    record = source(svc, status, evidence)
    site, inp = cite(svc, site, inp, where, [record["source_id"]], record=record)
    assert svc.prepare_scenario(inp)
    scenario = svc.create_accepted(inp)
    if code:
        with pytest.raises(DomainError) as exc:
            svc.resolve_for_job(ref(scenario), operation="evaluate_layout")
        assert exc.value.code == code
        assert not exc.value.details
        for private in (
            record["source_id"],
            record["source_reference"],
            record["licence_reference"],
            *evidence,
        ):
            assert private not in str(exc.value)
    else:
        deps, hashes = svc.resolve_for_job(ref(scenario), operation="evaluate_layout")
        assert deps["sources"][record["source_id"]] == record
        assert hashes["sources"] == content_hash(deps["sources"])
        if where not in ("asset", "rights_only"):
            assert record["source_id"] not in {r.source_id for r in site.rights}


@pytest.mark.parametrize("where", PROVENANCE)
def test_analysis_requires_an_explicit_source_or_assumption_declaration(setup, where):
    svc, site, inp, _ = setup
    _, inp = cite(svc, site, inp, where, [])
    scenario = svc.create_accepted(inp)
    assert svc.prepare_scenario(inp)
    with pytest.raises(DomainError) as exc:
        svc.resolve_for_job(ref(scenario), operation="evaluate_layout")
    assert exc.value.code == "RIGHTS_UNKNOWN"


@pytest.mark.parametrize("where", PROVENANCE)
def test_explicit_assumptions_remain_literal_without_invented_sources(setup, where):
    svc, site, inp, _ = setup
    _, inp = cite(svc, site, inp, where, [], assumption_ids=["literal synthetic assumption"])
    scenario = svc.create_accepted(inp)
    deps, _ = svc.resolve_for_job(ref(scenario), operation="evaluate_layout")
    assert set(deps["sources"]) == {site.assets[0].source_id}
    assert svc.get_scenario(ref(scenario)).input == inp


def test_source_reference_is_not_guessed_to_be_a_source_id(setup):
    svc, site, inp, _ = setup
    record = source(svc)
    _, inp = cite(svc, site, inp, "target", [record["source_reference"]])
    scenario = svc.create_accepted(inp)
    with pytest.raises(DomainError) as exc:
        svc.resolve_for_job(ref(scenario), operation="evaluate_layout")
    assert exc.value.code == "UNKNOWN_REVISION"
    assert record["source_reference"] not in str(exc.value)


def test_analysis_only_requires_local_permission_for_participating_sources(setup):
    svc, site, inp, _ = setup
    source(svc, "restricted")  # Unreferenced registry records are not dependencies.
    record = svc.assets.register_source(
        source_reference="synthetic local-only measurements",
        licence_reference="synthetic local use",
        evidence=["synthetic local receipt"],
        rights={p: "permitted" if p == "local_use_status" else "restricted" for p in PURPOSES},
    )
    _, inp = cite(svc, site, inp, "case", [record["source_id"]])
    scenario = svc.create_accepted(inp)
    deps, _ = svc.resolve_for_job(ref(scenario), operation="evaluate_layout")
    assert set(deps["sources"]) == {site.assets[0].source_id, record["source_id"]}


@pytest.mark.parametrize("where", PROVENANCE)
def test_source_identity_changes_dependency_fingerprint(setup, where):
    svc, site, inp, _ = setup
    first, second = source(svc), source(svc)
    assert {k: v for k, v in first.items() if k != "source_id"} == {
        k: v for k, v in second.items() if k != "source_id"
    }
    site, inp = cite(svc, site, inp, where, [first["source_id"]])
    original = svc.create_accepted(inp)
    deps1, hashes1 = svc.resolve_for_job(ref(original), operation="evaluate_layout")
    _, changed = cite(svc, site, inp, where, [second["source_id"]])
    accepted = svc.replace_accepted(ref(original), changed, if_match=1)
    deps2, hashes2 = svc.resolve_for_job(ref(accepted), operation="evaluate_layout")
    assert hashes1["sources"] != hashes2["sources"]
    assert first["source_id"] in deps1["sources"] and second["source_id"] not in deps1["sources"]
    assert second["source_id"] in deps2["sources"] and first["source_id"] not in deps2["sources"]
    assert svc.resolve_for_job(ref(original), operation="evaluate_layout") == (deps1, hashes1)


def test_public_submission_rejects_profile_with_unlisted_restricted_source(setup):
    from tree_planner.api.service import ApplicationService

    svc, site, inp, root = setup
    record = source(svc, "restricted")
    _, inp = cite(svc, site, inp, "placed_profile", [record["source_id"]])
    app = ApplicationService(
        svc.repository.workspace,
        approved_asset_root=root,
        capabilities=svc.capabilities,
        geometry_refs=frozenset({"mesh"}),
        handlers={"evaluate_layout": lambda *args: None},
    )
    scenario = app.create_accepted(inp)
    request = JobRequest.model_validate(
        dict(
            request_id="restricted-profile-proof",
            scenario_ref=ref(scenario).model_dump(mode="json"),
            operation="evaluate_layout",
            arguments={"layout_ref": inp.proposed_layout_ref.model_dump(mode="json")},
        )
    )
    with pytest.raises(DomainError) as exc:
        app.submit(request)
    assert exc.value.code == "RIGHTS_RESTRICTED"
    with svc.repository.transaction() as db:
        assert db.execute("SELECT COUNT(*) FROM job_records").fetchone()[0] == 0


@pytest.mark.parametrize(
    "status,code", [("restricted", "RIGHTS_RESTRICTED"), ("unknown", "RIGHTS_UNKNOWN")]
)
def test_http_source_error_does_not_leak_private_evidence(setup, status, code):
    from fastapi.testclient import TestClient
    from tree_planner.api import create_app

    svc, site, inp, root = setup
    record = source(svc, status)
    _, inp = cite(svc, site, inp, "placed_profile", [record["source_id"]])
    app = create_app(
        svc.repository.workspace,
        approved_asset_root=root,
        capabilities=svc.capabilities,
        geometry_refs=frozenset({"mesh"}),
        handlers={"evaluate_layout": lambda *args: None},
        start_worker=False,
    )
    scenario = app.state.service.create_accepted(inp)
    with TestClient(
        app, base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"}
    ) as client:
        response = client.post(
            "/api/v1/jobs",
            json=dict(
                request_id="private-source-error",
                scenario_ref=ref(scenario).model_dump(mode="json"),
                operation="evaluate_layout",
                arguments={"layout_ref": inp.proposed_layout_ref.model_dump(mode="json")},
            ),
        )
    assert response.status_code == 422
    assert response.json()["code"] == code
    assert response.json()["details"] == {}
    for private in (
        record["source_id"],
        record["source_reference"],
        record["licence_reference"],
        *record["evidence"],
    ):
        assert private not in response.text
