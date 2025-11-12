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

import json, gzip
from pathlib import Path
from typing import List
from .models import Cycle, CycleDict
import logging
import fcntl

from gi.repository import GLib # type: ignore

class CycleStore:
    """Handles persistent storage of Cycle objects as JSON."""
    
    path: Path
    cycles: List[Cycle]
    
    def __init__(self, app_id: str = "io.github.kingorgg.Luna") -> None:
        data_dir = Path(GLib.get_user_data_dir()) / app_id
        data_dir.mkdir(parents=True, exist_ok=True)
        self.path = data_dir / "cycles.json.gz"
        
        self.logger = logging.getLogger(__name__)
        
        self.cycles = []
        self.load()
        
    def load(self) -> None:
        """Load cycles from disk into memory. (compressed JSON)"""
        if not self.path.exists():
            self.cycles = []
            return

        try:
            with gzip.open(self.path, "rt", encoding="utf-8") as f:
                data: List[CycleDict] = json.load(f)
                self.cycles = [Cycle.from_dict(cycle_data) for cycle_data in data]
        except (json.JSONDecodeError, OSError) as e:
            self.logger.warning(f"Error loading cycles from {self.path}: {e}")
            self.cycles = []
            
    def save(self) -> None:
        """Save all cycles to disk as compressed JSON."""
        temp_path = self.path.with_suffix(".tmp")
        
        data: List[CycleDict] = [cycle.to_dict() for cycle in self.cycles]
        with gzip.open(temp_path, "wt", encoding="utf-8") as f:
            json.dump(data, f, separators=(",", ":"))
            f.flush()
            
            fd = f.fileno()
            try:
                import os
                os.fsync(fd)
            except OSError:
                pass
            
        with open(self.path, "a+") as lock_file:
            try:
                fcntl.flock(lock_file, fcntl.LOCK_EX)
                temp_path.replace(self.path)
            finally:
                fcntl.flock(lock_file, fcntl.LOCK_UN)
            
    def add_cycle(self, cycle: Cycle) -> None:
        """Add a new cycle and persist it."""
        self.cycles.append(cycle)
        self.save()
        
    def get_active_cycle(self) -> Cycle:
        """Return the most recent (active) cycle."""
        if not self.cycles:
            raise ValueError("No cycles available")
        return self.cycles[-1]