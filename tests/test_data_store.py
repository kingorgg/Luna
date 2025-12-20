import unittest
from datetime import date
from unittest.mock import MagicMock, patch

from src.data_store import DataStore
from src.models import Cycle, Pregnancy


class TestDataStore(unittest.TestCase):
    def setUp(self):
        # Patch SQLiteStore to use in-memory DB
        patcher = patch("src.data_store.SQLiteStore")
        self.addCleanup(patcher.stop)
        self.mock_sqlite_cls = patcher.start()
        self.mock_sqlite = self.mock_sqlite_cls.return_value

        # Provide empty return values for get_cycles/get_pregnancies
        self.mock_sqlite.get_cycles.return_value = []
        self.mock_sqlite.get_pregnancies.return_value = []

        self.store = DataStore()

    def tearDown(self):
        self.store.close()

    def test_add_cycle_emits_changed(self):
        cycle = Cycle(start_date=date(2025, 12, 20), duration=3)
        callback = MagicMock()
        self.store.connect("changed", callback)

        self.store.add_cycle(cycle)
        self.mock_sqlite.insert_cycle.assert_called_once_with(cycle)
        callback.assert_called_once()

    def test_update_cycle_emits_changed(self):
        cycle = Cycle(start_date=date(2025, 12, 20), duration=3)
        callback = MagicMock()
        self.store.connect("changed", callback)

        self.store.update_cycle(cycle)
        self.mock_sqlite.update_cycle.assert_called_once_with(cycle)
        callback.assert_called_once()

    def test_delete_cycle_emits_changed(self):
        cycle = Cycle(start_date=date(2025, 12, 20), duration=3)
        callback = MagicMock()
        self.store.connect("changed", callback)

        self.store.delete_cycle(cycle)
        self.mock_sqlite.delete_cycle.assert_called_once_with(cycle)
        callback.assert_called_once()

    def test_add_pregnancy_emits_changed(self):
        preg = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        callback = MagicMock()
        self.store.connect("changed", callback)

        self.store.add_pregnancy(preg)
        self.mock_sqlite.insert_pregnancy.assert_called_once_with(preg)
        callback.assert_called_once()

    def test_update_pregnancy_emits_changed(self):
        preg = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        callback = MagicMock()
        self.store.connect("changed", callback)

        self.store.update_pregnancy(preg)
        self.mock_sqlite.update_pregnancy.assert_called_once_with(preg)
        callback.assert_called_once()

    def test_delete_pregnancy_emits_changed(self):
        preg = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        callback = MagicMock()
        self.store.connect("changed", callback)

        self.store.delete_pregnancy(preg)
        self.mock_sqlite.delete_pregnancy.assert_called_once_with(preg)
        callback.assert_called_once()

    def test_get_cycles_and_active_cycle(self):
        cycle1 = Cycle(start_date=date(2025, 12, 20), duration=3)
        cycle2 = Cycle(start_date=date(2025, 12, 21), duration=2)
        self.mock_sqlite.get_cycles.return_value = [cycle1, cycle2]
        self.mock_sqlite.get_active_cycle.return_value = cycle2

        cycles = self.store.get_cycles()
        self.assertEqual(cycles, [cycle1, cycle2])
        self.assertEqual(self.store.get_active_cycle(), cycle2)

    def test_get_pregnancies_and_active_pregnancy(self):
        preg1 = Pregnancy(start_date=date(2025, 12, 20), confirmed=True)
        preg2 = Pregnancy(start_date=date(2025, 12, 21), confirmed=True)
        self.mock_sqlite.get_pregnancies.return_value = [preg1, preg2]
        self.mock_sqlite.get_active_pregnancy.return_value = preg2

        pregnancies = self.store.get_pregnancies()
        self.assertEqual(pregnancies, [preg1, preg2])
        self.assertEqual(self.store.get_active_pregnancy(), preg2)

    def test_save_all_is_noop(self):
        # save_all just passes
        self.store.save_all()  # Should not raise

    def test_reload_is_noop(self):
        # reload just passes
        self.store.reload()  # Should not raise


if __name__ == "__main__":
    unittest.main()
