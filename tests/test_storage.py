# test_storage.py
#
# Copyright 2025 Daniel Taylor
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
# SPDX-License-Identifier: GPL-3.0-or-later

import unittest
import gzip
import json
import shutil
from datetime import date
from pathlib import Path
from unittest.mock import patch

from src.storage import CycleStore
from src.models import Cycle

from gi.repository import GLib # type: ignore

class TestCycleStore(unittest.TestCase):
    """Unit tests for CycleStore persistence."""
    def setUp(self) -> None:
        self.app_id = "io.github.kingorgg.Luna"
        self.tmp_dir = Path(GLib.get_user_data_dir()) / self.app_id
        self.tmp_dir.mkdir(parents=True, exist_ok=True)
        
        self.store = CycleStore(app_id=self.app_id)

        self.store.path = self.tmp_dir / "test_cycles.json.gz"

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def make_cycle(self) -> Cycle:
        """Helper to create a Cycle with DayEntries."""
        cycle = Cycle(start_date=date(2025, 1, 1), duration=5)
        cycle.generate_days()
        cycle.days[0].mood = "happy"
        cycle.days[0].flow = "light"
        return cycle

    def test_add_and_get_cycle(self) -> None:
        """Adding and retrieving a cycle should work correctly."""
        cycle = self.make_cycle()
        self.store.add_cycle(cycle)
        
        self.assertTrue(self.store.path.exists())
        
        self.store.load()
        active = self.store.get_active_cycle()
        
        self.assertTrue(active.start_date == cycle.start_date)
        self.assertTrue(active.duration == cycle.duration)
        self.assertTrue(active.days[0].mood == "happy")
    
    def test_save_creates_compressed_file(self) -> None:
        """Ensure cycles are saved as gzip-compressed JSON."""
        self.store.cycles = [self.make_cycle()]
        self.store.save()
        
        with open(self.store.path, "rb") as f:
            magic = f.read(2)
            self.assertEqual(magic, b"\x1f\x8b")
            
        with gzip.open(self.store.path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertIsInstance(data, list)
        self.assertIn("start_date", data[0])
            
        
    def test_load_invalid_json(self) -> None:
        """Loading invalid JSON should not crash and should result in empty cycles."""
        with gzip.open(self.store.path, "wt", encoding="utf-8") as f:
            f.write("{invalid json}")
            
        with self.assertLogs(level="WARNING") as log:
            self.store.load()

        self.assertIn("Error loading cycles", log.output[0])
        self.assertEqual(self.store.cycles, [])
        
    def test_get_active_cycle_empty(self) -> None:
        """Getting active cycle from empty store should raise ValueError."""
        with self.assertRaises(ValueError):
            self.store.get_active_cycle()
            
    def test_atomic_save(self) -> None:
        """Ensure that save operation is atomic."""
        self.store.cycles = [self.make_cycle()]
        self.store.save()
        
        temp_path = self.store.path.with_suffix(".tmp")
        self.assertFalse(temp_path.exists())
        
        self.assertTrue(self.store.path.exists())
        with gzip.open(self.store.path, "rt", encoding="utf-8") as f:
            data = json.load(f)
        
        self.assertEqual(len(data), 1)
        
    @patch("src.storage.fcntl.flock")
    def test_save_with_lock(self, mock_flock):
        """Ensure save() uses flock for atomic replacement."""
        self.store.cycles = [self.make_cycle()]
        self.store.save()
        self.assertGreaterEqual(mock_flock.call_count, 2)


if __name__ == "__main__":
    unittest.main()