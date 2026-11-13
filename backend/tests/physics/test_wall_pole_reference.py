"""SYNTHETIC wall/pole reference cases for the CPU evaluator under a fixed sun.

Every input here is synthetic and hand-built: a made-up wall, a made-up pole and made-up
receivers on a flat plane. Nothing is Sheffield data and nothing is a captured runtime
fixture. Every expected value is a closed-form expression written next to its assertion.

Conventions under test (tree_planner.physics.solar.direction_from_angles):
ENU axes are x = east, y = north, z = up; azimuth is clockwise from true north. A sun at
azimuth 180 and elevation a is the unit vector (0, -cos a, sin a): it stands in the SOUTH
(-y), so a ray from a receiver towards the sun travels south and up, and only an occluder
to the south of the receiver can block it. Shadows therefore fall to the NORTH (+y).

Geometry used:
* Wall: a vertical rectangle in the plane y = 0, |x| <= WALL_HALF_WIDTH_M, 0 <= z <= 8.
  The ray from a ground receiver (x, y, 0) with y > 0 meets the plane y = 0 after slant
  distance y / cos a, at height y * tan a. It is blocked iff that height is below the top,
  i.e. iff y < 8 / tan a. For y < 0 the plane is behind the ray, so the receiver is lit.
* Pole: a closed vertical cylinder, axis through the origin, radius r, height H. On the
  centre line x = 0 the ray is inside the infinite cylinder for slant distances
  [(y - r) / cos a, (y + r) / cos a] and inside the height slab for [0, H / sin a].
  The overlap is non-empty iff -r < y < H / tan a + r. The shadow tip therefore lies at
  H / tan a + r north of the AXIS: the trunk radius is included, because the tip is cast by
  the northern edge of the top rim, not by the axis.

Margins: "just inside" and "just outside" are the analytic boundary scaled by (1 -/+ REL)
with REL = 1e-3. The source decides hits with roundoff-scale tolerances (32 ulp, about
7e-15) and double arithmetic here is good to about 1e-15 relative, so a 1e-3 relative
offset is some twelve orders of magnitude clear of anything floating point could flip.

tan 45 deg = 1 and tan 30 deg = 1 / sqrt(3) are written as hand constants (COT) so that
the expected boundaries do not come from the code under test.
"""

from math import cos, radians, sqrt, tan

import pytest

from tree_planner.physics import build_masks, compute
from tree_planner.physics.ray import trunk_path_length
from tree_planner.physics.solar import direction_from_angles

REL = 1e-3  # relative inside/outside margin; see module docstring

ELEVATIONS = [45, 30]
# cot(a) = 1 / tan(a), by hand: cot 45 = 1, cot 30 = sqrt(3).
COT = {45: 1.0, 30: sqrt(3.0)}
# (0, -cos a, sin a), by hand: cos 45 = sin 45 = sqrt(1/2); cos 30 = sqrt(3)/2, sin 30 = 1/2.
SUN_ENU = {45: (0.0, -sqrt(0.5), sqrt(0.5)), 30: (0.0, -sqrt(3.0) / 2, 0.5)}

TARGET = "synthetic-target"
AREA_M2 = 2.0
DURATION_H = 1.5
# One fully sunlit receiver contributes area * duration = 2.0 * 1.5 = 3.0 m2.h. The
# evaluator's baseline is binary (lit or not), not cosine weighted.
LIT_M2_H = AREA_M2 * DURATION_H

WALL_HEIGHT_M = 8.0
WALL_HALF_WIDTH_M = 10.0
POLE_HEIGHT_M = 6.0
POLE_RADIUS_M = 0.25


