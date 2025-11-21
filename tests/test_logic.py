import unittest
from datetime import date, timedelta

from src.logic import CycleStats
from src.models import Cycle, Pregnancy


class TestCycleStats(unittest.TestCase):
    def test_no_cycles(self):
        stats = CycleStats([], cycle_len=28, luteal_len=14)
        self.assertEqual(stats.intervals, [])
        self.assertEqual(stats.average_cycle_length(), 28.0)
        self.assertEqual(stats.cycle_length_std_dev(), 0.0)
        self.assertEqual(stats.cycle_length_range(), "-")
        self.assertIsNone(stats.predicted_next_period)
        self.assertIsNone(stats.predicted_ovulation)

    def test_single_cycle_uses_fallback_cycle_len(self):
        c = Cycle(start_date=date(2025, 11, 1), duration=5)
        stats = CycleStats([c], cycle_len=30, luteal_len=14)
        self.assertEqual(stats.intervals, [])
        # With no intervals average should fall back to provided cycle_len
        self.assertEqual(stats.average_cycle_length(), 30.0)
        self.assertEqual(stats.cycle_length_std_dev(), 0.0)
        # predicted next period = last.start_date + cycle_len days
        expected = c.start_date + timedelta(days=30)
        self.assertEqual(stats.predicted_next_period, expected)
        # ovulation = predicted_next_period - luteal_len
        self.assertEqual(stats.predicted_ovulation, expected - timedelta(days=14))

    def test_intervals_mean_std_range_and_predictions(self):
        # Create three cycles with known intervals: 30 and 28 -> mean 29, stdev sqrt(2)
        c1 = Cycle(start_date=date(2025, 1, 1), duration=5)
        c2 = Cycle(start_date=date(2025, 1, 31), duration=5)   # +30 days
        c3 = Cycle(start_date=date(2025, 2, 28), duration=5)   # +28 days
        stats = CycleStats([c1, c2, c3], cycle_len=28, luteal_len=14)

        self.assertEqual(stats.intervals, [30, 28])
        self.assertAlmostEqual(stats.average_cycle_length(), 29.0)
        # sample stdev of [30,28] = sqrt(2)
        self.assertAlmostEqual(stats.cycle_length_std_dev(), 2 ** 0.5, places=6)
        self.assertEqual(stats.cycle_length_range(), "28-30 days")

        # predicted next period = last.start_date + int(mean) days
        expected_next = c3.start_date + timedelta(days=29)
        self.assertEqual(stats.predicted_next_period, expected_next)
        self.assertEqual(stats.predicted_ovulation, expected_next - timedelta(days=14))

    def test_excludes_cycles_with_pregnancy(self):
        # cycles where one has a linked pregnancy should be excluded from calculations
        c1 = Cycle(start_date=date(2025, 1, 1), duration=5)
        c2 = Cycle(start_date=date(2025, 2, 1), duration=5)
        preg = Pregnancy(start_date=date(2025, 2, 10))
        # link pregnancy to c2
        c2.pregnancy = preg

        stats = CycleStats([c1, c2], cycle_len=28, luteal_len=14)
        # only c1 should be considered -> intervals empty, predicted next uses fallback
        self.assertEqual(stats.intervals, [])
        self.assertEqual(stats.average_cycle_length(), 28.0)
        self.assertEqual(stats.predicted_next_period, c1.start_date + timedelta(days=28))


if __name__ == "__main__":
    unittest.main()