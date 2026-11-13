"""Synthetic analytic reference cases for tree_planner.physics.ray.

Every input here is synthetic (axis-aligned spheres, ellipsoids, cylinders and
triangles chosen so the answer is a closed form). Nothing is Sheffield site data
and no expected value is copied from a run: each one is an equation written in
the test, with the derivation beside it.

Geometry is scale-covariant: multiplying every position, radius and height by s
multiplies every path length and hit distance by s. Those cases are parametrised
over s = 1e-6, 1 and 1e6. Argument validation does not depend on scale and runs
once.
"""

from math import inf, nan, sqrt

import pytest

from tree_planner.physics.ray import (
    ellipsoid_path_length,
    ray_triangle_distance,
    trunk_path_length,
)

SCALES = [1e-6, 1.0, 1e6]

# Well-conditioned cases take a handful of IEEE-754 operations on O(1) normalised
# quantities, so the error is a few ulp (about 1e-15 relative). 1e-12 leaves three
# orders of margin and still detects any wrong factor or wrong clip. abs=0.0 is
# explicit because pytest's default abs=1e-12 would swamp a 1e-6 scale expectation.
REL = 1e-12

# Relative offset of the grazing rays from the tangent line.
GRAZE = 1e-6


def close(expected):
    return pytest.approx(expected, rel=REL, abs=0.0)


def flat_triangle(s, up):
    """Right triangle with legs s along east and north, in the plane z = up."""
    return ((0, 0, up), (s, 0, up), (0, s, up))


# --- ellipsoid_path_length(origin, direction, center, radii) -----------------


@pytest.mark.parametrize("scale", SCALES)
def test_sphere_behind_origin_and_reversed_chord(scale):
    s = scale
    # Unit-sphere coordinates: p = (2, 0, 0). Heading +x the closest approach is at
    # t = -2 (behind), the interval is [-3, -1], the forward part is empty: 0.
    assert ellipsoid_path_length((2 * s, 0, 0), (1, 0, 0), (0, 0, 0), (s, s, s)) == 0.0
    # Heading -x the interval is [1, 3] in units of s: a full diameter, 2 s.
    assert ellipsoid_path_length((2 * s, 0, 0), (-1, 0, 0), (0, 0, 0), (s, s, s)) == close(2 * s)


@pytest.mark.parametrize("scale", SCALES)
def test_ellipsoid_axis_chords(scale):
    s = scale
    radii = (2 * s, s, s)
    # Along the long axis the chord is twice the east radius: 2 * (2 s) = 4 s.
    assert ellipsoid_path_length((-4 * s, 0, 0), (1, 0, 0), (0, 0, 0), radii) == close(4 * s)
    # Along a short axis the chord is twice the north radius: 2 * s.
    assert ellipsoid_path_length((0, -3 * s, 0), (0, 1, 0), (0, 0, 0), radii) == close(2 * s)


@pytest.mark.parametrize("scale", SCALES)
def test_ellipsoid_oblique_central_chord(scale):
    s = scale
    # A central chord along unit d meets x^2/a^2 + y^2/b^2 + z^2/c^2 = 1 at
    # t = +-1 / sqrt((dx/a)^2 + (dy/b)^2 + (dz/c)^2), so its length is twice that.
    # d = (0.6, 0.8, 0) is a 3-4-5 unit vector; the origin -5 s d = (-3 s, -4 s, 0)
    # is outside (9/4 + 16 > 1) and the ray passes through the centre.
    expected = 2 * s / sqrt((0.6 / 2) ** 2 + 0.8**2)
    actual = ellipsoid_path_length((-3 * s, -4 * s, 0), (0.6, 0.8, 0), (0, 0, 0), (2 * s, s, s))
    assert actual == close(expected)


@pytest.mark.parametrize("scale", SCALES)
def test_sphere_grazing_just_outside_is_exactly_zero(scale):
    s = scale
    # Offset y = s (1 + 1e-6): the squared normalised miss distance is about
    # 1 + 2e-6, so 1 - y^2 is about -2e-6, ten orders above roundoff (ulp(1) is
    # 2.2e-16 and 2e-6 / 2.2e-16 is 9e9). The ray misses and the early return gives
    # exactly 0.0, with no tolerance involved.
    y = s * (1 + GRAZE)
    assert ellipsoid_path_length((-2 * s, y, 0), (1, 0, 0), (0, 0, 0), (s, s, s)) == 0.0