def payload():
    """Smallest synthetic dependency payload accepted by evaluator._validate.

    Receivers, triangles, trees and profiles are added by each test.
    """
    # _validate requires these six keys to be equal in the site and the scenario input.
    identity = {
        "site_id": "synthetic",
        "scene_revision": 1,
        "semantic_revision": 1,
        "profile_library_revision": 1,
        "candidate_catalogue_revision": 1,
        "candidate_catalogue_fingerprint": "0" * 64,
    }
    return {
        "site": {
            **identity,
            # Only forwarded to solar_direction_enu (replaced by fix_sun) and hashed.
            "origin": {"latitude_deg": 0.0, "longitude_deg": 0.0, "height_m": 0.0},
            # Each receiver must resolve to a target with the same area basis.
            "targets": [{"target_id": TARGET, "area_basis": "surface"}],
            "candidate_catalogue": [],
        },
        "scenario": {
            "input": {
                **identity,
                # Must name exactly this evaluator/solar identity; spacing must equal the
                # scene's. The tolerances are required by the contract model.
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
                # One benefit case with one time bin: one mask entry per receiver. The
                # timestamp is irrelevant because the sun is fixed by fix_sun.
                "evaluation_cases": [
                    {
                        "case_id": "fixed-sun",
                        "role": "benefit",
                        "profile_state": "mature",
                        "horizon_years": 20,
                        "target_ids": [TARGET],
                        "target_weights": {TARGET: 1.0},
                        "time_bins": [
                            {"midpoint_utc": "2026-06-21T12:00:00Z", "duration_h": DURATION_H}
                        ],
                        "source_ids": [],
                        "assumption_ids": ["synthetic"],
                        "area_basis": "surface",
                        "weather_ref": None,
                    }
                ],
                # compute() needs a primary benefit case and a quantity kind.
                "objective": {"quantity_kind": "geometric", "primary_case_id": "fixed-sun"},
            }
        },
        # Mapping by profile_id; empty unless a test plants the pole.
        "profiles": {},
        "scene": {
            "format_version": "canopy-physical-scene/1",
            "flat_ground_z_m": 0.0,
            "spatial_spacing_m": 1.0,
            "samples": [],
            "triangles": [],
            "existing_trees": [],
        },
    }


def receiver(sample_id, position_enu_m, normal_enu=(0.0, 0.0, 1.0)):
    """Synthetic receiver; the default normal is an upward-facing ground sample."""
    return {
        "sample_id": sample_id,
        "position_enu_m": list(position_enu_m),
        "normal_enu": list(normal_enu),
        "area_m2": AREA_M2,
        "target_id": TARGET,
        "area_basis": "surface",
    }


def wall_triangles():
    """Synthetic wall in the plane y = 0 as two triangles sharing the rising diagonal."""
    w, h = WALL_HALF_WIDTH_M, WALL_HEIGHT_M
    return [
        {
            "triangle_id": "wall-lower",
            "vertices_enu_m": [[-w, 0.0, 0.0], [w, 0.0, 0.0], [w, 0.0, h]],
        },
        {
            "triangle_id": "wall-upper",
            "vertices_enu_m": [[-w, 0.0, 0.0], [w, 0.0, h], [-w, 0.0, h]],
        },
    ]


def pole_profile():
    """Synthetic bare pole expressed as a tree profile.

    The contract requires a crown with positive radii, so the crown is a sphere of radius
    r / 2 centred on the axis at mid height. It lies strictly inside the trunk cylinder
    (r / 2 < r and H / 2 +/- r / 2 within [0, H]); every ray through it also has positive
    length inside the trunk, so the crown adds no shadow of its own and the profile casts
    exactly the cylinder's shadow.
    """
    return {
        "schema_version": "0.1.0",
        "profile_id": "pole",
        "library_revision": 1,
        "species_size_label": "synthetic-pole",
        "source_ids": [],
        "assumption_ids": ["synthetic"],
        "cost_pence": 0,
        "cost_scope": "upfront",
        "price_date": "2026-11-13",
        "states": {
            "mature": {
                "horizon_years": 20,
                "leaf_state": "leaf_on",
                "crown_center_height_m": POLE_HEIGHT_M / 2,
                "crown_radii_m": [POLE_RADIUS_M / 2, POLE_RADIUS_M / 2, POLE_RADIUS_M / 2],
                "trunk_radius_m": POLE_RADIUS_M,
                "trunk_height_m": POLE_HEIGHT_M,
                "attenuation": {"mode": "opaque"},
            }
        },
    }


def pole_placement():
    """The synthetic pole standing on the flat ground with its axis through the origin."""
    return {
        "placement_id": "pole",
        "location_id": "pole",
        "position_enu_m": [0.0, 0.0, 0.0],
        "profile_id": "pole",
        "candidate_id": None,
        "pinned": False,
    }


