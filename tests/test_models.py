# test_models.py
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
from datetime import date, timedelta

from src.models import Cycle, DayEntry, DayEntryDict, CycleDict

class TestDayEntry(unittest.TestCase):
    """Unit tests for DayEntry model."""
    def test_to_dict(self) -> None:
        """DayEntry.to_dict() should serialize correctly."""
        day = DayEntry(
            date=date(2025, 1, 1),
            symptoms=["cramps", "headache"],
            mood="happy",
            temperature=36.5,
            flow="light",
            notes="Felt good today."
        )
        
        day_dict: DayEntryDict = day.to_dict()
        
        self.assertEqual(day_dict["date"], "2025-01-01")
        self.assertEqual(day_dict["symptoms"], ["cramps", "headache"])
        self.assertEqual(day_dict["mood"], "happy")
        self.assertEqual(day_dict["temperature"], 36.5)
        self.assertEqual(day_dict["flow"], "light")
        self.assertEqual(day_dict["notes"], "Felt good today.")
        
    def test_optional_fields_default(self) -> None:
        """Ensure optional fields default to None or [] when not provided."""
        entry: DayEntry = DayEntry(date=date(2025, 1, 1))
        data: DayEntryDict = entry.to_dict()
        
        self.assertEqual(data["symptoms"], [])
        self.assertIsNone(data["mood"])
        self.assertIsNone(data["flow"])
        self.assertIsNone(data["temperature"])
        self.assertIsNone(data["notes"])


class TestCycle(unittest.TestCase):
    """Unit tests for Cycle model."""
    def test_generate_days_creates_expected_dates(self):
        """Cycle.generate_days() should create DayEntry objects with correct dates."""
        start: date = date(2025, 1, 1)
        cycle: Cycle = Cycle(start_date=start, duration=3)
        
        cycle.generate_days()
        
        self.assertEqual(len(cycle.days), 3)
        self.assertEqual(cycle.days[0].date, start)
        self.assertEqual(cycle.days[2].date, start + timedelta(days=2))
            
    def test_to_dict_and_from_dict_roundtrip(self):
        """Ensure Cycle can serialize to dict and back without data loss."""
        cycle: Cycle = Cycle(start_date=date(2025, 1, 1), duration=2)
        cycle.generate_days()
        
        cycle.days[0].mood = "happy"
        cycle.days[1].flow = "light"

        data: CycleDict = cycle.to_dict()
        new_cycle: Cycle = Cycle.from_dict(data)

        self.assertEqual(new_cycle.start_date, cycle.start_date)
        self.assertEqual(new_cycle.duration, 2)
        self.assertEqual(new_cycle.days[0].mood, "happy")
        self.assertEqual(new_cycle.days[1].flow, "light")
        
    def test_from_dict_handles_missing_days(self):
        """Ensure from_dict() correctly handles missing 'days' key."""
        data: CycleDict = {"start_date": "2025-01-01", "duration": 5}
        
        cycle: Cycle = Cycle.from_dict(data)
        self.assertEqual(cycle.days, [])
        
    def test_from_dict_with_partial_day_fields(self) -> None:
        """Ensure from_dict() handles missing optional fields in DayEntry."""
        data: CycleDict = {
            "start_date": "2025-01-01",
            "duration": 1,
            "days": [{"date": "2025-01-01"}]  # minimal day entry
        }

        cycle: Cycle = Cycle.from_dict(data)
        day: DayEntry = cycle.days[0]

        self.assertEqual(day.date, date(2025, 1, 1))
        self.assertEqual(day.symptoms, [])
        self.assertIsNone(day.mood)
        self.assertIsNone(day.flow)
        self.assertIsNone(day.temperature)
        self.assertIsNone(day.notes)
        

if __name__ == "__main__":
    unittest.main()