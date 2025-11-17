# storage.py
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

import json
import gzip
import logging
import os
import fcntl
from pathlib import Path
from typing import List, Type, TypeVar, Optional

from .models import Cycle, Pregnancy

from gi.repository import GLib  # type: ignore

T = TypeVar("T")  # model type (Cycle, Pregnancy)


class BaseStore:
    """
    Generic JSON+GZip persistent store with atomic writes and flock locking.

    Subclasses only need to provide:
        - filename
        - model_class (Cycle or Pregnancy)
    """

    filename: str
    model_class: Type[T]

    def __init__(self, app_id: str) -> None:
        self.app_id = app_id
        self.items: List[T] = []

        self.logger = logging.getLogger(__name__)

        self.data_dir = Path(GLib.get_user_data_dir()) / app_id
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.file_path = self.data_dir / self.filename
        self.lock_path = self.data_dir / (self.filename + ".lock")

        self.load()

    def load(self) -> None:
        """Loads JSON data from a gzip file. Corrupt files return empty list."""
        self.items = []

        if not self.file_path.exists():
            return

        try:
            with gzip.open(self.file_path, "rt", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    self.items = [self.model_class.from_dict(x) for x in data]
                else:
                    self.logger.warning(f"Unexpected JSON format in {self.filename}")
        except Exception as e:
            self.logger.error(f"Failed to load {self.filename}: {e}")
            self.items = []

    def save(self) -> None:
        """Saves items atomically using flock + temp file + gzip."""
        tmp_path = self.file_path.with_name(self.file_path.name + ".tmp")

        with open(self.lock_path, "w") as lock_file:
            try:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)

                with gzip.open(tmp_path, "wt", encoding="utf-8") as f:
                    json.dump([item.to_dict() for item in self.items], f)

                os.replace(tmp_path, self.file_path)

            finally:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
                except Exception:
                    pass

    def add(self, item: T) -> None:
        self.items.append(item)
        self.save()


class CycleStore(BaseStore):
    """Handles persistent storage of Cycle objects as JSON."""

    filename = "cycles.json.gz"
    model_class = Cycle

    def add_cycle(self, cycle: Cycle) -> None:
        """Add a new cycle and persist it."""
        self.add(cycle)

    def delete_cycle(self, cycle: Cycle) -> None:
        """Delete a cycle and persist changes."""
        try:
            self.items.remove(cycle)
        except ValueError:
            self.logger.warning("Attempted to delete a cycle that does not exist")
            return

        self.save()

    def get_active_cycle(self) -> Optional[Cycle]:
        """Return the most recent (active) cycle."""
        if not self.items:
            return None
        return max(self.items, key=lambda c: c.start_date)

    def has_active_pregnancy(self) -> bool:
        """Return True if the active cycle has a linked pregnancy."""
        active_cycle = self.get_active_cycle()
        if not active_cycle:
            return False
        return active_cycle.pregnancy is not None

    def get_active_pregnancy(self) -> Optional[Pregnancy]:
        """Return the pregnancy linked to the active cycle, if any."""
        active_cycle = self.get_active_cycle()
        if not active_cycle:
            return None
        return active_cycle.pregnancy


class PregnancyStore(BaseStore):
    """Handles persistent storage of Pregnancy objects as JSON."""

    filename = "pregnancies.json.gz"
    model_class = Pregnancy

    def add_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Add a new pregnancy and persist it."""
        self.add(pregnancy)

    def get_active_pregnancy(self) -> Optional[Pregnancy]:
        """Return the currently active pregnancy, if any."""
        if not self.items:
            return None
        return self.items[-1]
