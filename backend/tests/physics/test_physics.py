"""Synthetic analytic inputs; expected values are equations, never runtime fixtures."""

from copy import deepcopy
from datetime import UTC, datetime
from math import pi, sqrt

import pytest

from tree_planner.physics import compute, build_masks, validate_masks, PhysicsStopped
from tree_planner.physics.ray import ellipsoid_path_length, trunk_path_length, ray_triangle_distance
from tree_planner.physics.solar import direction_from_angles, local_to_utc, solar_position


def payload():
    state = {
        "horizon_years": 20,
        "leaf_state": "leaf_on",
        "crown_center_height_m": 3.0,
        "crown_radii_m": [2.0, 2.0, 2.0],
        "trunk_radius_m": 0.1,
        "trunk_height_m": 1.0,
        "attenuation": {"mode": "opaque"},
    }
    return {
        "site": {
            "site_id": "synthetic",
            "scene_revision": 1,
            "semantic_revision": 1,
            "profile_library_revision": 1,
            "candidate_catalogue_revision": 1,
            "candidate_catalogue_fingerprint": "0" * 64,
            "origin": {"latitude_deg": 53.38, "longitude_deg": -1.47, "height_m": 100.0},
            "targets": [{"target_id": "ground", "area_basis": "surface"}],
            "candidate_catalogue": [],
        },
        "scenario": {
            "input": {
                "site_id": "synthetic",
                "scene_revision": 1,
                "semantic_revision": 1,
                "profile_library_revision": 1,
                "candidate_catalogue_revision": 1,
                "candidate_catalogue_fingerprint": "0" * 64,
                "numerics": {
                    "evaluator": "canopy-cpu-reference",
                    "evaluator_version": "takeover-v1",
                    "spatial_spacing_m": 1.0,
                    "ray_offset_m": 1e-6,
                    "intersection_tolerance_m": 1e-10,
                    "feasibility_tolerance": 1e-9,
                    "solar_algorithm": "pvlib-spa-geometric",
                    "solar_version": "0.15.2",
                    "quadrature": "midpoint",
                },
                "evaluation_cases": [
                    {
                        "case_id": "summer",
                        "role": "benefit",
                        "profile_state": "mature",
                        "horizon_years": 20,
                        "target_ids": ["ground"],
                        "target_weights": {"ground": 3.0},
                        "time_bins": [{"midpoint_utc": "2026-06-21T12:00:00Z", "duration_h": 2.0}],
                        "source_ids": [],
                        "assumption_ids": ["synthetic"],
                        "area_basis": "surface",
                        "weather_ref": None,
                    }
                ],
                "objective": {"quantity_kind": "geometric", "primary_case_id": "summer"},
                "constraints": {"budget_pence": 500, "winter_limits": []},
            }
        },
        "profiles": {
            "p": {
                "schema_version": "0.1.0",
                "profile_id": "p",
                "library_revision": 1,
                "species_size_label": "synthetic",
                "source_ids": [],
                "assumption_ids": ["synthetic"],
                "cost_pence": 100,
                "cost_scope": "upfront",
                "price_date": "2026-11-13",
                "states": {"mature": state},
            }
        },
        "scene": {
            "flat_ground_z_m": 0.0,
            "format_version": "canopy-physical-scene/1",
            "spatial_spacing_m": 1.0,
            "samples": [
                {
                    "sample_id": "s0",
                    "position_enu_m": [0.0, 0.0, 0.0],
                    "normal_enu": [0.0, 0.0, 1.0],
                    "area_m2": 2.0,
                    "target_id": "ground",
                    "area_basis": "surface",
                }
            ],
            "triangles": [],
            "existing_trees": [],
        },
    }


def placement(i="one", x=0.0):
    return {
        "placement_id": i,
        "location_id": i,
        "position_enu_m": [x, 0.0, 0.0],
        "profile_id": "p",
        "candidate_id": None,
        "pinned": False,
    }


def overhead(monkeypatch):
    monkeypatch.setattr(
        "tree_planner.physics.evaluator.solar_direction_enu",
        lambda *a, **kw: direction_from_angles(180, 90),
    )


