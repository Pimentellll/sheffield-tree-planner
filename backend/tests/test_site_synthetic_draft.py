"""Labelled synthetic STP-006 transform and raster failure checks."""

import math
import sys
import unittest
from pathlib import Path

from pyproj import Geod, Transformer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tree_planner.site.synthetic_import import (
    BngEnuTransform,
    SyntheticRaster,
    import_synthetic_pair,
)


class SyntheticSitePilotTests(unittest.TestCase):
    def setUp(self):
        # Synthetic coordinates near Sheffield; not a surveyed Sheffield site.
        self.transform = BngEnuTransform(430000.0, 387000.0, 100.0)
        self.bng_to_geo = Transformer.from_crs(27700, 4326, always_xy=True)

    def test_origin_roundtrip_and_true_north(self):
        self.assertTrue(
            all(abs(v) < 1e-5 for v in self.transform.to_enu(430000, 387000, 100))
        )
        source = self.transform.from_enu(0, 10, 0)
        self.assertAlmostEqual(self.transform.to_enu(*source)[1], 10, delta=1e-3)
        lon1, lat1 = self.bng_to_geo.transform(430000, 387000)
        lon2, lat2 = self.bng_to_geo.transform(source[0], source[1])
        azimuth, _, distance = Geod(ellps="WGS84").inv(lon1, lat1, lon2, lat2)
        self.assertAlmostEqual(azimuth, 0, delta=0.01)
        self.assertAlmostEqual(distance, 10, delta=0.01)
        # The BNG grid's north vector is measurably different from true north.
        grid_north = self.transform.to_enu(430000, 387010, 100)
        self.assertGreater(abs(grid_north[0]), 0.001)

    def test_metre_and_height_roundtrip(self):
        for enu in ((1, 0, 0), (0, 1, 0), (0, 0, 1), (25, -18, 3)):
            self.assertTrue(
                all(
                    math.isclose(a, b, abs_tol=1e-3)
                    for a, b in zip(
                        enu, self.transform.to_enu(*self.transform.from_enu(*enu))
                    )
                )
            )

    def test_reject_unconverted_vertical_datum(self):
        with self.assertRaises(ValueError):
            BngEnuTransform(430000, 387000, 100, "ODN")
        with self.assertRaises(ValueError):
            SyntheticRaster(((100.0,),), 430000, 387000, 1, "unknown")

    def test_aligned_raster_mesh_and_semantic_unknown(self):
        dtm = SyntheticRaster(
            ((100.0, 100.0, 100.0), (100.0, None, 100.0), (100.0, 100.0, 100.0)),
            430000,
            387000,
            1,
        )
        dsm = SyntheticRaster(
            ((100.0, 104.0, 100.0), (100.0, None, 102.0), (100.0, 100.0, 100.0)),
            430000,
            387000,
            1,
        )
        scene = import_synthetic_pair(dtm, dsm, self.transform)
        self.assertEqual(len(scene.terrain_vertices_enu_m), 9)
        self.assertEqual(len(scene.terrain_triangles), 2)
        self.assertEqual(scene.elevated_cells, ((0, 1, "unknown"), (1, 2, "unknown")))
        self.assertEqual(scene.missing_cells, ((1, 1),))
        self.assertIn("context", scene.context_warning)
        mask = (
            ("unknown", "vegetation", "unknown"),
            ("unknown", "unknown", "building"),
            ("unknown", "unknown", "unknown"),
        )
        classified = import_synthetic_pair(dtm, dsm, self.transform, semantic_mask=mask)
        self.assertEqual(
            classified.elevated_cells, ((0, 1, "vegetation"), (1, 2, "building"))
        )

    def test_alignment_and_invalid_surface_rejected(self):
        dtm = SyntheticRaster(((100.0, 100.0), (100.0, 100.0)), 430000, 387000, 1)
        shifted = SyntheticRaster(((100.0, 100.0), (100.0, 100.0)), 430001, 387000, 1)
        with self.assertRaises(ValueError):
            import_synthetic_pair(dtm, shifted, self.transform)
        below = SyntheticRaster(((100.0, 99.0), (100.0, 100.0)), 430000, 387000, 1)
        with self.assertRaises(ValueError):
            import_synthetic_pair(dtm, below, self.transform)


if __name__ == "__main__":
    unittest.main()