def fix_sun(monkeypatch, azimuth_deg, elevation_deg):
    monkeypatch.setattr(
        "tree_planner.physics.evaluator.solar_direction_enu",
        lambda *a, **kw: direction_from_angles(azimuth_deg, elevation_deg),
    )


def baseline_mask(dependencies):
    """Per-receiver baseline (1.0 lit, 0.0 not) from build_masks with no candidates.

    The mask is sample-major/time-minor and the payload has a single time bin, so there is
    exactly one entry per receiver, in scene order. The baseline includes facing, static
    triangles and existing trees.
    """
    case = build_masks(dependencies, [])["cases"][0]
    ids = [s["sample_id"] for s in dependencies["scene"]["samples"]]
    assert len(case["baseline"]) == len(ids)
    return dict(zip(ids, case["baseline"]))


@pytest.mark.parametrize("elevation_deg", ELEVATIONS)
def test_due_south_sun_vector_points_south_and_up(elevation_deg):
    sun = direction_from_angles(180, elevation_deg)
    assert sun.above_horizon
    # (cos a sin 180, cos a cos 180, sin a) = (0, -cos a, sin a); sin(pi) is about 1e-16 in
    # floating point, hence the absolute tolerance on the east component.
    assert sun.enu == pytest.approx(SUN_ENU[elevation_deg], abs=1e-12)
    _, north, up = sun.enu
    assert north < 0 < up  # the sun is to the south (-y) and above the horizon
    assert up / -north == pytest.approx(1 / COT[elevation_deg], rel=1e-12)  # tan a
    # The hand constants agree with the library tangent (pure arithmetic cross-check).
    assert 1 / tan(radians(elevation_deg)) == pytest.approx(COT[elevation_deg], rel=1e-12)


@pytest.mark.parametrize("elevation_deg", ELEVATIONS)
def test_wall_shadow_reaches_height_over_tan_elevation_to_the_north(monkeypatch, elevation_deg):
    fix_sun(monkeypatch, 180, elevation_deg)
    # Shadow length 8 / tan a: 8 m at 45 deg, 8 * sqrt(3) = 13.856... m at 30 deg.
    length = WALL_HEIGHT_M * COT[elevation_deg]
    d = payload()
    d["scene"]["triangles"] = wall_triangles()
    d["scene"]["samples"] = [
        # Ray meets the wall plane at height y * tan a = 8 * (1 - REL) = 7.992 < 8: blocked.
        # (At x = 0 the shared diagonal is at height 4, so this is well inside one triangle.)
        receiver("north-inside", [0.0, length * (1 - REL), 0.0]),
        # Ray crosses the wall plane at height 8 * (1 + REL) = 8.008 > 8: passes over the top.
        receiver("north-outside", [0.0, length * (1 + REL), 0.0]),
        # South of the wall (-y): the ray heads further south, the wall is behind it.
        receiver("south", [0.0, -length * (1 - REL), 0.0]),
    ]
    # ENU sign: with the sun due south the shadow is on the +y (north) side only.
    assert baseline_mask(d) == {"north-inside": 0.0, "north-outside": 1.0, "south": 1.0}
    case = compute(d, [])["cases"][0]
    # Two of three receivers are lit; no trees are proposed, so nothing is gained.
    assert case["baseline_direct_sun_m2_h"] == 2 * LIT_M2_H
    assert case["proposal_direct_sun_m2_h"] == 2 * LIT_M2_H
    assert case["physical_m2_h"] == 0


def test_wall_shadow_has_no_east_west_spread_for_due_south_sun(monkeypatch):
    fix_sun(monkeypatch, 180, 45)
    # Half-way into the 8 m shadow (y = 4, tan 45 = 1) the ray crosses the wall plane at
    # height 4. A due-south sun has no east component, so the crossing keeps the receiver's
    # x: it is on the wall iff |x| < WALL_HALF_WIDTH_M.
    depth = WALL_HEIGHT_M * COT[45] / 2
    inside, outside = WALL_HALF_WIDTH_M * (1 - REL), WALL_HALF_WIDTH_M * (1 + REL)
    d = payload()
    d["scene"]["triangles"] = wall_triangles()
    d["scene"]["samples"] = [
        receiver("east-inside", [inside, depth, 0.0]),
        receiver("east-outside", [outside, depth, 0.0]),
        receiver("west-inside", [-inside, depth, 0.0]),
        receiver("west-outside", [-outside, depth, 0.0]),
    ]
    assert baseline_mask(d) == {
        "east-inside": 0.0,
        "east-outside": 1.0,
        "west-inside": 0.0,
        "west-outside": 1.0,
    }