def test_solar_reference_and_dst():
    # NREL TP-560-34302 Appendix A.5 independently published values (rounded 5 decimals).
    p = solar_position(
        39.742476,
        -105.1786,
        datetime(2003, 10, 17, 19, 30, 30, tzinfo=UTC),
        altitude_m=1830.14,
        pressure_pa=82000,
        temperature_c=11,
        delta_t_s=67,
    )
    assert p.azimuth_deg == pytest.approx(194.34024, abs=0.000005)
    assert 90 - p.apparent_elevation_deg == pytest.approx(50.11162, abs=0.000005)
    assert p.geometric_elevation_deg < p.apparent_elevation_deg
    print("NREL residual deg", p.azimuth_deg - 194.34024, 90 - p.apparent_elevation_deg - 50.11162)
    for t in [datetime(2026, 3, 29, 1, 30), datetime(2026, 10, 25, 1, 30)]:
        with pytest.raises(ValueError):
            local_to_utc(t)
    assert local_to_utc(datetime(2026, 7, 1, 12)).hour == 11
    assert direction_from_angles(180, 45).enu == pytest.approx((0, -sqrt(0.5), sqrt(0.5)))


@pytest.mark.parametrize("scale", [1e-6, 1.0, 1e6])
def test_positive_length_geometry(scale):
    s = scale
    assert ellipsoid_path_length((-2 * s, 0, 0), (1, 0, 0), (0, 0, 0), (s, s, s)) == pytest.approx(
        2 * s
    )
    assert ellipsoid_path_length((-2 * s, s, 0), (1, 0, 0), (0, 0, 0), (s, s, s)) == 0
    assert ellipsoid_path_length((0, 0, 0), (1, 0, 0), (0, 0, 0), (s, s, s)) == pytest.approx(s)
    assert ellipsoid_path_length((s, 0, 0), (1, 0, 0), (0, 0, 0), (s, s, s)) == 0
    assert trunk_path_length((-2 * s, 0, s), (1, 0, 0), 0, 0, 0, s, 2 * s) == pytest.approx(2 * s)
    assert trunk_path_length((-2 * s, s, s), (1, 0, 0), 0, 0, 0, s, 2 * s) == 0
    tri = ((0, 0, s), (s, 0, s), (0, s, s))
    assert ray_triangle_distance((s / 4, s / 4, 0), (0, 0, 1), tri) == pytest.approx(s)


