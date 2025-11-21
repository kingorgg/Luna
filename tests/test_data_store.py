import unittest
from unittest.mock import patch, MagicMock
from datetime import date, timedelta
import tempfile
from pathlib import Path

from src.data_store import DataStore
from src.models import Cycle, Pregnancy


class TestDataStore(unittest.TestCase):
    """Test cases for DataStore."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)

        # Mock GLib to use temp directory
        self.glib_patcher = patch("src.storage.GLib.get_user_data_dir")
        self.mock_glib = self.glib_patcher.start()
        self.mock_glib.return_value = str(self.temp_path)

        self.data_store = DataStore()

        self.start_date_1 = date(2025, 11, 1)
        self.start_date_2 = date(2025, 12, 1)
        self.start_date_3 = date(2026, 1, 1)

    def tearDown(self):
        """Clean up test fixtures."""
        self.glib_patcher.stop()
        self.temp_dir.cleanup()

    def test_data_store_initialization(self):
        """Test DataStore initializes with empty stores."""
        self.assertEqual(len(self.data_store.cycles.items), 0)
        self.assertEqual(len(self.data_store.pregnancies.items), 0)

    def test_add_cycle(self):
        """Test adding a cycle to the data store."""
        cycle = Cycle(start_date=self.start_date_1, duration=5)
        self.data_store.add_cycle(cycle)

        self.assertEqual(len(self.data_store.cycles.items), 1)
        self.assertEqual(self.data_store.cycles.items[0].start_date, self.start_date_1)

    def test_get_cycles(self):
        """Test retrieving all cycles."""
        cycle1 = Cycle(start_date=self.start_date_1, duration=5)
        cycle2 = Cycle(start_date=self.start_date_2, duration=5)

        self.data_store.add_cycle(cycle1)
        self.data_store.add_cycle(cycle2)

        cycles = self.data_store.get_cycles()
        self.assertEqual(len(cycles), 2)

    def test_get_active_cycle(self):
        """Test getting the active (most recent) cycle."""
        cycle1 = Cycle(start_date=self.start_date_1, duration=5)
        cycle2 = Cycle(start_date=self.start_date_2, duration=5)

        self.data_store.add_cycle(cycle1)
        self.data_store.add_cycle(cycle2)

        active = self.data_store.get_active_cycle()
        self.assertEqual(active.start_date, self.start_date_2)

    def test_get_active_cycle_empty(self):
        """Test getting active cycle when none exist."""
        active = self.data_store.get_active_cycle()
        self.assertIsNone(active)

    def test_delete_cycle(self):
        """Test deleting a cycle."""
        cycle = Cycle(start_date=self.start_date_1, duration=5)
        self.data_store.add_cycle(cycle)

        self.assertEqual(len(self.data_store.cycles.items), 1)

        self.data_store.delete_cycle(cycle)
        self.assertEqual(len(self.data_store.cycles.items), 0)

    def test_add_pregnancy(self):
        """Test adding a pregnancy to the data store."""
        pregnancy = Pregnancy(start_date=self.start_date_1)
        self.data_store.add_pregnancy(pregnancy)

        self.assertEqual(len(self.data_store.pregnancies.items), 1)
        self.assertEqual(
            self.data_store.pregnancies.items[0].start_date, self.start_date_1
        )

    def test_get_pregnancies(self):
        """Test retrieving all pregnancies."""
        preg1 = Pregnancy(start_date=self.start_date_1)
        preg2 = Pregnancy(start_date=self.start_date_2)

        self.data_store.add_pregnancy(preg1)
        self.data_store.add_pregnancy(preg2)

        pregnancies = self.data_store.get_pregnancies()
        self.assertEqual(len(pregnancies), 2)

    def test_get_active_pregnancy(self):
        """Test getting the active pregnancy."""
        preg1 = Pregnancy(start_date=self.start_date_1)
        preg2 = Pregnancy(start_date=self.start_date_2)

        self.data_store.add_pregnancy(preg1)
        self.data_store.add_pregnancy(preg2)

        active = self.data_store.get_active_pregnancy()
        self.assertEqual(active.start_date, self.start_date_2)

    def test_link_pregnancy_to_cycle(self):
        """Test that pregnancy is linked to the correct cycle."""
        cycle1 = Cycle(start_date=self.start_date_1, duration=5)
        cycle2 = Cycle(start_date=self.start_date_2, duration=5)

        self.data_store.add_cycle(cycle1)
        self.data_store.add_cycle(cycle2)

        # Pregnancy falls between cycle1 and cycle2
        preg_date = self.start_date_1 + timedelta(days=15)
        pregnancy = Pregnancy(start_date=preg_date)

        self.data_store.add_pregnancy(pregnancy)

        # Pregnancy should be linked to cycle1
        self.assertEqual(cycle1.pregnancy, pregnancy)
        self.assertEqual(cycle1.pregnancy_id, pregnancy.id)
        self.assertIsNone(cycle2.pregnancy)

    def test_auto_link_all_pregnancies(self):
        """Test automatic linking of multiple pregnancies to cycles."""
        cycle1 = Cycle(start_date=self.start_date_1, duration=5)
        cycle2 = Cycle(start_date=self.start_date_2, duration=5)
        cycle3 = Cycle(start_date=self.start_date_3, duration=5)

        self.data_store.add_cycle(cycle1)
        self.data_store.add_cycle(cycle2)
        self.data_store.add_cycle(cycle3)

        preg1 = Pregnancy(start_date=self.start_date_1 + timedelta(days=10))
        preg2 = Pregnancy(start_date=self.start_date_2 + timedelta(days=10))

        self.data_store.add_pregnancy(preg1)
        self.data_store.add_pregnancy(preg2)

        self.assertEqual(cycle1.pregnancy, preg1)
        self.assertEqual(cycle2.pregnancy, preg2)
        self.assertIsNone(cycle3.pregnancy)

    def test_relink_on_cycle_deletion(self):
        """Test that pregnancies are relinked when a cycle is deleted."""
        cycle1 = Cycle(start_date=self.start_date_1, duration=5)
        cycle2 = Cycle(start_date=self.start_date_2, duration=5)

        self.data_store.add_cycle(cycle1)
        self.data_store.add_cycle(cycle2)

        # Add pregnancy in cycle1's date range
        preg = Pregnancy(start_date=self.start_date_1 + timedelta(days=10))
        self.data_store.add_pregnancy(preg)

        self.assertEqual(cycle1.pregnancy, preg)

        # Delete cycle1, pregnancy should now link to cycle2 (if dates allow)
        self.data_store.delete_cycle(cycle1)

        # Since cycle2 is the only one left and preg date is before it,
        # it should link to cycle2
        remaining_cycle = self.data_store.cycles.items[0]
        self.assertEqual(remaining_cycle.pregnancy, preg)

    def test_restore_links_after_reload(self):
        """Test that links are restored after reloading data."""
        cycle = Cycle(start_date=self.start_date_1, duration=5)
        pregnancy = Pregnancy(start_date=self.start_date_1 + timedelta(days=10))

        self.data_store.add_cycle(cycle)
        self.data_store.add_pregnancy(pregnancy)

        cycle_id = cycle.id if hasattr(cycle, "id") else id(cycle)
        preg_id = pregnancy.id

        # Reload data
        self.data_store.reload()

        # Links should be restored
        reloaded_cycle = self.data_store.cycles.items[0]
        self.assertIsNotNone(reloaded_cycle.pregnancy)
        self.assertEqual(reloaded_cycle.pregnancy.id, preg_id)

    def test_save_all_persists_data(self):
        """Test that save_all persists data to storage."""
        cycle = Cycle(start_date=self.start_date_1, duration=5)
        pregnancy = Pregnancy(start_date=self.start_date_1 + timedelta(days=10))

        self.data_store.add_cycle(cycle)
        self.data_store.add_pregnancy(pregnancy)

        # Save explicitly
        self.data_store.save_all()

        # Create new DataStore and reload
        new_store = DataStore()

        self.assertEqual(len(new_store.cycles.items), 1)
        self.assertEqual(len(new_store.pregnancies.items), 1)

    def test_multiple_cycles_same_date_gets_most_recent(self):
        """Test getting active cycle when multiple exist."""
        cycles = [
            Cycle(start_date=self.start_date_1, duration=5),
            Cycle(start_date=self.start_date_2, duration=5),
            Cycle(start_date=self.start_date_3, duration=5),
        ]

        for cycle in cycles:
            self.data_store.add_cycle(cycle)

        active = self.data_store.get_active_cycle()
        self.assertEqual(active.start_date, self.start_date_3)

    def test_pregnancy_without_matching_cycle(self):
        """Test adding pregnancy when no cycles exist."""
        pregnancy = Pregnancy(start_date=self.start_date_1)

        # Should not raise an error
        self.data_store.add_pregnancy(pregnancy)

        self.assertEqual(len(self.data_store.pregnancies.items), 1)

    def test_changed_signal_emitted_on_add_cycle(self):
        """Test that changed signal is emitted when adding a cycle."""
        signal_handler = MagicMock()
        self.data_store.connect("changed", lambda *args: signal_handler())

        cycle = Cycle(start_date=self.start_date_1, duration=5)
        self.data_store.add_cycle(cycle)

        signal_handler.assert_called_once()

    def test_changed_signal_emitted_on_add_pregnancy(self):
        """Test that changed signal is emitted when adding a pregnancy."""
        signal_handler = MagicMock()
        self.data_store.connect("changed", lambda *args: signal_handler())

        pregnancy = Pregnancy(start_date=self.start_date_1)
        self.data_store.add_pregnancy(pregnancy)

        signal_handler.assert_called_once()

    def test_changed_signal_emitted_on_delete_cycle(self):
        """Test that changed signal is emitted when deleting a cycle."""
        cycle = Cycle(start_date=self.start_date_1, duration=5)
        self.data_store.add_cycle(cycle)

        signal_handler = MagicMock()
        self.data_store.connect("changed", lambda *args: signal_handler())

        self.data_store.delete_cycle(cycle)

        signal_handler.assert_called_once()


if __name__ == "__main__":
    unittest.main()
