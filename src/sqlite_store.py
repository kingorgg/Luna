# sqlite_store.py
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

import json
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import List, Optional

from gi.repository import GLib

from .models import Cycle, DayEntry, Pregnancy


class SQLiteStore:
    def __init__(self, app_id: str, db_path: Optional[str] = None):
        if db_path is None:
            data_dir = Path(GLib.get_user_data_dir()) / app_id
            data_dir.mkdir(parents=True, exist_ok=True)
            self.db_path = data_dir / "luna.db"
        else:
            self.db_path = Path(db_path)

        self.conn = sqlite3.connect(
            self.db_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES
        )

        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.execute("PRAGMA synchronous = NORMAL")

        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self._init_schema()

    def _init_schema(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_date TEXT UNIQUE NOT NULL,
                duration INTEGER NOT NULL,
                pregnancy_id TEXT
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS day_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cycle_id INTEGER NOT NULL,
                date TEXT NOT NULL,
                mood TEXT,
                temperature REAL,
                flow TEXT,
                notes TEXT,
                symptoms TEXT,
                FOREIGN KEY (cycle_id) REFERENCES cycles(id) ON DELETE CASCADE,
                UNIQUE (cycle_id, date)
            )
        """
        )

        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pregnancies (
                id TEXT PRIMARY KEY,
                start_date TEXT UNIQUE NOT NULL,
                confirmed INTEGER NOT NULL,
                end_date TEXT,
                notes TEXT,
                custom_due_date TEXT
            )
        """
        )

        self.conn.commit()

    @contextmanager
    def transaction(self):
        try:
            self.conn.execute("BEGIN TRANSACTION")
            yield
            self.conn.commit()
        except Exception:
            self.conn.rollback()
            raise

    def close(self) -> None:
        """Close the SQLite connection."""
        if hasattr(self, "conn") and self.conn:
            self.conn.close()

    def get_cycles(self) -> List[Cycle]:
        """Return all stored cycles."""
        self.cursor.execute("SELECT * FROM cycles")
        cycles = []

        for row in self.cursor.fetchall():
            cycle_id = row["id"]

            cycle = Cycle(
                id=cycle_id,
                start_date=date.fromisoformat(row["start_date"]),
                duration=row["duration"],
                pregnancy_id=row["pregnancy_id"],
                days=self._get_days_for_cycle(cycle_id),
            )
            cycles.append(cycle)

        self._link_pregnancies(cycles)
        return cycles

    def insert_cycle(self, cycle: Cycle) -> None:
        """Insert a new cycle into the database."""
        with self.transaction():
            self.cursor.execute(
                """
                INSERT INTO cycles
                (start_date, duration, pregnancy_id)
                VALUES (?, ?, ?)
                """,
                (
                    cycle.start_date.isoformat(),
                    cycle.duration,
                    cycle.pregnancy_id,
                ),
            )

            cycle.id = self.cursor.lastrowid
            self._insert_day_entries(cycle.id, cycle.days)

    def update_cycle(self, cycle: Cycle) -> None:
        """Update an existing cycle."""
        if cycle.id is None:
            raise ValueError("Cannot update cycle without ID")

        with self.transaction():
            self.cursor.execute(
                """
                UPDATE cycles
                SET start_date = ?, duration = ?, pregnancy_id = ?
                WHERE id = ?
                """,
                (
                    cycle.start_date.isoformat(),
                    cycle.duration,
                    cycle.pregnancy_id,
                    cycle.id,
                ),
            )

            # Replace days
            self.cursor.execute(
                "DELETE FROM day_entries WHERE cycle_id = ?",
                (cycle.id,),
            )
            self._insert_day_entries(cycle.id, cycle.days)

    def delete_cycle(self, cycle: Cycle) -> None:
        """Delete a cycle and its associated day entries."""
        if cycle.id is None:
            raise ValueError("Cannot delete cycle without ID")

        with self.transaction():
            self.cursor.execute(
                "DELETE FROM cycles WHERE id = ?",
                (cycle.id,),
            )

    def get_active_cycle(self) -> Optional[Cycle]:
        """Return the most recent (active) cycle, or None if none exist."""
        cycles = self.get_cycles()
        return cycles[-1] if cycles else None

    def get_pregnancies(self) -> List[Pregnancy]:
        """Return all stored pregnancies."""
        self.cursor.execute("SELECT * FROM pregnancies ORDER BY start_date")
        pregnancies = []

        for row in self.cursor.fetchall():
            pregnancy = Pregnancy(
                id=row["id"],
                start_date=date.fromisoformat(row["start_date"]),
                confirmed=row["confirmed"],
                end_date=(
                    date.fromisoformat(row["end_date"]) if row["end_date"] else None
                ),
                custom_due_date=(
                    date.fromisoformat(row["custom_due_date"])
                    if row["custom_due_date"]
                    else None
                ),
                notes=row["notes"],
            )
            pregnancies.append(pregnancy)
        return pregnancies

    def insert_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Insert a new pregnancy into the database."""
        with self.transaction():
            self.cursor.execute(
                """
                INSERT INTO pregnancies
                (id, start_date, confirmed, end_date, notes, custom_due_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    pregnancy.id,
                    pregnancy.start_date.isoformat(),
                    int(pregnancy.confirmed),
                    pregnancy.end_date.isoformat() if pregnancy.end_date else None,
                    pregnancy.notes,
                    (
                        pregnancy.custom_due_date.isoformat()
                        if pregnancy.custom_due_date
                        else None
                    ),
                ),
            )

    def update_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Update an existing pregnancy in the database."""
        with self.transaction():
            self.cursor.execute(
                """
                UPDATE pregnancies
                SET start_date = ?, confirmed = ?, end_date = ?, notes = ?, custom_due_date = ?
                WHERE id = ?
                """,
                (
                    pregnancy.start_date.isoformat(),
                    int(pregnancy.confirmed),
                    pregnancy.end_date.isoformat() if pregnancy.end_date else None,
                    pregnancy.notes,
                    (
                        pregnancy.custom_due_date.isoformat()
                        if pregnancy.custom_due_date
                        else None
                    ),
                    pregnancy.id,
                ),
            )

    def delete_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Delete a pregnancy."""
        with self.transaction():
            self.cursor.execute(
                "DELETE FROM pregnancies WHERE id = ?",
                (pregnancy.id,),
            )

    def get_active_pregnancy(self) -> Optional[Pregnancy]:
        """Return the most recent (active) pregnancy, or None if none exist."""
        pregnancies = self.get_pregnancies()
        return pregnancies[-1] if pregnancies else None

    def _get_days_for_cycle(self, cycle_id: str) -> List[DayEntry]:
        """Return all stored days for a given cycle."""
        self.cursor.execute(
            "SELECT * FROM day_entries WHERE cycle_id = ? ORDER BY date",
            (cycle_id,),
        )

        days = []
        for row in self.cursor.fetchall():
            days.append(
                DayEntry(
                    date=date.fromisoformat(row["date"]),
                    mood=row["mood"],
                    temperature=row["temperature"],
                    flow=row["flow"],
                    notes=row["notes"],
                    symptoms=json.loads(row["symptoms"]) if row["symptoms"] else [],
                )
            )

        return days

    def _insert_day_entries(self, cycle_id: int, days: List[DayEntry]) -> None:
        """Insert day entries into the database."""
        for day in days:
            self.cursor.execute(
                """
                INSERT INTO day_entries
                (cycle_id, date, mood, temperature, flow, notes, symptoms)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    cycle_id,
                    day.date.isoformat(),
                    day.mood,
                    day.temperature,
                    day.flow,
                    day.notes,
                    json.dumps(day.symptoms),
                ),
            )

    def _link_pregnancies(self, cycles: List[Cycle]) -> None:
        """Link pregnancies to cycles."""
        pregnancies = {p.id: p for p in self.get_pregnancies()}

        for cycle in cycles:
            if cycle.pregnancy_id:
                cycle.pregnancy = pregnancies.get(cycle.pregnancy_id)

    def _get_cycle_id(self, start_date: date) -> int:
        """Get the ID of a cycle by its start date."""
        self.cursor.execute(
            "SELECT id FROM cycles WHERE start_date = ?",
            (start_date.isoformat(),),
        )
        row = self.cursor.fetchone()
        if row is None:
            raise ValueError("Cycle not found")
        return row["id"]
