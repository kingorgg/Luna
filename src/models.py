# models.py
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

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class DayEntry:
    """Represents a single day in a menstrual cycle."""

    date: date
    symptoms: List[str] = field(default_factory=list)
    mood: Optional[str] = None
    temperature: Optional[float] = None
    flow: Optional[str] = None
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert this DayEntry instance into a serializable dictionary."""
        return {
            "date": self.date.isoformat(),
            "symptoms": list(self.symptoms),
            "mood": self.mood,
            "temperature": self.temperature,
            "flow": self.flow,
            "notes": self.notes,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> DayEntry:
        """Create a DayEntry instance from a dictionary representation."""
        return DayEntry(
            date=date.fromisoformat(data["date"]),
            symptoms=data.get("symptoms", []),
            mood=data.get("mood"),
            temperature=data.get("temperature"),
            flow=data.get("flow"),
            notes=data.get("notes"),
        )


@dataclass
class Pregnancy:
    """Represents a pregnancy event."""

    start_date: date
    confirmed: bool = True
    end_date: Optional[date] = None
    notes: Optional[str] = None
    custom_due_date: Optional[date] = None
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    @property
    def is_active(self) -> bool:
        """Check if the pregnancy is currently active (not ended)."""
        return self.end_date is None

    def to_dict(self) -> Dict[str, Any]:
        """Convert this Pregnancy instance into a serializable dictionary."""
        return {
            "id": self.id,
            "start_date": self.start_date.isoformat(),
            "confirmed": self.confirmed,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "notes": self.notes,
            "custom_due_date": (
                self.custom_due_date.isoformat() if self.custom_due_date else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Pregnancy":
        """Create a Pregnancy instance from a dictionary representation."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            start_date=date.fromisoformat(data["start_date"]),
            confirmed=data.get("confirmed", True),
            end_date=(
                date.fromisoformat(data["end_date"]) if data.get("end_date") else None
            ),
            notes=data.get("notes"),
            custom_due_date=(
                date.fromisoformat(data["custom_due_date"])
                if data.get("custom_due_date")
                else None
            ),
        )


@dataclass
class Cycle:
    """Represents a complete menstrual cycle and its tracked data."""

    start_date: date
    duration: int  # bleeding days
    pregnancy_id: Optional[str] = None  # link to pregnancy
    days: List[DayEntry] = field(default_factory=list)

    def generate_days(self):
        """Generate DayEntry objects for this cycle based on duration."""
        if not self.days:
            self.days = [
                DayEntry(date=self.start_date + timedelta(days=i))
                for i in range(self.duration)
            ]

    @property
    def pregnancy(self) -> Optional[Pregnancy]:
        """Get the linked Pregnancy object, if any."""
        return getattr(self, "_pregnancy_obj", None)

    @pregnancy.setter
    def pregnancy(self, value: Optional[Pregnancy]) -> None:
        """Set the linked Pregnancy object and update pregnancy_id."""
        self._pregnancy_obj = value
        self.pregnancy_id = value.id if value else None

    def to_dict(self) -> Dict[str, Any]:
        """Convert this Cycle instance into a serializable dictionary."""
        return {
            "start_date": self.start_date.isoformat(),
            "duration": self.duration,
            "pregnancy_id": self.pregnancy_id,
            "days": [day.to_dict() for day in self.days],
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> Cycle:
        """Create a Cycle instance from a dictionary representation."""
        return Cycle(
            start_date=date.fromisoformat(data["start_date"]),
            duration=data["duration"],
            pregnancy_id=data.get("pregnancy_id"),
            days=[DayEntry.from_dict(d) for d in data.get("days", [])],
        )
