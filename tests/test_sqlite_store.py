import unittest
from datetime import date

from src.constants import APP_ID
from src.models import Cycle, DayEntry, Pregnancy
from src.sqlite_store import SQLiteStore


class TestSQLiteStore(unittest.TestCase):
    def setUp(self):
        # Use an in-memory SQLite DB for testing
        self.store = SQLiteStore(app_id=APP_ID, db_path=":memory:")

    def tearDown(self):
        self.store.close()

    def test_insert_and_get_cycle(self):
        cycle = Cycle(start_date=date(2025, 12, 20), duration=3)
        cycle.days = [
            DayEntry(date=date(2025, 12, 20), mood="happy", flow="light"),
            DayEntry(date=date(2025, 12, 21), mood="sad", flow="medium"),
        ]

        self.store.insert_cycle(cycle)
        cycles = self.store.get_cycles()

        self.assertEqual(len(cycles), 1)
        c = cycles[0]
        self.assertEqual(c.start_date, cycle.start_date)
        self.assertEqual(c.duration, cycle.duration)
        self.assertEqual(len(c.days), 2)
        self.assertEqual(c.days[0].mood, "happy")
        self.assertEqual(c.days[1].flow, "medium")

    def test_update_cycle(self):
        cycle = Cycle(start_date=date(2025, 12, 20), duration=3)
        self.store.insert_cycle(cycle)
        cycle.duration = 5
        self.store.update_cycle(cycle)
        cycles = self.store.get_cycles()
        self.assertEqual(cycles[0].duration, 5)

    def test_delete_cycle(self):
        cycle = Cycle(start_date=date(2025, 12, 20), duration=3)
        self.store.insert_cycle(cycle)
        self.store.delete_cycle(cycle)
        cycles = self.store.get_cycles()
        self.assertEqual(len(cycles), 0)

    def test_insert_and_get_pregnancy(self):
        preg = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        self.store.insert_pregnancy(preg)
        pregnancies = self.store.get_pregnancies()
        self.assertEqual(len(pregnancies), 1)
        self.assertEqual(pregnancies[0].start_date, preg.start_date)
        self.assertTrue(pregnancies[0].confirmed)

    def test_update_pregnancy(self):
        preg = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        self.store.insert_pregnancy(preg)
        preg.confirmed = False
        self.store.update_pregnancy(preg)
        pregnancies = self.store.get_pregnancies()
        self.assertFalse(pregnancies[0].confirmed)

    def test_delete_pregnancy(self):
        preg = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        self.store.insert_pregnancy(preg)
        self.store.delete_pregnancy(preg)
        pregnancies = self.store.get_pregnancies()
        self.assertEqual(len(pregnancies), 0)

    def test_link_pregnancy_to_cycle(self):
        preg = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        self.store.insert_pregnancy(preg)

        cycle = Cycle(start_date=date(2025, 12, 20), duration=3, pregnancy_id=preg.id)
        self.store.insert_cycle(cycle)

        cycles = self.store.get_cycles()
        self.assertIsNotNone(cycles[0].pregnancy)
        self.assertEqual(cycles[0].pregnancy.id, preg.id)

    def test_get_active_cycle_and_pregnancy(self):
        cycle1 = Cycle(start_date=date(2025, 12, 20), duration=3)
        cycle2 = Cycle(start_date=date(2025, 12, 21), duration=2)
        self.store.insert_cycle(cycle1)
        self.store.insert_cycle(cycle2)

        active_cycle = self.store.get_active_cycle()
        self.assertEqual(active_cycle.start_date, cycle2.start_date)

        preg1 = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        preg2 = Pregnancy(start_date=date(2025, 12, 21), confirmed=True)
        self.store.insert_pregnancy(preg1)
        self.store.insert_pregnancy(preg2)

        active_preg = self.store.get_active_pregnancy()
        self.assertEqual(active_preg.start_date, preg2.start_date)


if __name__ == "__main__":
    unittest.main()
