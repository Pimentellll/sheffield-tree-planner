"""Labelled synthetic STP-006 transform and raster failure checks."""

import math
import sys
import unittest
from pathlib import Path

from pyproj import Geod, Transformer

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tree_planner.site.synthetic_import import (
    ANALYSIS_TO_VIEWER_DRAFT,
    BngEnuTransform,
    SyntheticRaster,
    enu_to_provisional_viewer,
    import_synthetic_pair,
    provisional_viewer_to_enu,
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
        with self.assertRaises(ValueError):
            BngEnuTransform(430000, 387000, 100, site_kind="real_site")
        with self.assertRaises(ValueError):
            SyntheticRaster(((100.0,),), 430000, 387000, 1, site_kind="real_site")

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

    def test_horizontal_operation_is_reported(self):
        description, stated_accuracy_m = self.transform.selected_horizontal_operation()
        self.assertIn("British National Grid", description)
        self.assertTrue(math.isfinite(stated_accuracy_m))

    def test_provisional_viewer_known_points_and_metres(self):
        self.assertEqual(
            ANALYSIS_TO_VIEWER_DRAFT, (1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1)
        )
        self.assertEqual(enu_to_provisional_viewer((1, 2, 3)), (1, 3, -2))
        self.assertEqual(enu_to_provisional_viewer((0, 1, 0)), (0, 0, -1))
        for point in ((0, 0, 0), (1, 0, 0), (0, 1, 0), (0, 0, 1), (12.5, -7, 3)):
            viewer = enu_to_provisional_viewer(point)
            self.assertEqual(provisional_viewer_to_enu(viewer), point)
            self.assertAlmostEqual(
                math.dist(viewer, (0, 0, 0)), math.dist(point, (0, 0, 0))
            )


if __name__ == "__main__":
    unittest.main()