@pytest.mark.parametrize("elevation_deg", ELEVATIONS)
def test_trunk_path_length_shadow_tip_includes_trunk_radius(elevation_deg):
    sun = direction_from_angles(180, elevation_deg).enu
    cos_a = cos(radians(elevation_deg))
    r, h = POLE_RADIUS_M, POLE_HEIGHT_M
    axis_tip = h * COT[elevation_deg]  # where the top of the AXIS casts its shadow
    tip = axis_tip + r  # true tip: cast by the northern edge of the top rim

    def path(north_m, east_m=0.0):
        # Ground receiver at (east, north, 0); pole axis at (0, 0), base on the ground.
        return trunk_path_length((east_m, north_m, 0.0), sun, 0.0, 0.0, 0.0, r, h)

    inside, outside = tip * (1 - REL), tip * (1 + REL)
    # The margin (REL * tip) is much smaller than r, so "just inside the tip" is already
    # beyond the axis-only tip: a shadow that ignored the radius would call it lit.
    assert inside > axis_tip
    # For H / tan a - r <= y < H / tan a + r the ray enters through the north side at slant
    # distance (y - r) / cos a and leaves through the top at H / sin a, so the interior
    # length is H / sin a - (y - r) / cos a = (H / tan a + r - y) / cos a.
    assert path(inside) > 0
    assert path(inside) == pytest.approx((tip - inside) / cos_a, rel=1e-9)
    assert path(axis_tip + r / 2) == pytest.approx((r / 2) / cos_a, rel=1e-9)
    # Beyond the tip the ray passes over the northern rim: no interior length at all.
    assert path(outside) == 0
    # ENU sign: south of the pole (-y) the trunk is behind the ray.
    assert path(-inside) == 0
    assert path(-2 * r) == 0
    # Mid shadow (r <= y <= H / tan a - r): the ray crosses the full diameter below the
    # top, horizontal chord 2r, slant length 2r / cos a.
    assert path(axis_tip / 2) == pytest.approx(2 * r / cos_a, rel=1e-9)
    # Off the centre line the horizontal chord is 2 * sqrt(r^2 - x^2); none for |x| > r.
    east_in, east_out = r * (1 - REL), r * (1 + REL)
    chord = 2 * sqrt(r * r - east_in * east_in)
    assert path(axis_tip / 2, east_in) == pytest.approx(chord / cos_a, rel=1e-9)
    assert path(axis_tip / 2, -east_in) == pytest.approx(chord / cos_a, rel=1e-9)
    assert path(axis_tip / 2, east_out) == 0
    assert path(axis_tip / 2, -east_out) == 0


@pytest.mark.parametrize("elevation_deg", ELEVATIONS)
def test_pole_shades_ground_to_the_north_up_to_tip_plus_radius(monkeypatch, elevation_deg):
    fix_sun(monkeypatch, 180, elevation_deg)
    axis_tip = POLE_HEIGHT_M * COT[elevation_deg]
    # Shadow tip H / tan a + r: 6.25 m at 45 deg, 6 * sqrt(3) + 0.25 = 10.642... m at 30 deg.
    # It includes the trunk radius (see the module docstring).
    tip = axis_tip + POLE_RADIUS_M
    assert tip * (1 - REL) > axis_tip
    d = payload()
    d["profiles"] = {"pole": pole_profile()}
    d["scene"]["samples"] = [
        receiver("north-inside", [0.0, tip * (1 - REL), 0.0]),
        # Between the axis-only tip and the true tip: shaded only because of the radius.
        receiver("north-rim-band", [0.0, axis_tip + POLE_RADIUS_M / 2, 0.0]),
        receiver("north-outside", [0.0, tip * (1 + REL), 0.0]),
        receiver("south", [0.0, -tip * (1 - REL), 0.0]),
    ]
    # Pole as an existing tree: its shade is part of the baseline.
    d["scene"]["existing_trees"] = [pole_placement()]
    assert baseline_mask(d) == {
        "north-inside": 0.0,
        "north-rim-band": 0.0,
        "north-outside": 1.0,
        "south": 1.0,
    }
    # Pole as a proposed tree: all four receivers are lit in the baseline, the proposal
    # shades the two northern in-shadow ones, and the gain is their area * hours.
    d["scene"]["existing_trees"] = []
    case = compute(d, [pole_placement()])["cases"][0]
    assert case["baseline_direct_sun_m2_h"] == 4 * LIT_M2_H
    assert case["physical_m2_h"] == 2 * LIT_M2_H
    assert case["proposal_direct_sun_m2_h"] == 2 * LIT_M2_H


