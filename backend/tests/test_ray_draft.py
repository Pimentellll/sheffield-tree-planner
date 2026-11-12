"""Analytic synthetic ray cases for provisional STP-009 geometry."""

import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tree_planner.physics.ray import (
    ray_ellipsoid_distance,
    ray_triangle_distance,
    ray_vertical_trunk_distance,
)


class RayDraftTests(unittest.TestCase):
    def test_ellipsoid_hit_miss_tangent_inside(self):
        center = (0.0, 0.0, 0.0)
        radii = (1.0, 1.0, 1.0)
        east = (1.0, 0.0, 0.0)
        self.assertAlmostEqual(
            ray_ellipsoid_distance((-2, 0, 0), east, center, radii), 1
        )
        self.assertIsNone(ray_ellipsoid_distance((-2, 1.001, 0), east, center, radii))
        self.assertAlmostEqual(
            ray_ellipsoid_distance((-2, 1, 0), east, center, radii), 2
        )
        self.assertAlmostEqual(
            ray_ellipsoid_distance((0, 0, 0), east, center, radii), 1
        )

    def test_ellipsoid_axis_radii_and_offset(self):
        self.assertAlmostEqual(
            ray_ellipsoid_distance((-4, 0, 0), (1, 0, 0), (0, 0, 0), (2, 1, 1)), 2
        )
        self.assertIsNone(
            ray_ellipsoid_distance(
                (-1 - 1e-10, 0, 0), (1, 0, 0), (0, 0, 0), (1, 1, 1), min_distance=3
            )
        )
        with self.assertRaises(ValueError):
            ray_ellipsoid_distance((0, 0, 0), (1, 0, 0), (0, 0, 0), (1, 0, 1))

    def test_near_grazing_hit_and_miss(self):
        y = 1 - 1e-6
        expected = 2 - math.sqrt(1 - y * y)
        observed = ray_ellipsoid_distance((-2, y, 0), (1, 0, 0), (0, 0, 0), (1, 1, 1))
        self.assertAlmostEqual(observed, expected, delta=1e-12)
        self.assertIsNone(
            ray_ellipsoid_distance((-2, 1 + 1e-6, 0), (1, 0, 0), (0, 0, 0), (1, 1, 1))
        )

    def test_vertical_trunk_side_tangent_and_caps(self):
        trunk = (0.0, 0.0, 0.0, 1.0, 2.0)
        self.assertAlmostEqual(
            ray_vertical_trunk_distance((-2, 0, 1), (1, 0, 0), *trunk), 1
        )
        self.assertAlmostEqual(
            ray_vertical_trunk_distance((-2, 1, 1), (1, 0, 0), *trunk), 2
        )
        self.assertAlmostEqual(
            ray_vertical_trunk_distance((0, 0, 3), (0, 0, -1), *trunk), 1
        )
        self.assertAlmostEqual(
            ray_vertical_trunk_distance((0, 0, 1), (0, 0, 1), *trunk), 1
        )
        self.assertIsNone(ray_vertical_trunk_distance((-2, 0, 3), (1, 0, 0), *trunk))
        with self.assertRaises(ValueError):
            ray_vertical_trunk_distance((0, 0, 0), (0, 0, 1), 0, 0, 0, 0, 2)

    def test_static_triangle_two_sides_miss_degenerate_and_near_zero(self):
        triangle = ((-1.0, -1.0, 0.0), (1.0, -1.0, 0.0), (0.0, 1.0, 0.0))
        self.assertAlmostEqual(
            ray_triangle_distance((0, 0, 1), (0, 0, -1), triangle), 1
        )
        self.assertAlmostEqual(
            ray_triangle_distance((0, 0, -1), (0, 0, 1), triangle), 1
        )
        self.assertIsNone(ray_triangle_distance((2, 0, 1), (0, 0, -1), triangle))
        self.assertIsNone(ray_triangle_distance((0, 0, 1e-12), (0, 0, -1), triangle))
        self.assertIsNone(
            ray_triangle_distance(
                (0, 0, 1), (0, 0, -1), ((0, 0, 0), (1, 0, 0), (2, 0, 0))
            )
        )

    def test_reject_nonfinite_nonunit_and_negative_offset(self):
        with self.assertRaises(ValueError):
            ray_ellipsoid_distance((0, 0, 0), (2, 0, 0), (0, 0, 0), (1, 1, 1))
        with self.assertRaises(ValueError):
            ray_triangle_distance(
                (math.nan, 0, 1), (0, 0, -1), ((0, 0, 0), (1, 0, 0), (0, 1, 0))
            )
        with self.assertRaises(ValueError):
            ray_ellipsoid_distance(
                (0, 0, 0), (1, 0, 0), (0, 0, 0), (1, 1, 1), min_distance=-1
            )


if __name__ == "__main__":
    unittest.main()