@pytest.mark.parametrize("scale", SCALES)
def test_sphere_grazing_just_inside_matches_chord(scale):
    s = scale
    # Chord of a sphere of radius s at perpendicular offset y: 2 sqrt(s^2 - y^2).
    y = s * (1 - GRAZE)
    expected = 2 * s * sqrt(1 - (1 - GRAZE) ** 2)
    actual = ellipsoid_path_length((-2 * s, y, 0), (1, 0, 0), (0, 0, 0), (s, s, s))
    assert actual > 0
    # 1 - (y/s)^2 is about 2e-6 and is formed by cancellation from values near 1,
    # so a relative error e in y/s is amplified by (y/s)^2 / (1 - (y/s)^2), about
    # 5e5. A few ulp (2e-16) therefore become about 1e-10 in the chord. 1e-6 is
    # deliberately no tighter: it still pins the chord (2.83e-3 s) to six digits.
    assert actual == pytest.approx(expected, rel=1e-6, abs=0.0)


# --- trunk_path_length(origin, direction, east, north, base_up, radius, height)


@pytest.mark.parametrize("scale", SCALES)
def test_trunk_vertical_rays(scale):
    s = scale
    # Radius s, height 2 s, base at z = 0, axis through the ENU origin.
    # On the axis from below: inside the caps for z in [0, 2 s], length 2 s.
    assert trunk_path_length((0, 0, -s), (0, 0, 1), 0, 0, 0, s, 2 * s) == close(2 * s)
    # Two radii off the axis a vertical ray never enters the lateral surface.
    assert trunk_path_length((2 * s, 0, -s), (0, 0, 1), 0, 0, 0, s, 2 * s) == 0.0
    # From above heading down: enters the top at t = s, leaves the base at t = 3 s.
    assert trunk_path_length((0, 0, 3 * s), (0, 0, -1), 0, 0, 0, s, 2 * s) == close(2 * s)


@pytest.mark.parametrize("scale", SCALES)
def test_trunk_horizontal_rays(scale):
    s = scale
    # At z = 3 s, above the top cap at 2 s, a horizontal ray never enters.
    assert trunk_path_length((-2 * s, 0, 3 * s), (1, 0, 0), 0, 0, 0, s, 2 * s) == 0.0
    # From the axis at mid-height only the forward half of the diameter counts:
    # the lateral interval is [-s, s], clipped at the origin to [0, s].
    assert trunk_path_length((0, 0, s), (1, 0, 0), 0, 0, 0, s, 2 * s) == close(s)


@pytest.mark.parametrize("scale", SCALES)
def test_trunk_diagonal_ray_clipped_by_side_and_top(scale):
    s = scale
    # 45 degree ray in the east-up plane from (-2 s, 0, 0): x(t) = -2 s + t / sqrt 2,
    # z(t) = t / sqrt 2. It crosses the lateral surface (|x| <= s) for
    # t in [sqrt 2 s, 3 sqrt 2 s] and the slab 0 <= z <= 2 s for t in
    # [0, 2 sqrt 2 s]. The intersection is [sqrt 2 s, 2 sqrt 2 s]: length sqrt 2 s.
    r = sqrt(0.5)
    assert trunk_path_length((-2 * s, 0, 0), (r, 0, r), 0, 0, 0, s, 2 * s) == close(sqrt(2) * s)


@pytest.mark.parametrize("scale", SCALES)
def test_trunk_grazing_lateral_surface(scale):
    s = scale
    # Horizontal ray at mid-height. Just outside the radius it misses: exactly 0.
    outside = s * (1 + GRAZE)
    assert trunk_path_length((-2 * s, outside, s), (1, 0, 0), 0, 0, 0, s, 2 * s) == 0.0
    # Just inside, the chord of the circular section is 2 sqrt(s^2 - y^2). Same
    # cancellation as the sphere (amplification about 5e5 on a few ulp), so the
    # same deliberately loose relative tolerance of 1e-6.
    inside = s * (1 - GRAZE)
    expected = 2 * s * sqrt(1 - (1 - GRAZE) ** 2)
    actual = trunk_path_length((-2 * s, inside, s), (1, 0, 0), 0, 0, 0, s, 2 * s)
    assert actual > 0
    assert actual == pytest.approx(expected, rel=1e-6, abs=0.0)