# Azimuth is clockwise from north, so the sun at 0/90/180/270 stands north/east/south/west
# and the shadow falls on the opposite side: south/west/north/east.
SHADOW_SIDE = {0: "south", 90: "west", 180: "north", 270: "east"}


@pytest.mark.parametrize("azimuth_deg", sorted(SHADOW_SIDE))
def test_pole_shadow_falls_on_the_side_opposite_the_sun(monkeypatch, azimuth_deg):
    fix_sun(monkeypatch, azimuth_deg, 45)
    # Mid shadow at 45 deg: H / (2 tan a) = 3 m from the axis. On the shadow side the ray
    # passes through the axis at height 3 (inside the 6 m pole). On the other three sides
    # the ray either heads away from the pole or passes 3 m (= 12 radii) beside it.
    distance = POLE_HEIGHT_M * COT[45] / 2
    d = payload()
    d["profiles"] = {"pole": pole_profile()}
    d["scene"]["existing_trees"] = [pole_placement()]
    d["scene"]["samples"] = [
        receiver("north", [0.0, distance, 0.0]),  # +y
        receiver("east", [distance, 0.0, 0.0]),  # +x
        receiver("south", [0.0, -distance, 0.0]),  # -y
        receiver("west", [-distance, 0.0, 0.0]),  # -x
    ]
    expected = {
        side: 0.0 if side == SHADOW_SIDE[azimuth_deg] else 1.0
        for side in ("north", "east", "south", "west")
    }
    assert baseline_mask(d) == expected


@pytest.mark.parametrize("elevation_deg", ELEVATIONS)
def test_vertical_receiver_is_lit_only_when_it_faces_the_sun(monkeypatch, elevation_deg):
    fix_sun(monkeypatch, 180, elevation_deg)
    d = payload()
    d["scene"]["samples"] = [
        # Outward normal -y (faces south): sun . normal = cos a > 0, so it is lit.
        receiver("south-facing", [0.0, 0.0, 1.5], normal_enu=[0.0, -1.0, 0.0]),
        # Outward normal +y (faces north): sun . normal = -cos a < 0, a back face reads 0.
        receiver("north-facing", [0.0, 1.0, 1.5], normal_enu=[0.0, 1.0, 0.0]),
    ]
    assert baseline_mask(d) == {"south-facing": 1.0, "north-facing": 0.0}
    case = compute(d, [])["cases"][0]
    # Only the south-facing receiver contributes, as full area * hours (binary baseline).
    assert case["baseline_direct_sun_m2_h"] == LIT_M2_H
    assert case["proposal_direct_sun_m2_h"] == LIT_M2_H
    assert case["physical_m2_h"] == 0


@pytest.mark.parametrize(
    "normal_enu",
    [
        [0.0, -2.0, 0.0],  # squared length 4
        [0.0, -0.5, 0.0],  # squared length 0.25
        [0.0, -1.0, 1.0],  # squared length 2
        [0.0, 0.0, 0.0],  # squared length 0
    ],
)
def test_non_unit_receiver_normal_is_rejected(monkeypatch, normal_enu):
    fix_sun(monkeypatch, 180, 45)
    d = payload()
    d["scene"]["samples"] = [receiver("bad-normal", [0.0, 0.0, 1.5], normal_enu=normal_enu)]
    # Receiver requires |sum(n^2) - 1| <= 1e-9; these are off by 0.75 or more.
    with pytest.raises(ValueError, match="unit"):
        compute(d, [])
    with pytest.raises(ValueError, match="unit"):
        build_masks(d, [])
