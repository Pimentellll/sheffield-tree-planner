"""Synthetic and published-reference checks for the STP-008 draft."""

import math
import sys
import unittest
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from tree_planner.physics.solar import (
    DraftTimeBin,
    direct_incidence,
    direction_from_angles,
    local_to_utc,
    solar_direction_enu,
    validate_time_bins,
)


class SolarDraftTests(unittest.TestCase):
    def test_cardinal_enu_and_shadow_direction(self):
        south = direction_from_angles(180, 45)
        self.assertAlmostEqual(south.enu[0], 0, places=14)
        self.assertAlmostEqual(south.enu[1], -math.sqrt(0.5), places=14)
        self.assertAlmostEqual(south.enu[2], math.sqrt(0.5), places=14)
        self.assertAlmostEqual(direction_from_angles(90, 0).enu[0], 1)
        self.assertAlmostEqual(direct_incidence(south, (0, 0, 1)), math.sqrt(0.5))
        self.assertEqual(direct_incidence(south, (0, 1, 0)), 0)
        self.assertEqual(
            direct_incidence(direction_from_angles(180, -10), (0, 0, 1)), 0
        )

    def test_published_nrel_spa_example(self):
        # NREL/TP-560-34302 (2008), Appendix A.5:
        # https://www.nrel.gov/docs/fy08osti/34302.pdf
        # 2003-10-17 12:30:30 MST,
        # 39.742476 N, -105.1786 E; apparent zenith 50.11162 deg,
        # azimuth 194.34024 deg. Reference includes altitude 1830.14 m.
        # Our draft uses geometric elevation, whereas NREL tabulates apparent
        # elevation. The roughly 0.0163 degree difference is atmospheric refraction.
        actual = solar_direction_enu(
            39.742476, -105.1786, datetime(2003, 10, 17, 19, 30, 30, tzinfo=UTC)
        )
        self.assertAlmostEqual(actual.azimuth_deg, 194.34024, delta=0.0001)
        self.assertAlmostEqual(actual.elevation_deg, 90 - 50.11162, delta=0.02)

    def test_solar_day_night_and_repeatability(self):
        noon = datetime(2026, 6, 21, 12, tzinfo=UTC)
        night = datetime(2026, 6, 21, 0, tzinfo=UTC)
        sun = solar_direction_enu(53.3811, -1.4701, noon)
        self.assertTrue(sun.above_horizon)
        self.assertLess(sun.enu[1], 0)
        self.assertEqual(sun, solar_direction_enu(53.3811, -1.4701, noon))
        self.assertFalse(solar_direction_enu(53.3811, -1.4701, night).above_horizon)

    def test_london_dst(self):
        self.assertEqual(
            local_to_utc(datetime(2026, 3, 29, 0, 30)),
            datetime(2026, 3, 29, 0, 30, tzinfo=UTC),
        )
        self.assertEqual(
            local_to_utc(datetime(2026, 3, 29, 2, 30)),
            datetime(2026, 3, 29, 1, 30, tzinfo=UTC),
        )
        for ambiguous in (datetime(2026, 3, 29, 1, 30), datetime(2026, 10, 25, 1, 30)):
            with self.assertRaises(ValueError):
                local_to_utc(ambiguous)

    def test_time_bins_and_invalid_inputs(self):
        one = DraftTimeBin(datetime(2026, 6, 1, 12, tzinfo=UTC), 1)
        two = DraftTimeBin(datetime(2026, 6, 1, 13, tzinfo=UTC), 1)
        validate_time_bins([one, two])
        with self.assertRaises(ValueError):
            validate_time_bins(
                [one, DraftTimeBin(datetime(2026, 6, 1, 12, 30, tzinfo=UTC), 1)]
            )
        with self.assertRaises(ValueError):
            validate_time_bins([DraftTimeBin(datetime(2026, 6, 1, 12, tzinfo=UTC), 0)])
        with self.assertRaises(ValueError):
            solar_direction_enu(53, -1, datetime(2026, 6, 1, 12))
        with self.assertRaises(ValueError):
            direction_from_angles(float("nan"), 30)
        with self.assertRaises(ValueError):
            direct_incidence(direction_from_angles(180, 45), (0, 0, 2))


if __name__ == "__main__":
    unittest.main()