# --- ray_triangle_distance(origin, direction, vertices, *, min_distance, tolerance)


@pytest.mark.parametrize("scale", SCALES)
def test_triangle_hit_is_double_sided(scale):
    s = scale
    tri = flat_triangle(s, s)
    # (s/4, s/4) has barycentric u = v = 1/4, inside. The plane z = s is a distance
    # s from an origin at z = 0 heading up and from an origin at z = 2 s heading down.
    assert ray_triangle_distance((s / 4, s / 4, 0), (0, 0, 1), tri) == close(s)
    assert ray_triangle_distance((s / 4, s / 4, 2 * s), (0, 0, -1), tri) == close(s)


@pytest.mark.parametrize("scale", SCALES)
def test_triangle_behind_origin_or_missed_gives_none(scale):
    s = scale
    tri = flat_triangle(s, s)
    # Origin above the plane heading further up: the plane is at t = -s, behind.
    assert ray_triangle_distance((s / 4, s / 4, 2 * s), (0, 0, 1), tri) is None
    # (s, s) has u = v = 1, so u + v = 2 > 1: the ray pierces the plane outside.
    assert ray_triangle_distance((s, s, 0), (0, 0, 1), tri) is None


@pytest.mark.parametrize("scale", SCALES)
def test_ray_parallel_to_triangle_plane_gives_none(scale):
    s = scale
    tri = flat_triangle(s, s)
    # Direction +x is orthogonal to the plane normal +z, so the determinant
    # e1 . (d x e2) is exactly 0 for these axis-aligned edges: no crossing, whether
    # the ray runs below the plane (z = s/2) or edge-on inside it (z = s).
    assert ray_triangle_distance((-s, s / 4, s / 2), (1, 0, 0), tri) is None
    assert ray_triangle_distance((-s, s / 4, s), (1, 0, 0), tri) is None


@pytest.mark.parametrize("scale", SCALES)
def test_zero_area_triangle_gives_none(scale):
    s = scale
    # Three coincident vertices: both edges are zero vectors.
    point = ((s, s, s), (s, s, s), (s, s, s))
    assert ray_triangle_distance((s, s, 0), (0, 0, 1), point) is None
    # Three collinear vertices: e2 = 2 e1, so e1 . (d x e2) = 0 for every d. The ray
    # is aimed straight at the segment and still must not report an occluder.
    segment = ((0, 0, s), (s, 0, s), (2 * s, 0, s))
    assert ray_triangle_distance((s / 2, 0, 0), (0, 0, 1), segment) is None


@pytest.mark.parametrize("scale", SCALES)
def test_min_distance_excludes_nearer_hit_only(scale):
    s = scale
    near = flat_triangle(s, s)
    far = flat_triangle(s, 3 * s)
    origin = (s / 4, s / 4, 0)
    up = (0, 0, 1)
    # Hits are at s and 3 s. A threshold below the near hit keeps it.
    assert ray_triangle_distance(origin, up, near, min_distance=s / 2) == close(s)
    # A threshold of 2 s lies between them: the near hit is dropped, the far kept.
    assert ray_triangle_distance(origin, up, near, min_distance=2 * s) is None
    assert ray_triangle_distance(origin, up, far, min_distance=2 * s) == close(3 * s)


# --- validation (scale independent) -------------------------------------------

UNIT_SPHERE = ((0, 0, 0), (1, 1, 1))
UNIT_TRUNK = (0, 0, 0, 1, 2)
UNIT_TRIANGLE = flat_triangle(1.0, 1.0)


@pytest.mark.parametrize(
    "direction",
    [
        (1, 1, 0),  # squared norm 2
        (2, 0, 0),  # squared norm 4
        (0, 0, 0),  # squared norm 0
        (1 + 1e-6, 0, 0),  # squared norm 1 + 2e-6, far outside the 1e-9 band
    ],
)
def test_non_unit_direction_rejected(direction):
    origin = (0, 0, -3)
    with pytest.raises(ValueError):
        ellipsoid_path_length(origin, direction, *UNIT_SPHERE)
    with pytest.raises(ValueError):
        trunk_path_length(origin, direction, *UNIT_TRUNK)
    with pytest.raises(ValueError):
        ray_triangle_distance(origin, direction, UNIT_TRIANGLE)


