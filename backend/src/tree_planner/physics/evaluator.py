"""Pure deterministic CPU producer for the takeover-v1 working contract.

Uses PR37 ENU/time utilities and PR43 ray/shade formulation with documented
repairs. This module consumes already resolved typed-domain JSON dependencies;
it validates the numerical subset again. It never reads arbitrary assets/network.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from hashlib import sha256
from importlib.metadata import version
import json
from math import fsum, isfinite, prod
from pathlib import Path
from typing import Literal

from pydantic import model_validator

from tree_planner.contracts.base import Array, ContractModel, ID, Positive, Vec3, unique
from tree_planner.contracts.profiles import Placement, TreeProfile
from tree_planner.contracts.scenario import EvaluationCase, Numerics
from .ray import ellipsoid_path_length, point_on_triangle, ray_triangle_distance, trunk_path_length
from .solar import direct_incidence, solar_direction_enu

EVALUATOR = "canopy-cpu-reference"
EVALUATOR_VERSION = "takeover-v1"
SOLAR_ALGORITHM = "pvlib-spa-geometric"
SOLAR_VERSION = "0.15.2"


class PhysicsStopped(RuntimeError):
    """Callback requested stop; no final/partial metric may be published."""


def _check(stop):
    if stop is not None and stop():
        raise PhysicsStopped("physics cancelled or deadline reached")


def _hash(value):
    return sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


class Receiver(ContractModel):
    sample_id: ID
    position_enu_m: Vec3
    normal_enu: Vec3
    area_m2: Positive
    target_id: ID
    area_basis: Literal["surface", "planimetric"]
    origin_triangle_id: ID | None = None

    @model_validator(mode="after")
    def unit_normal(self):
        if abs(sum(x * x for x in self.normal_enu) - 1) > 1e-9:
            raise ValueError("receiver normal must be unit length")
        return self


class Triangle(ContractModel):
    triangle_id: ID
    vertices_enu_m: Array[Vec3]

    @model_validator(mode="after")
    def vertices(self):
        if len(self.vertices_enu_m) != 3:
            raise ValueError("triangle needs three vertices")
        return self


def source_manifest():
    """Content hashes, not asserted git revisions or external source filenames."""
    directory = Path(__file__).parent
    return {
        "implementation": EVALUATOR,
        "version": EVALUATOR_VERSION,
        "files": {
            p.name: sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob("*.py"))
        },
        "dependencies": {name: version(name) for name in ("pvlib", "numpy", "pandas")},
        "solar_elevation": "geometric",
        "solar_delta_t_s": 67.0,
        "self_intersection": "originating_triangle_exclusion; no origin displacement",
        "model": "independent fixed crossing; opaque trunks; axis-aligned ellipsoids",
    }


def _validate(dependencies, placements, stop, diagnostic=False):
    if type(diagnostic) is not bool:
        raise ValueError("diagnostic must be boolean")
    _check(stop)
    # Detach mutable caller payloads, also reject non-JSON/nonfinite payload values.
    _hash(dependencies)
    deps = deepcopy(dependencies)
    site, scenario, scene = deps["site"], deps["scenario"]["input"], deps["scene"]
    for key in (
        "site_id",
        "scene_revision",
        "semantic_revision",
        "profile_library_revision",
        "candidate_catalogue_revision",
        "candidate_catalogue_fingerprint",
    ):
        if site[key] != scenario[key]:
            raise ValueError(f"unresolved site {key}")
    if scene.get("format_version") != "canopy-physical-scene/1":
        raise ValueError("unsupported scene format")
    allowed = {
        "format_version",
        "spatial_spacing_m",
        "samples",
        "triangles",
        "existing_trees",
        "flat_ground_z_m",
        "terrain",
        "regions",
        "baked_vegetation",
    }
    if set(scene) - allowed:
        raise ValueError("unknown physical scene fields")
    if scene.get("terrain") is not None:
        raise ValueError("nonflat terrain unsupported")
    ground = scene.get("flat_ground_z_m")
    if type(ground) not in (int, float) or not isfinite(ground):
        raise ValueError("explicit flat_ground_z_m required")
    numerics = Numerics.model_validate(scenario["numerics"])
    if (
        numerics.evaluator,
        numerics.evaluator_version,
        numerics.solar_algorithm,
        numerics.solar_version,
    ) != (EVALUATOR, EVALUATOR_VERSION, SOLAR_ALGORITHM, SOLAR_VERSION):
        raise ValueError("unsupported evaluator/solar identity")
    if version("pvlib") != SOLAR_VERSION:
        raise ValueError("installed solar version differs")
    if scene.get("spatial_spacing_m") != numerics.spatial_spacing_m:
        raise ValueError("scene spatial spacing mismatch")
    samples = [Receiver.model_validate(v) for v in scene["samples"]]
    triangles = [Triangle.model_validate(v) for v in scene["triangles"]]
    unique([s.sample_id for s in samples], "sample ID")
    unique([s.position_enu_m for s in samples], "receiver position/target overlap")
    unique([t.triangle_id for t in triangles], "triangle ID")
    triangle_map = {t.triangle_id: t for t in triangles}
    for s in samples:
        if s.origin_triangle_id is not None:
            t = triangle_map.get(s.origin_triangle_id)
            if t is None or not point_on_triangle(s.position_enu_m, t.vertices_enu_m):
                raise ValueError("origin triangle does not contain receiver")
    target_map = {t["target_id"]: t for t in site["targets"]}
    for s in samples:
        if s.target_id not in target_map or s.area_basis != target_map[s.target_id]["area_basis"]:
            raise ValueError("receiver target/area basis unresolved")
    cases = [EvaluationCase.model_validate(c) for c in scenario["evaluation_cases"]]
    unique([c.case_id for c in cases], "case ID")
    if not cases:
        raise ValueError("evaluation cases required")
    for c in cases:
        if c.weather_ref is not None:
            raise ValueError("weather-weighted evaluation unsupported")
        for t in c.target_ids:
            selected = [s for s in samples if s.target_id == t]
            if not selected or any(s.area_basis != c.area_basis for s in selected):
                raise ValueError("case target samples/area basis unresolved")
    # Validate complete profile structure using current authority's opaque subset;
    # fixed crossing is validated here until producer-backed public extension lands.
    profiles = deps["profiles"]
    if type(profiles) is not dict:
        raise ValueError("profiles must be mapping by profile_id")
    for pid, p in profiles.items():
        _check(stop)
        if p["profile_id"] != pid or p["library_revision"] != scenario["profile_library_revision"]:
            raise ValueError("profile identity mismatch")
        compatible = deepcopy(p)
        for name, state in p["states"].items():
            att = state["attenuation"]
            if att in ({"mode": "opaque"}, {"mode": "opaque", "transmission": None}):
                pass
            elif (
                set(att) == {"mode", "transmission"}
                and att["mode"] == "fixed_crossing"
                and type(att["transmission"]) in (int, float)
                and isfinite(att["transmission"])
                and 0 <= att["transmission"] <= 1
            ):
                pass
            else:
                raise ValueError("unsupported/invalid attenuation")
            compatible["states"][name]["attenuation"] = {"mode": "opaque"}
        TreeProfile.model_validate(compatible)
    proposed = [Placement.model_validate(p) for p in placements]
    existing = [Placement.model_validate(p) for p in scene["existing_trees"]]
    for group in (proposed, existing):
        unique([p.placement_id for p in group], "placement ID")
        unique([p.location_id for p in group], "placement location")
        unique([p.position_enu_m for p in group], "placement position")
    candidates = {c["candidate_id"]: c for c in site["candidate_catalogue"]}
    for p in proposed + existing:
        if p.profile_id not in profiles:
            raise ValueError("unresolved profile")
        if abs(p.position_enu_m[2] - ground) > numerics.intersection_tolerance_m:
            raise ValueError("placement not attached to flat ground")
        if p.candidate_id is not None:
            cand = candidates.get(p.candidate_id)
            if cand is None or any(
                cand[k] != p.model_dump(mode="json")[k] for k in ("location_id", "profile_id")
            ):
                raise ValueError("candidate placement mismatch")
            if cand["position_enu_m"] != list(p.position_enu_m) and not diagnostic:
                raise ValueError("candidate position mismatch")
        for c in cases:
            state = profiles[p.profile_id]["states"].get(c.profile_state)
            if state is None or state["horizon_years"] != c.horizon_years:
                raise ValueError("profile state/horizon mismatch")
    baked = scene.get("baked_vegetation")
    if baked is not None:
        if type(baked) is not dict or set(baked) != {
            "supported_profile_states",
            "existing_trees_separate",
        }:
            raise ValueError("baked vegetation requires supported state and separation declaration")
        if baked["existing_trees_separate"] is not True or any(
            c.profile_state not in baked["supported_profile_states"] for c in cases
        ):
            raise ValueError("baked vegetation duplicate or unsupported leaf state")
    return deps, scene, site, scenario, samples, triangles, cases, profiles, proposed, existing


def _tree_transmission(origin, direction, placement, state):
    x, y, z = placement.position_enu_m
    if (
        trunk_path_length(
            origin, direction, x, y, z, state["trunk_radius_m"], state["trunk_height_m"]
        )
        > 0
    ):
        return 0.0
    center = (x, y, z + state["crown_center_height_m"])
    if ellipsoid_path_length(origin, direction, center, state["crown_radii_m"]) <= 0:
        return 1.0
    att = state["attenuation"]
    return 0.0 if att["mode"] == "opaque" else att["transmission"]


def _identities(deps, candidates):
    scene = deps["scene"]
    s = deps["scenario"]["input"]
    sampling = {
        "samples": scene["samples"],
        "cases": [
            {k: c[k] for k in ("case_id", "time_bins", "target_ids", "area_basis")}
            for c in s["evaluation_cases"]
        ],
    }
    profile_shapes = {
        pid: {"library_revision": p["library_revision"], "states": p["states"]}
        for pid, p in deps["profiles"].items()
    }
    physics = {
        "scene": scene,
        "origin": deps["site"]["origin"],
        "profiles": profile_shapes,
        "cases": s["evaluation_cases"],
        "numerics": s["numerics"],
        "source": source_manifest(),
    }
    return {
        "sampling_identity": _hash(sampling),
        "physics_identity": _hash(physics),
        "candidate_identity": _hash(candidates),
        "scene_identity": _hash(scene),
    }


def build_masks(dependencies, candidates, stop=None):
    """Flatten sample-major/time-minor masks; B includes day/facing/static/existing.

    Physical weights are represented area*hours. Candidate transmissions multiply;
    target_weights remain separate utility multipliers. Costs/budgets absent from
    geometry identity. Candidate input is resolved Candidate JSON, not a layout.
    """
    ids = [c["candidate_id"] for c in candidates]
    unique(ids, "candidate ID")
    placements = [
        {
            "placement_id": c["candidate_id"],
            "location_id": c["location_id"],
            "profile_id": c["profile_id"],
            "candidate_id": c["candidate_id"],
            "position_enu_m": c["position_enu_m"],
            "pinned": False,
        }
        for c in candidates
    ]
    # Alternative profiles at one location are masks, not a selected layout.
    validated = _validate(dependencies, [], stop)
    deps, scene, site, scenario, samples, triangles, cases, profiles, _, existing = validated
    proposed = []
    for p in placements:
        _check(stop)
        proposed.append(_validate(deps, [p], stop)[8][0])
    identities = _identities(deps, candidates)
    result = {**identities, "cases": []}
    for case in cases:
        _check(stop)
        bins = []
        for b in case.time_bins:
            _check(stop)
            sun = solar_direction_enu(
                site["origin"]["latitude_deg"],
                site["origin"]["longitude_deg"],
                datetime.fromisoformat(b.midpoint_utc.replace("Z", "+00:00")),
                altitude_m=site["origin"]["height_m"],
            )
            bins.append((b, sun))
        relevant = [p for p in proposed + existing]
        partial = any(
            profiles[p.profile_id]["states"][case.profile_state]["attenuation"]["mode"] != "opaque"
            for p in relevant
        )
        out = {
            "case_id": case.case_id,
            "role": case.role,
            "profile_state": case.profile_state,
            "horizon_years": case.horizon_years,
            "quantity_kind": "blocking_equivalent" if partial else "geometric",
            "baseline": [],
            "physical_weights": [],
            "target_ids": [],
            "target_weights": [],
            "candidate_transmissions": {i: [] for i in ids},
        }
        for sample in samples:
            if sample.target_id not in case.target_ids:
                continue
            for bin_, sun in bins:
                _check(stop)
                origin = sample.position_enu_m
                baseline = 1.0 if direct_incidence(sun, sample.normal_enu) > 0 else 0.0
                if baseline:
                    for tri in triangles:
                        _check(stop)
                        if (
                            tri.triangle_id != sample.origin_triangle_id
                            and ray_triangle_distance(origin, sun.enu, tri.vertices_enu_m)
                            is not None
                        ):
                            baseline = 0.0
                            break
                if baseline:
                    for p in existing:
                        _check(stop)
                        baseline *= _tree_transmission(
                            origin, sun.enu, p, profiles[p.profile_id]["states"][case.profile_state]
                        )
                out["baseline"].append(baseline)
                out["physical_weights"].append(sample.area_m2 * bin_.duration_h)
                out["target_ids"].append(sample.target_id)
                out["target_weights"].append(case.target_weights[sample.target_id])
                for p in proposed:
                    _check(stop)
                    out["candidate_transmissions"][p.candidate_id].append(
                        _tree_transmission(
                            origin, sun.enu, p, profiles[p.profile_id]["states"][case.profile_state]
                        )
                        if baseline
                        else 1.0
                    )
        result["cases"].append(out)
    _check(stop)
    result["content_identity"] = _hash(result)
    return result


def validate_masks(dependencies, candidates, masks):
    """Fail closed for wrong dependencies or tampered serialised mask content."""
    _validate(dependencies, [], None)
    expected = _identities(dependencies, candidates)
    if any(masks.get(k) != v for k, v in expected.items()):
        raise ValueError("mask identity mismatch")
    content = {k: v for k, v in masks.items() if k != "content_identity"}
    if masks.get("content_identity") != _hash(content):
        raise ValueError("mask content identity mismatch")


def compute(dependencies, placements, stop=None, *, diagnostic=False):
    validated = _validate(dependencies, placements, stop, diagnostic=diagnostic)
    deps, _, site, scenario, _, _, cases, profiles, proposed, existing = validated
    primary = next(
        (c for c in cases if c.case_id == scenario["objective"]["primary_case_id"]), None
    )
    if primary is None or primary.role != "benefit":
        raise ValueError("unresolved primary benefit case")
    if scenario["objective"]["quantity_kind"] == "geometric" and any(
        profiles[p.profile_id]["states"][primary.profile_state]["attenuation"]["mode"] != "opaque"
        for p in proposed + existing
    ):
        raise ValueError("geometric quantity incompatible with fixed-crossing transmission")
    catalogue = {c["candidate_id"]: c for c in site["candidate_catalogue"]}
    diagnostics = [
        {
            "placement_id": p.placement_id,
            "candidate_id": p.candidate_id,
            "code": "candidate_position_mismatch",
        }
        for p in proposed
        if p.candidate_id is not None
        and catalogue[p.candidate_id]["position_enu_m"] != list(p.position_enu_m)
    ]
    # Internal synthetic catalogue only connects already validated manual placements
    # to reusable masks. Original candidate IDs and dependency identities are retained.
    candidates = []
    inner = deepcopy(deps)
    for n, p in enumerate(proposed):
        candidates.append(
            {
                "candidate_id": f"selected-{n}",
                "location_id": p.location_id,
                "profile_id": p.profile_id,
                "position_enu_m": list(p.position_enu_m),
            }
        )
    inner["site"]["candidate_catalogue"] = candidates
    masks = build_masks(inner, candidates, stop)
    output = {**_identities(deps, [p.model_dump(mode="json") for p in proposed]), "cases": []}
    output.update(diagnostic=diagnostic, diagnostics=diagnostics)
    return _aggregate(masks, output, stop)


def evaluate_masks(dependencies, candidates, masks, selected_candidate_ids, stop=None):
    """Evaluate a registered finite-candidate selection without new solar/ray work.

    Rechecks source/sampling/geometry/candidate/content identity on each use.
    This function does not establish budget/spacing/winter feasibility.
    """
    _check(stop)
    validate_masks(dependencies, candidates, masks)
    unique(selected_candidate_ids, "selected candidate ID")
    catalogue = {c["candidate_id"]: c for c in candidates}
    if any(cid not in catalogue for cid in selected_candidate_ids):
        raise ValueError("unresolved selected candidate")
    placements = [
        {
            "placement_id": cid,
            "candidate_id": cid,
            "location_id": catalogue[cid]["location_id"],
            "profile_id": catalogue[cid]["profile_id"],
            "position_enu_m": catalogue[cid]["position_enu_m"],
            "pinned": False,
        }
        for cid in selected_candidate_ids
    ]
    validated = _validate(dependencies, placements, stop)
    deps, _, _, scenario, _, _, cases, profiles, proposed, existing = validated
    selected = deepcopy(masks)
    for case in selected["cases"]:
        _check(stop)
        case["candidate_transmissions"] = {
            cid: case["candidate_transmissions"][cid] for cid in selected_candidate_ids
        }
        partial = any(
            profiles[p.profile_id]["states"][case["profile_state"]]["attenuation"]["mode"]
            != "opaque"
            for p in proposed + existing
        )
        case["quantity_kind"] = "blocking_equivalent" if partial else "geometric"
        if (
            case["case_id"] == scenario["objective"]["primary_case_id"]
            and scenario["objective"]["quantity_kind"] == "geometric"
            and partial
        ):
            raise ValueError("geometric quantity incompatible with fixed-crossing transmission")
    output = {**_identities(deps, candidates), "cases": [], "diagnostic": False, "diagnostics": []}
    return _aggregate(selected, output, stop)


def _aggregate(masks, output, stop):
    for case in masks["cases"]:
        _check(stop)
        totals = {}
        arrays = list(case["candidate_transmissions"].values())
        for i, (baseline, weight, target, priority) in enumerate(
            zip(
                case["baseline"],
                case["physical_weights"],
                case["target_ids"],
                case["target_weights"],
            )
        ):
            _check(stop)
            proposed_sun = baseline * prod(a[i] for a in arrays)
            delta = (baseline - proposed_sun) * weight
            row = totals.setdefault(
                target, {"physical": [], "weighted": [], "baseline": [], "proposal": []}
            )
            row["physical"].append(delta)
            row["weighted"].append(delta * priority)
            row["baseline"].append(baseline * weight)
            row["proposal"].append(proposed_sun * weight)
        target_rows = [
            {
                "target_id": target,
                "physical_m2_h": fsum(row["physical"]),
                "weighted_m2_h": fsum(row["weighted"]),
                "baseline_direct_sun_m2_h": fsum(row["baseline"]),
                "proposal_direct_sun_m2_h": fsum(row["proposal"]),
            }
            for target, row in totals.items()
        ]
        out = {
            k: case[k]
            for k in ("case_id", "role", "profile_state", "horizon_years", "quantity_kind")
        }
        out["targets"] = target_rows
        for k in (
            "physical_m2_h",
            "weighted_m2_h",
            "baseline_direct_sun_m2_h",
            "proposal_direct_sun_m2_h",
        ):
            out[k] = fsum(row[k] for row in target_rows)
            if not isfinite(out[k]):
                raise ValueError("nonfinite integrated metric")
        output["cases"].append(out)
    _check(stop)
    return output
