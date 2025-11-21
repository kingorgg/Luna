import unittest
from datetime import date, timedelta
from src.models import DayEntry, Pregnancy, Cycle


class TestDayEntry(unittest.TestCase):
    """Test cases for DayEntry model."""

    def setUp(self):
        self.test_date = date(2025, 11, 21)

    def test_day_entry_creation(self):
        """Test creating a DayEntry with all fields."""
        entry = DayEntry(
            date=self.test_date,
            symptoms=["cramps", "headache"],
            mood="anxious",
            temperature=37.2,
            flow="heavy",
            notes="Test note",
        )
        self.assertEqual(entry.date, self.test_date)
        self.assertEqual(entry.symptoms, ["cramps", "headache"])
        self.assertEqual(entry.mood, "anxious")
        self.assertEqual(entry.temperature, 37.2)
        self.assertEqual(entry.flow, "heavy")
        self.assertEqual(entry.notes, "Test note")

    def test_day_entry_defaults(self):
        """Test DayEntry with default values."""
        entry = DayEntry(date=self.test_date)
        self.assertEqual(entry.date, self.test_date)
        self.assertEqual(entry.symptoms, [])
        self.assertIsNone(entry.mood)
        self.assertIsNone(entry.temperature)
        self.assertIsNone(entry.flow)
        self.assertIsNone(entry.notes)

    def test_day_entry_to_dict(self):
        """Test converting DayEntry to dictionary."""
        entry = DayEntry(
            date=self.test_date,
            symptoms=["cramps"],
            mood="sad",
            temperature=36.8,
            flow="light",
            notes="Feeling tired",
        )
        result = entry.to_dict()
        self.assertEqual(result["date"], self.test_date.isoformat())
        self.assertEqual(result["symptoms"], ["cramps"])
        self.assertEqual(result["mood"], "sad")
        self.assertEqual(result["temperature"], 36.8)
        self.assertEqual(result["flow"], "light")
        self.assertEqual(result["notes"], "Feeling tired")

    def test_day_entry_from_dict(self):
        """Test creating DayEntry from dictionary."""
        data = {
            "date": self.test_date.isoformat(),
            "symptoms": ["headache"],
            "mood": "happy",
            "temperature": 37.0,
            "flow": "medium",
            "notes": "Feeling good",
        }
        entry = DayEntry.from_dict(data)
        self.assertEqual(entry.date, self.test_date)
        self.assertEqual(entry.symptoms, ["headache"])
        self.assertEqual(entry.mood, "happy")
        self.assertEqual(entry.temperature, 37.0)
        self.assertEqual(entry.flow, "medium")
        self.assertEqual(entry.notes, "Feeling good")

    def test_day_entry_roundtrip(self):
        """Test to_dict and from_dict roundtrip."""
        original = DayEntry(
            date=self.test_date,
            symptoms=["cramps", "bloating"],
            mood="neutral",
            temperature=36.9,
            flow="heavy",
            notes="Day 1",
        )
        restored = DayEntry.from_dict(original.to_dict())
        self.assertEqual(restored.date, original.date)
        self.assertEqual(restored.symptoms, original.symptoms)
        self.assertEqual(restored.mood, original.mood)
        self.assertEqual(restored.temperature, original.temperature)
        self.assertEqual(restored.flow, original.flow)
        self.assertEqual(restored.notes, original.notes)


class TestPregnancy(unittest.TestCase):
    """Test cases for Pregnancy model."""

    def setUp(self):
        self.start_date = date(2025, 11, 1)
        self.end_date = date(2026, 8, 1)

    def test_pregnancy_creation(self):
        """Test creating a Pregnancy with all fields."""
        pregnancy = Pregnancy(
            start_date=self.start_date,
            confirmed=True,
            end_date=self.end_date,
            notes="Test pregnancy",
            custom_due_date=date(2026, 8, 10),
        )
        self.assertEqual(pregnancy.start_date, self.start_date)
        self.assertTrue(pregnancy.confirmed)
        self.assertEqual(pregnancy.end_date, self.end_date)
        self.assertEqual(pregnancy.notes, "Test pregnancy")
        self.assertEqual(pregnancy.custom_due_date, date(2026, 8, 10))

    def test_pregnancy_defaults(self):
        """Test Pregnancy with default values."""
        pregnancy = Pregnancy(start_date=self.start_date)
        self.assertEqual(pregnancy.start_date, self.start_date)
        self.assertTrue(pregnancy.confirmed)
        self.assertIsNone(pregnancy.end_date)
        self.assertIsNone(pregnancy.notes)
        self.assertIsNone(pregnancy.custom_due_date)
        self.assertIsNotNone(pregnancy.id)

    def test_pregnancy_is_active_true(self):
        """Test is_active returns True when end_date is None."""
        pregnancy = Pregnancy(start_date=self.start_date)
        self.assertTrue(pregnancy.is_active)

    def test_pregnancy_is_active_false(self):
        """Test is_active returns False when end_date is set."""
        pregnancy = Pregnancy(start_date=self.start_date, end_date=self.end_date)
        self.assertFalse(pregnancy.is_active)

    def test_pregnancy_to_dict(self):
        """Test converting Pregnancy to dictionary."""
        pregnancy = Pregnancy(
            start_date=self.start_date,
            confirmed=True,
            end_date=self.end_date,
            notes="Test",
            custom_due_date=date(2026, 8, 10),
        )
        result = pregnancy.to_dict()
        self.assertEqual(result["start_date"], self.start_date.isoformat())
        self.assertTrue(result["confirmed"])
        self.assertEqual(result["end_date"], self.end_date.isoformat())
        self.assertEqual(result["notes"], "Test")
        self.assertEqual(result["custom_due_date"], date(2026, 8, 10).isoformat())
        self.assertIn("id", result)

    def test_pregnancy_from_dict(self):
        """Test creating Pregnancy from dictionary."""
        data = {
            "id": "test-id-123",
            "start_date": self.start_date.isoformat(),
            "confirmed": False,
            "end_date": self.end_date.isoformat(),
            "notes": "From dict",
            "custom_due_date": date(2026, 8, 10).isoformat(),
        }
        pregnancy = Pregnancy.from_dict(data)
        self.assertEqual(pregnancy.id, "test-id-123")
        self.assertEqual(pregnancy.start_date, self.start_date)
        self.assertFalse(pregnancy.confirmed)
        self.assertEqual(pregnancy.end_date, self.end_date)
        self.assertEqual(pregnancy.notes, "From dict")
        self.assertEqual(pregnancy.custom_due_date, date(2026, 8, 10))

    def test_pregnancy_roundtrip(self):
        """Test to_dict and from_dict roundtrip."""
        original = Pregnancy(
            start_date=self.start_date,
            confirmed=True,
            end_date=self.end_date,
            notes="Roundtrip test",
            custom_due_date=date(2026, 8, 15),
        )
        restored = Pregnancy.from_dict(original.to_dict())
        self.assertEqual(restored.id, original.id)
        self.assertEqual(restored.start_date, original.start_date)
        self.assertEqual(restored.confirmed, original.confirmed)
        self.assertEqual(restored.end_date, original.end_date)
        self.assertEqual(restored.notes, original.notes)
        self.assertEqual(restored.custom_due_date, original.custom_due_date)