@pytest.mark.parametrize(
    "call",
    [
        lambda: ellipsoid_path_length((nan, 0, 0), (0, 0, 1), (0, 0, 0), (1, 1, 1)),
        lambda: ellipsoid_path_length((0, 0, -3), (inf, 0, 0), (0, 0, 0), (1, 1, 1)),
        lambda: ellipsoid_path_length((0, 0, -3), (0, 0, 1), (0, inf, 0), (1, 1, 1)),
        lambda: ellipsoid_path_length((0, 0, -3), (0, 0, 1), (0, 0, 0), (1, nan, 1)),
        lambda: ellipsoid_path_length((0, 0, -3), (0, 0, 1), (0, 0, 0), (inf, 1, 1)),
        lambda: trunk_path_length((0, nan, -3), (0, 0, 1), 0, 0, 0, 1, 2),
        lambda: trunk_path_length((0, 0, -3), (0, 0, 1), nan, 0, 0, 1, 2),
        lambda: trunk_path_length((0, 0, -3), (0, 0, 1), 0, inf, 0, 1, 2),
        lambda: trunk_path_length((0, 0, -3), (0, 0, 1), 0, 0, -inf, 1, 2),
        lambda: trunk_path_length((0, 0, -3), (0, 0, 1), 0, 0, 0, inf, 2),
        lambda: trunk_path_length((0, 0, -3), (0, 0, 1), 0, 0, 0, 1, nan),
        lambda: ray_triangle_distance((0, 0, inf), (0, 0, 1), UNIT_TRIANGLE),
        lambda: ray_triangle_distance(
            (0, 0, 0), (0, 0, 1), ((0, 0, 1), (1, nan, 1), (0, 1, 1))
        ),
        lambda: ray_triangle_distance((0, 0, 0), (0, 0, 1), UNIT_TRIANGLE, min_distance=nan),
        lambda: ray_triangle_distance((0, 0, 0), (0, 0, 1), UNIT_TRIANGLE, min_distance=inf),
        lambda: ray_triangle_distance((0, 0, 0), (0, 0, 1), UNIT_TRIANGLE, tolerance=nan),
    ],
)
def test_non_finite_input_rejected(call):
    with pytest.raises(ValueError):
        call()


@pytest.mark.parametrize(
    "radii",
    [(0, 1, 1), (1, 0, 1), (1, 1, 0), (-1, 1, 1), (1, 1, -2)],
)
def test_non_positive_ellipsoid_radii_rejected(radii):
    with pytest.raises(ValueError):
        ellipsoid_path_length((0, 0, -3), (0, 0, 1), (0, 0, 0), radii)


@pytest.mark.parametrize(
    ("radius", "height"),
    [(0, 2), (-1, 2), (1, 0), (1, -2)],
)
def test_non_positive_trunk_dimensions_rejected(radius, height):
    with pytest.raises(ValueError):
        trunk_path_length((0, 0, -3), (0, 0, 1), 0, 0, 0, radius, height)


@pytest.mark.parametrize(
    "call",
    [
        # A vector must have exactly three components.
        lambda: ellipsoid_path_length((0, 0), (0, 0, 1), (0, 0, 0), (1, 1, 1)),
        lambda: ellipsoid_path_length((0, 0, -3), (0, 0, 1), (0, 0, 0), (1, 1)),
        lambda: trunk_path_length((0, 0, -3, 0), (0, 0, 1), 0, 0, 0, 1, 2),
        # A triangle must have exactly three vertices of three components.
        lambda: ray_triangle_distance((0, 0, 0), (0, 0, 1), UNIT_TRIANGLE[:2]),
        lambda: ray_triangle_distance((0, 0, 0), (0, 0, 1), ((0, 0, 1), (1, 0), (0, 1, 1))),
        # A cut-off distance or roundoff tolerance cannot be negative.
        lambda: ray_triangle_distance((0, 0, 0), (0, 0, 1), UNIT_TRIANGLE, min_distance=-1.0),
        lambda: ray_triangle_distance((0, 0, 0), (0, 0, 1), UNIT_TRIANGLE, tolerance=-1.0),
    ],
)
def test_malformed_shape_or_negative_threshold_rejected(call):
    with pytest.raises(ValueError):
        call()
