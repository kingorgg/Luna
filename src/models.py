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

from dataclasses import dataclass, field
from typing import Optional, List, Mapping, Any, TypedDict
from datetime import date, timedelta


class DayEntryDict(TypedDict, total=False):
    """Dictionary representation of a DayEntry, used for serialization."""
    date: str
    symptoms: List[str]
    mood: Optional[str]
    temperature: Optional[float]
    flow: Optional[str]
    notes: Optional[str]
    
class CycleDict(TypedDict):
    """Dictionary representation of a Cycle, used for serialization."""
    start_date: str
    duration: int
    days: List[DayEntryDict]
    


@dataclass
class DayEntry:
    """Represents a single day in a menstrual cycle."""
    date: date
    symptoms: List[str] = field(default_factory=list)
    mood: Optional[str] = None
    temperature: Optional[float] = None
    flow: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> DayEntryDict:
        """Convert this DayEntry instance into a serializable dictionary."""
        return {
            "date": self.date.isoformat(),
            "symptoms": list(self.symptoms),
            "mood": self.mood,
            "temperature": self.temperature,
            "flow": self.flow,
            "notes": self.notes,
        }


@dataclass
class Cycle:
    """Represents a complete menstrual cycle and its tracked data."""
    start_date: date
    duration: int
    days: List[DayEntry] = field(default_factory=list)
       
    def generate_days(self) -> None:
        """Generate DayEntry objects for this cycle based on duration."""
        self.days = [
            DayEntry(date=self.start_date + timedelta(days=i))
            for i in range(self.duration or 0)
        ]
        
    def to_dict(self) -> CycleDict:
        """Convert this Cycle instance into a serializable dictionary."""
        return {
            "start_date": self.start_date.isoformat(),
            "duration": self.duration,
            "days": [day.to_dict() for day in self.days],
        }
        
    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> Cycle:
        """Create a Cycle instance from a dictionary representation."""
        cycle = cls(
            start_date=date.fromisoformat(data["start_date"]),
            duration=data["duration"],
        )
        cycle.days = [
            DayEntry(
                date=date.fromisoformat(day_data["date"]),
                symptoms=day_data.get("symptoms", []),
                mood=day_data.get("mood"),
                temperature=day_data.get("temperature"),
                flow=day_data.get("flow"),
                notes=day_data.get("notes"),
            )
            for day_data in data.get("days", [])
        ]
        return cycle