class TestCycle(unittest.TestCase):
    """Test cases for Cycle model."""

    def setUp(self):
        self.start_date = date(2025, 11, 1)
        self.duration = 5

    def test_cycle_creation(self):
        """Test creating a Cycle."""
        cycle = Cycle(start_date=self.start_date, duration=self.duration)
        self.assertEqual(cycle.start_date, self.start_date)
        self.assertEqual(cycle.duration, self.duration)
        self.assertIsNone(cycle.pregnancy_id)
        self.assertEqual(cycle.days, [])

    def test_cycle_generate_days(self):
        """Test generating DayEntry objects for a cycle."""
        cycle = Cycle(start_date=self.start_date, duration=self.duration)
        cycle.generate_days()
        self.assertEqual(len(cycle.days), self.duration)
        for i, day in enumerate(cycle.days):
            expected_date = self.start_date + timedelta(days=i)
            self.assertEqual(day.date, expected_date)

    def test_cycle_generate_days_called_once(self):
        """Test that generate_days doesn't overwrite existing days."""
        cycle = Cycle(start_date=self.start_date, duration=self.duration)
        cycle.generate_days()
        first_gen = cycle.days.copy()
        cycle.generate_days()  # Call again
        self.assertEqual(cycle.days, first_gen)

    def test_cycle_pregnancy_setter_getter(self):
        """Test setting and getting pregnancy on a cycle."""
        cycle = Cycle(start_date=self.start_date, duration=self.duration)
        pregnancy = Pregnancy(start_date=self.start_date)
        
        cycle.pregnancy = pregnancy
        self.assertEqual(cycle.pregnancy, pregnancy)
        self.assertEqual(cycle.pregnancy_id, pregnancy.id)

    def test_cycle_pregnancy_setter_none(self):
        """Test setting pregnancy to None."""
        cycle = Cycle(start_date=self.start_date, duration=self.duration)
        pregnancy = Pregnancy(start_date=self.start_date)
        cycle.pregnancy = pregnancy
        
        cycle.pregnancy = None
        self.assertIsNone(cycle.pregnancy)
        self.assertIsNone(cycle.pregnancy_id)

    def test_cycle_to_dict(self):
        """Test converting Cycle to dictionary."""
        cycle = Cycle(
            start_date=self.start_date,
            duration=self.duration,
            pregnancy_id="preg-123",
        )
        cycle.generate_days()
        result = cycle.to_dict()
        
        self.assertEqual(result["start_date"], self.start_date.isoformat())
        self.assertEqual(result["duration"], self.duration)
        self.assertEqual(result["pregnancy_id"], "preg-123")
        self.assertEqual(len(result["days"]), self.duration)

    def test_cycle_from_dict(self):
        """Test creating Cycle from dictionary."""
        data = {
            "start_date": self.start_date.isoformat(),
            "duration": self.duration,
            "pregnancy_id": "preg-456",
            "days": [
                {
                    "date": (self.start_date + timedelta(days=i)).isoformat(),
                    "symptoms": [],
                    "mood": None,
                    "temperature": None,
                    "flow": None,
                    "notes": None,
                }
                for i in range(self.duration)
            ],
        }
        cycle = Cycle.from_dict(data)
        self.assertEqual(cycle.start_date, self.start_date)
        self.assertEqual(cycle.duration, self.duration)
        self.assertEqual(cycle.pregnancy_id, "preg-456")
        self.assertEqual(len(cycle.days), self.duration)

    def test_cycle_roundtrip(self):
        """Test to_dict and from_dict roundtrip."""
        original = Cycle(
            start_date=self.start_date,
            duration=self.duration,
            pregnancy_id="preg-789",
        )
        original.generate_days()
        restored = Cycle.from_dict(original.to_dict())
        
        self.assertEqual(restored.start_date, original.start_date)
        self.assertEqual(restored.duration, original.duration)
        self.assertEqual(restored.pregnancy_id, original.pregnancy_id)
        self.assertEqual(len(restored.days), len(original.days))


if __name__ == "__main__":
    unittest.main()