"""Analytic synthetic evaluator cases; no successful runtime fixture is authored."""

import math
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tree_planner.physics.shade_reference import (
    DraftSolarBin,
    OpaqueEllipsoid,
    OpaqueTrunk,
    ProposedTree,
    ReceiverSample,
    StaticTriangle,
    evaluate_one_tree_synthetic,
)

SUN = (0.0, -math.sqrt(0.5), math.sqrt(0.5))
MID = datetime(2026, 6, 21, 12, tzinfo=UTC)
SAMPLE = ReceiverSample((0, 0, 0), (0, 0, 1), 2, "target")
TREE = ProposedTree(
    OpaqueEllipsoid((0, -1, 1), (0.5, 0.5, 0.5)),
    OpaqueTrunk(0, -1, 0, 0.1, 2),
)


class OneTreeSyntheticTests(unittest.TestCase):
    def test_one_tree_gain_and_unaffected_target(self):
        samples = (SAMPLE, ReceiverSample((10, 0, 0), (0, 0, 1), 1, "target"))
        result = evaluate_one_tree_synthetic(
            samples, (DraftSolarBin(MID, 3, SUN, True),), (), TREE
        )
        self.assertEqual(result.baseline_direct_sun_m2_h, 9)
        self.assertEqual(result.proposal_direct_sun_m2_h, 3)
        self.assertEqual(result.additional_useful_shade_m2_h, 6)
        self.assertEqual((result.sample_count, result.bin_count), (2, 1))

    def test_existing_shade_has_zero_additional_gain(self):
        existing = (OpaqueEllipsoid((0, -1, 1), (0.5, 0.5, 0.5)),)
        result = evaluate_one_tree_synthetic(
            (SAMPLE,), (DraftSolarBin(MID, 3, SUN, True),), existing, TREE
        )
        self.assertEqual(
            (
                result.baseline_direct_sun_m2_h,
                result.proposal_direct_sun_m2_h,
                result.additional_useful_shade_m2_h,
            ),
            (0, 0, 0),
        )

    def test_missed_tree_has_valid_zero_gain(self):
        far_tree = ProposedTree(
            OpaqueEllipsoid((20, -1, 1), (0.5, 0.5, 0.5)),
            OpaqueTrunk(20, -1, 0, 0.1, 2),
        )
        result = evaluate_one_tree_synthetic(
            (SAMPLE,), (DraftSolarBin(MID, 3, SUN, True),), (), far_tree
        )
        self.assertEqual(
            (
                result.baseline_direct_sun_m2_h,
                result.proposal_direct_sun_m2_h,
                result.additional_useful_shade_m2_h,
            ),
            (6, 6, 0),
        )

    def test_static_triangle_baseline_and_crown_trunk_union(self):
        wall = StaticTriangle(((-2, -2, 0.5), (2, -2, 0.5), (0, 1, 0.5)))
        blocked = evaluate_one_tree_synthetic(
            (SAMPLE,), (DraftSolarBin(MID, 3, SUN, True),), (wall,), TREE
        )
        self.assertEqual(blocked.additional_useful_shade_m2_h, 0)
        # Crown and trunk both intersect this ray, but shade contributes once.
        clear = evaluate_one_tree_synthetic(
            (SAMPLE,), (DraftSolarBin(MID, 3, SUN, True),), (), TREE
        )
        self.assertEqual(clear.additional_useful_shade_m2_h, 6)

    def test_night_back_face_and_distinct_durations(self):
        night = evaluate_one_tree_synthetic(
            (SAMPLE,), (DraftSolarBin(MID, 1, SUN, False),), (), TREE
        )
        self.assertEqual(night.additional_useful_shade_m2_h, 0)
        back = ReceiverSample((0, 0, 0), (0, 1, 0), 2, "target")
        self.assertEqual(
            evaluate_one_tree_synthetic(
                (back,), (DraftSolarBin(MID, 1, SUN, True),), (), TREE
            ).additional_useful_shade_m2_h,
            0,
        )
        bins = (
            DraftSolarBin(datetime(2026, 6, 21, 11, tzinfo=UTC), 1, SUN, True),
            DraftSolarBin(datetime(2026, 6, 21, 13, tzinfo=UTC), 2, SUN, True),
        )
        result = evaluate_one_tree_synthetic((SAMPLE,), bins, (), TREE)
        self.assertEqual(result.additional_useful_shade_m2_h, 6)

    def test_invalid_inputs_and_overlap_rejected(self):
        with self.assertRaises(ValueError):
            evaluate_one_tree_synthetic(
                (), (DraftSolarBin(MID, 1, SUN, True),), (), TREE
            )
        with self.assertRaises(ValueError):
            evaluate_one_tree_synthetic(
                (SAMPLE,), (DraftSolarBin(MID, 0, SUN, True),), (), TREE
            )
        with self.assertRaises(ValueError):
            evaluate_one_tree_synthetic(
                (ReceiverSample((0, 0, 0), (0, 0, 2), 2, "target"),),
                (DraftSolarBin(MID, 1, SUN, True),),
                (),
                TREE,
            )
        with self.assertRaises(ValueError):
            evaluate_one_tree_synthetic(
                (SAMPLE,),
                (
                    DraftSolarBin(MID, 1, SUN, True),
                    DraftSolarBin(
                        datetime(2026, 6, 21, 12, 30, tzinfo=UTC), 1, SUN, True
                    ),
                ),
                (),
                TREE,
            )

    def test_invalid_geometry_rejected_even_at_night(self):
        invalid = ProposedTree(OpaqueEllipsoid((0, -1, 1), (0, 0.5, 0.5)), TREE.trunk)
        with self.assertRaises(ValueError):
            evaluate_one_tree_synthetic(
                (SAMPLE,), (DraftSolarBin(MID, 1, SUN, False),), (), invalid
            )


if __name__ == "__main__":
    unittest.main()
