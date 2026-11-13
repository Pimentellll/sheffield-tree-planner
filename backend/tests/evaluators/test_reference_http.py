"""Actual HTTP/SQLite integration, with explicitly synthetic numerical INPUTS."""

import importlib.util
import math
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tree_planner.api import create_app
from tree_planner.contracts import Capabilities, Result, ScenarioRef
from tree_planner.evaluators import ReferenceInputs, ReferenceJobHandler, ReferenceProvider
from tree_planner.evaluators.runtime import load_numerics

HASHES = {
    "shade_reference.py": "128ef3f607933785bb895a651f225a54a3d4af605a607ff28cfc3918f89d65ce",
    "ray.py": "7eb34bdaa967a0b01bbda977b2c2cd8385b19196609574d9ddea5aa4867b7198",
}


@pytest.fixture(scope="module")
def numerical():
    source = os.environ.get("CANOPY_NUMERICS_SOURCE")
    if not source:
        pytest.skip("CANOPY_NUMERICS_SOURCE is not configured; real numerical integration not run")
    return load_numerics(Path(source)).shade


def api_helpers():
    path = Path(__file__).resolve().parents[1] / "api/test_app.py"
    spec = importlib.util.spec_from_file_location("existing_api_synthetic_helpers", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize(
    "mode,expected",
    [
        ("shadow", 2.0),
        ("miss", 0.0),
        ("night", 0.0),
        ("occluded", 0.0),
        ("malformed", None),
        ("hash_mismatch", None),
        ("binding_mismatch", None),
        ("cancel_during", None),
        ("hash_after", None),
        ("inputs_after", None),
    ],
)
def test_http_actual_reference(numerical, tmp_path, mode, expected):
    p = numerical
    root = tmp_path / "inputs"
    root.mkdir()
    (root / "mesh").write_bytes(b"synthetic geometry input")
    holder = {}

    def resolve(ref, *, operation):
        deps, hashes = holder["app"].state.service.resolve_for_execution(ref, operation=operation)
        if mode == "hash_mismatch" or (mode == "hash_after" and holder.get("computed")):
            hashes["geometry"] = "f" * 64
        holder.setdefault("resolved_hashes", []).append(hashes)
        return deps, hashes

    def inputs(deps, request):
        from datetime import datetime

        scenario = deps["scenario"]
        case = scenario["input"]["evaluation_cases"][0]
        placement = deps["layout"]["placements"][0]
        x, y, z = placement["position_enu_m"]
        tree = p.ProposedTree(
            p.OpaqueEllipsoid((x, y, z + 1), (0.5, 0.5, 0.5)), p.OpaqueTrunk(x, y, z, 0.1, 2)
        )
        sun = (
            (0, 0, 1)
            if mode == "inputs_after" and holder.get("computed")
            else (0, -math.sqrt(0.5), math.sqrt(0.5))
        )
        bins = tuple(
            p.DraftSolarBin(
                datetime.fromisoformat(b["midpoint_utc"].replace("Z", "+00:00")),
                b["duration_h"],
                sun,
                mode != "night",
            )
            for b in case["time_bins"]
        )
        obstacles = (p.OpaqueEllipsoid((0, -1, 1), (0.5, 0.5, 0.5)),) if mode == "occluded" else ()
        return (
            ReferenceInputs(
                request.scenario_ref,
                deps["layout"]["layout_id"],
                deps["layout"]["revision"],
                placement["placement_id"],
                case["case_id"],
                case["horizon_years"],
                case["target_ids"][0],
                (
                    p.ReceiverSample(
                        (0, 0, 0), (0, 0, 2) if mode == "malformed" else (0, 0, 1), 2, "target"
                    ),
                ),
                bins,
                obstacles,
                tree,
            )
            if mode != "binding_mismatch"
            else ReferenceInputs(
                request.scenario_ref,
                "wrong",
                deps["layout"]["revision"],
                placement["placement_id"],
                case["case_id"],
                case["horizon_years"],
                case["target_ids"][0],
                (p.ReceiverSample((0, 0, 0), (0, 0, 1), 2, "target"),),
                bins,
                obstacles,
                tree,
            )
        )

    def evaluate(*args, **kwargs):
        result = p.evaluate_one_tree_synthetic(*args, **kwargs)
        holder["computed"] = True
        if mode == "cancel_during":
            holder["app"].state.jobs.cancel(holder["job_id"])
        return result

    provider = ReferenceProvider(
        resolve,
        inputs,
        evaluate,
        "synthetic",
        "unit",
        "synthetic",
        "unit",
        tuple(HASHES.items()),
        synthetic_stub=True,
    )

    class DiagnosticHandler(ReferenceJobHandler):
        def __call__(self, *args, **kwargs):
            try:
                return super().__call__(*args, **kwargs)
            except Exception as exc:
                holder["failure"] = str(exc)
                raise

    caps = Capabilities(
        evaluator_versions=["synthetic@unit"],
        solar_versions=["synthetic@unit"],
        search_versions=["synthetic@unit"],
    )
    app = create_app(
        tmp_path / "workspace",
        approved_asset_root=root,
        capabilities=caps,
        geometry_refs=frozenset({"mesh"}),
        handlers={"evaluate_layout": DiagnosticHandler(provider)},
        start_worker=False,
    )
    holder["app"] = app
    h = api_helpers()
    with TestClient(
        app, base_url="http://127.0.0.1:8000", headers={"Origin": "http://127.0.0.1:8000"}
    ) as client:
        inp = h.seed(client)
        profile = dict(
            schema_version="0.1.0",
            profile_id="tree",
            library_revision=1,
            species_size_label="synthetic",
            source_ids=[],
            assumption_ids=["synthetic"],
            cost_pence=1234,
            cost_scope="synthetic",
            price_date="2026-01-01",
            states={
                "mature": dict(
                    horizon_years=20,
                    leaf_state="synthetic",
                    crown_center_height_m=1,
                    crown_radii_m=[0.5, 0.5, 0.5],
                    trunk_radius_m=0.1,
                    trunk_height_m=2,
                    attenuation={"mode": "opaque"},
                )
            },
        )
        response = client.post("/api/v1/profiles", json=profile)
        assert response.status_code == 201, response.text
        position = [20, -1, 0] if mode == "miss" else [0, -1, 0]
        layout = dict(
            schema_version="0.1.0",
            layout_id="one",
            revision=1,
            kind="proposed",
            placements=[
                dict(
                    placement_id="p",
                    location_id="l",
                    position_enu_m=position,
                    profile_id="tree",
                    candidate_id=None,
                    pinned=False,
                )
            ],
        )
        response = client.post("/api/v1/layouts", json=layout)
        assert response.status_code == 201, response.text
        inp["proposed_layout_ref"] = {"layout_id": "one", "revision": 1}
        inp["constraints"]["allowed_profile_ids"] = ["tree"]
        scenario = h.create(client, inp)
        req = h.request_for(scenario)
        req["arguments"]["layout_ref"] = inp["proposed_layout_ref"]
        response = client.post("/api/v1/jobs", json=req)
        assert response.status_code == 202, response.text
        job = response.json()
        holder["job_id"] = job["job_id"]
        completed = app.state.run_one()
        if expected is None:
            assert completed.status == ("cancelled" if mode == "cancel_during" else "failed")
            assert completed.run_id is None
            return
        checks = holder.get("resolved_hashes", [])
        delta = {
            k: (checks[0][k], checks[-1][k]) for k in checks[0] if checks[0][k] != checks[-1][k]
        }
        assert completed.status == "completed", (holder.get("failure"), delta)
        response = client.get("/api/v1/results/" + completed.run_id)
        assert response.status_code == 200, response.text
        result = Result.model_validate(response.json())
        if mode == "shadow":
            print("SYNTHETIC_REAL_RESULT", result.model_dump_json())
        assert result.metrics[0].value == expected
        assert result.run_id == completed.run_id and result.source_job_id == job["job_id"]
        assert result.input_fingerprint == job["input_fingerprint"]
        assert result.layouts[0].feasibility == "not_evaluated"
        assert (
            result.provenance.source_hashes
            == resolve(
                ScenarioRef.model_validate(req["scenario_ref"]), operation="evaluate_layout"
            )[1]
        )
        selection = client.get(
            f"/api/v1/scenarios/{scenario['scenario_id']}/selections?revision=1"
        ).json()
        assert selection["evaluation"]["current_job"]["run_id"] == result.run_id
        req["request_id"] = "later"
        later = client.post("/api/v1/jobs", json=req)
        assert later.status_code == 202, later.text
        selection = client.get(
            f"/api/v1/scenarios/{scenario['scenario_id']}/selections?revision=1"
        ).json()
        assert selection["evaluation"]["current_job"] is None
        assert client.get("/api/v1/results/" + result.run_id).json() == response.json()
        assert client.post("/api/v1/jobs/" + later.json()["job_id"] + "/cancel").status_code == 200
        assert app.state.run_one() is None
        changed = client.put(
            "/api/v1/scenarios/" + scenario["scenario_id"], json=inp, headers={"If-Match": '"1"'}
        )
        assert changed.status_code == 200, changed.text
        selection = client.get(
            f"/api/v1/scenarios/{scenario['scenario_id']}/selections?revision=1"
        ).json()
        assert selection["evaluation"]["current_job"] is None
        assert client.get("/api/v1/results/" + result.run_id).json() == response.json()