def test_overlap_and_baseline_and_weighted(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    a = compute(d, [placement(), placement("two", 0.5)])
    c = a["cases"][0]
    assert c["physical_m2_h"] == 4
    assert c["weighted_m2_h"] == 12
    assert c["baseline_direct_sun_m2_h"] == 4
    assert c["proposal_direct_sun_m2_h"] == 0
    assert compute(d, [])["cases"][0]["physical_m2_h"] == 0
    d["scene"]["existing_trees"] = [placement("old")]
    assert compute(d, [placement()])["cases"][0]["physical_m2_h"] == 0


def test_fixed_crossing_winter_establishment_and_trunk(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    # Offset ray avoids trunk while traversing all three crowns.
    d["scene"]["samples"][0]["position_enu_m"][0] = 0.5
    for key, transmission in [("p", 0.5), ("q", 0.25), ("old", 0.8)]:
        d["profiles"][key] = deepcopy(d["profiles"]["p"])
        d["profiles"][key]["profile_id"] = key
        d["profiles"][key]["states"]["mature"]["attenuation"] = {
            "mode": "fixed_crossing",
            "transmission": transmission,
        }
    old = placement("old")
    old["profile_id"] = "old"
    d["scene"]["existing_trees"] = [old]
    second = placement("two", 0.2)
    second["profile_id"] = "q"
    d["scenario"]["input"]["objective"]["quantity_kind"] = "blocking_equivalent"
    winter = deepcopy(d["scenario"]["input"]["evaluation_cases"][0])
    winter.update(case_id="winter", role="winter_check", profile_state="leaf_off")
    young = deepcopy(winter)
    young.update(
        case_id="young", role="establishment_report", profile_state="young", horizon_years=1
    )
    d["scenario"]["input"]["evaluation_cases"] += [winter, young]
    for profile in d["profiles"].values():
        profile["states"]["leaf_off"] = deepcopy(profile["states"]["mature"])
        profile["states"]["leaf_off"].update(
            leaf_state="leaf_off", attenuation={"mode": "fixed_crossing", "transmission": 1.0}
        )
        profile["states"]["young"] = deepcopy(profile["states"]["mature"])
        profile["states"]["young"].update(horizon_years=1, crown_radii_m=[0.1, 0.1, 0.1])
    c = compute(d, [placement(), second])["cases"]
    assert c[0]["physical_m2_h"] == pytest.approx(2.8)
    assert c[0]["proposal_direct_sun_m2_h"] == pytest.approx(0.4)
    assert c[0]["quantity_kind"] == "blocking_equivalent"
    assert c[1]["physical_m2_h"] == 0
    assert c[2]["physical_m2_h"] == 0
    d["scene"]["existing_trees"] = []
    d["scene"]["samples"][0]["position_enu_m"][0] = 0
    assert compute(d, [placement()])["cases"][1]["physical_m2_h"] == 4  # bare trunk retained


def test_static_thin_triangle_and_origin_exclusion(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    d["scene"]["triangles"] = [
        {"triangle_id": "thin", "vertices_enu_m": [[-1, -1, 1e-9], [1, -1, 1e-9], [0, 1, 1e-9]]}
    ]
    assert compute(d, [placement()])["cases"][0]["physical_m2_h"] == 0
    d["scene"]["samples"][0]["origin_triangle_id"] = "thin"
    with pytest.raises(ValueError, match="origin"):
        compute(d, [placement()])  # cannot exclude another triangle


def test_identity_and_cancel(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    p = placement()
    candidate = {k: v for k, v in p.items() if k not in ("placement_id", "pinned")}
    candidate["candidate_id"] = "c1"
    d["site"]["candidate_catalogue"] = [candidate]
    m = build_masks(d, [candidate])
    validate_masks(d, [candidate], m)
    same = deepcopy(d)
    same["scenario"]["input"]["constraints"]["budget_pence"] = 1
    validate_masks(same, [candidate], m)
    for mutator in [
        lambda x: x["scene"]["samples"][0].update(area_m2=3),
        lambda x: x["profiles"]["p"]["states"]["mature"].update(crown_radii_m=[3, 2, 2]),
        lambda x: x["scenario"]["input"]["evaluation_cases"][0]["time_bins"][0].update(
            duration_h=1
        ),
    ]:
        changed = deepcopy(d)
        mutator(changed)
        with pytest.raises(ValueError, match="identity"):
            validate_masks(changed, [candidate], m)
    with pytest.raises(PhysicsStopped):
        compute(d, [p], stop=lambda: True)


@pytest.mark.parametrize(
    "change",
    [
        lambda d: d["scene"]["samples"][0].update(area_m2=float("nan")),
        lambda d: d["scene"]["samples"].append(deepcopy(d["scene"]["samples"][0])),
        lambda d: d["scene"]["samples"][0].update(area_basis="planimetric"),
        lambda d: d["profiles"]["p"]["states"]["mature"].update(horizon_years=1),
        lambda d: d["scenario"]["input"]["numerics"].update(solar_version="fake"),
        lambda d: d["scenario"]["input"]["evaluation_cases"][0]["time_bins"].append(
            {"midpoint_utc": "2026-06-21T12:00:00Z", "duration_h": 1}
        ),
    ],
)
def test_invalid_inputs(change):
    d = payload()
    change(d)
    with pytest.raises(ValueError):
        compute(d, [placement()])


def test_documented_sixteen_union(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    d["scene"]["samples"] = [
        {
            "sample_id": f"s{i}",
            "position_enu_m": [float(i), 0.0, 0.0],
            "normal_enu": [0.0, 0.0, 1.0],
            "area_m2": 1.0,
            "target_id": "ground",
            "area_basis": "surface",
        }
        for i in range(10)
    ]
    state = d["profiles"]["p"]["states"]["mature"]
    state["crown_radii_m"] = [2.6, 1.0, 1.0]
    d["profiles"]["existing"] = deepcopy(d["profiles"]["p"])
    d["profiles"]["existing"]["profile_id"] = "existing"
    d["profiles"]["existing"]["states"]["mature"]["crown_radii_m"] = [0.6, 1.0, 1.0]
    old = placement("old", 0.5)
    old["profile_id"] = "existing"
    d["scene"]["existing_trees"] = [old]
    a, b = placement("a", 2.5), placement("b", 6.5)
    assert compute(d, [a, b])["cases"][0]["physical_m2_h"] == 16
    assert (
        compute(d, [a])["cases"][0]["physical_m2_h"] + compute(d, [b])["cases"][0]["physical_m2_h"]
        == 20
    )


def test_back_face_night_and_durations(monkeypatch):
    d = payload()
    monkeypatch.setattr(
        "tree_planner.physics.evaluator.solar_direction_enu",
        lambda *a, **kw: direction_from_angles(180, -1),
    )
    assert compute(d, [placement()])["cases"][0]["physical_m2_h"] == 0
    overhead(monkeypatch)
    d["scene"]["samples"][0]["normal_enu"] = [0.0, 0.0, -1.0]
    assert compute(d, [placement()])["cases"][0]["physical_m2_h"] == 0
    d["scene"]["samples"][0]["normal_enu"] = [0.0, 0.0, 1.0]
    d["scenario"]["input"]["evaluation_cases"][0]["time_bins"].append(
        {"midpoint_utc": "2026-06-21T14:00:00Z", "duration_h": 1.0}
    )
    assert compute(d, [placement()])["cases"][0]["physical_m2_h"] == 6


def test_real_solar_repeatability_and_night():
    d = payload()
    a = compute(d, [placement()])
    b = compute(d, [placement()])
    assert a == b and a["cases"][0]["physical_m2_h"] > 0
    d["scenario"]["input"]["evaluation_cases"][0]["time_bins"][0]["midpoint_utc"] = (
        "2026-12-21T00:00:00Z"
    )
    assert compute(d, [placement()])["cases"][0]["baseline_direct_sun_m2_h"] == 0


def test_baked_leaf_state_and_ground_rejected():
    d = payload()
    d["scene"]["baked_vegetation"] = {
        "supported_profile_states": ["leaf_on"],
        "existing_trees_separate": True,
    }
    with pytest.raises(ValueError, match="baked"):
        compute(d, [placement()])
    d = payload()
    d["scene"].pop("flat_ground_z_m")
    with pytest.raises(ValueError, match="ground"):
        compute(d, [placement()])
    d = payload()
    p = placement()
    p["position_enu_m"][2] = 1
    with pytest.raises(ValueError, match="ground"):
        compute(d, [p])


def test_origin_ground_triangle_and_stop_during_loop(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    d["scene"]["triangles"] = [
        {"triangle_id": "ground", "vertices_enu_m": [[-1, -1, 0], [1, -1, 0], [0, 1, 0]]}
    ]
    d["scene"]["samples"][0]["origin_triangle_id"] = "ground"
    assert compute(d, [placement()])["cases"][0]["physical_m2_h"] == 4
    calls = 0

    def stop():
        nonlocal calls
        calls += 1
        return calls > 15

    with pytest.raises(PhysicsStopped):
        compute(d, [placement()], stop)


def test_spatial_midpoint_convergence(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    expected = pi
    d["scenario"]["input"]["evaluation_cases"][0]["time_bins"][0]["duration_h"] = 1.0
    d["profiles"]["p"]["states"]["mature"]["crown_radii_m"] = [1, 1, 1]
    errors = []
    for count in (8, 16, 32, 64):
        spacing = 2 / count
        d["scene"]["spatial_spacing_m"] = spacing
        d["scenario"]["input"]["numerics"]["spatial_spacing_m"] = spacing
        d["scene"]["samples"] = [
            {
                "sample_id": f"{i}-{j}",
                "position_enu_m": [-1 + (i + 0.5) * spacing, -1 + (j + 0.5) * spacing, 0.0],
                "normal_enu": [0.0, 0.0, 1.0],
                "area_m2": spacing * spacing,
                "target_id": "ground",
                "area_basis": "surface",
            }
            for i in range(count)
            for j in range(count)
        ]
        actual = compute(d, [placement()])["cases"][0]["physical_m2_h"]
        errors.append(abs(actual - expected))
        print("disk spatial", count, "actual", actual, "residual", actual - expected)
    # Not a universal monotone convergence claim for discontinuous masks.
    assert errors[-1] < errors[0] and errors[-1] / expected < 0.005


def test_time_and_context_refinement():
    from datetime import timedelta

    d = payload()
    d["profiles"]["p"]["states"]["mature"]["crown_radii_m"] = [1, 1, 1]
    d["scene"]["samples"][0]["position_enu_m"] = [0.0, 1.5, 0.0]
    totals = []
    for count in (4, 16, 64, 256):
        start = datetime(2026, 6, 21, 9, tzinfo=UTC)
        duration = 6 / count
        d["scenario"]["input"]["evaluation_cases"][0]["time_bins"] = [
            {
                "midpoint_utc": (start + timedelta(hours=(i + 0.5) * duration))
                .isoformat()
                .replace("+00:00", "Z"),
                "duration_h": duration,
            }
            for i in range(count)
        ]
        value = compute(d, [placement()])["cases"][0]["physical_m2_h"]
        totals.append(value)
        print("actual solar time bins", count, "m2_h", value)
    assert abs(totals[-1] - totals[-2]) <= 2 * 6 / 64
    # A context occluder creates valid zero additional tree shade; changing it invalidates masks.
    d["scene"]["triangles"] = [
        {"triangle_id": "roof", "vertices_enu_m": [[-100, -100, 1], [100, -100, 1], [0, 100, 1]]}
    ]
    blocked = compute(d, [placement()])["cases"][0]["physical_m2_h"]
    print("context absent/present m2_h", totals[-1], blocked)
    assert blocked == 0


def test_diagnostic_relocation_keeps_candidate_identity(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    c = {
        "candidate_id": "c",
        "location_id": "one",
        "profile_id": "p",
        "position_enu_m": [0.0, 0.0, 0.0],
    }
    d["site"]["candidate_catalogue"] = [c]
    p = placement()
    p.update(candidate_id="c", position_enu_m=[20.0, 0.0, 0.0])
    before = deepcopy(p)
    with pytest.raises(ValueError, match="candidate"):
        compute(d, [p])
    r = compute(d, [p], diagnostic=True)
    assert r["diagnostic"] is True and r["cases"][0]["physical_m2_h"] == 0
    assert r["diagnostics"] == [
        {"placement_id": "one", "candidate_id": "c", "code": "candidate_position_mismatch"}
    ]
    assert p == before
    p["location_id"] = "wrong"
    with pytest.raises(ValueError, match="candidate"):
        compute(d, [p], diagnostic=True)


def test_geometric_objective_cannot_hide_partial_transmission(monkeypatch):
    overhead(monkeypatch)
    d = payload()
    d["profiles"]["p"]["states"]["mature"]["attenuation"] = {
        "mode": "fixed_crossing",
        "transmission": 0.5,
    }
    with pytest.raises(ValueError, match="quantity"):
        compute(d, [placement()])


def test_false_baked_semantics_rejected():
    d = payload()
    d["scene"]["baked_vegetation"] = {}
    with pytest.raises(ValueError, match="baked"):
        compute(d, [placement()])


def test_masks_reproduce_compute_without_reray(monkeypatch):
    from tree_planner.physics import evaluate_masks

    overhead(monkeypatch)
    d = payload()
    candidates = [
        {
            "candidate_id": f"c{i}",
            "location_id": f"l{i}",
            "profile_id": "p",
            "position_enu_m": [x, 0.0, 0.0],
        }
        for i, x in enumerate((0.0, 0.5, 20.0))
    ]
    d["site"]["candidate_catalogue"] = candidates
    masks = build_masks(d, candidates)
    wanted = [
        dict(
            placement(c["candidate_id"]),
            location_id=c["location_id"],
            candidate_id=c["candidate_id"],
            position_enu_m=c["position_enu_m"],
        )
        for c in candidates[:2]
    ]
    expected = compute(d, wanted)

    def forbidden(*a, **kw):
        raise AssertionError("mask aggregation must not call ray evaluator")

    monkeypatch.setattr("tree_planner.physics.evaluator._tree_transmission", forbidden)
    actual = evaluate_masks(d, candidates, masks, ["c0", "c1"])
    assert actual["cases"] == expected["cases"]
    assert evaluate_masks(d, candidates, masks, [])["cases"][0]["physical_m2_h"] == 0
    with pytest.raises(ValueError):
        evaluate_masks(d, candidates, masks, ["missing"])
    changed = deepcopy(d)
    changed["scene"]["samples"][0]["area_m2"] = 3
    with pytest.raises(ValueError, match="identity"):
        evaluate_masks(changed, candidates, masks, ["c0"])
    with pytest.raises(PhysicsStopped):
        evaluate_masks(d, candidates, masks, ["c0"], stop=lambda: True)
