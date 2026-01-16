# data_store.py
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
import logging
from pathlib import Path
from typing import List, Optional

from gi.repository import GLib, GObject  # type: ignore

from .constants import APP_ID
from .models import Cycle, Pregnancy
from .sqlite_store import SQLiteStore


class DataStore(GObject.GObject):
    __gsignals__ = {
        "changed": (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self) -> None:
        """Main data store managing cycles and pregnancies."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.data_dir = Path(GLib.get_user_data_dir()) / APP_ID
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self.sqlite = SQLiteStore(app_id=APP_ID)

        if self._get_storage_version() != 3:
            self._set_storage_version(3)

    def close(self) -> None:
        """Close the SQLite connection."""
        if hasattr(self, "sqlite") and self.sqlite:
            self.sqlite.close()

    def get_cycles(self) -> List[Cycle]:
        """Return all stored cycles."""
        return self.sqlite.get_cycles()

    def get_active_cycle(self) -> Optional[Cycle]:
        """Return the most recent (active) cycle, or None if none exist."""
        try:
            return self.sqlite.get_active_cycle()
        except ValueError:
            return None

    def add_cycle(self, cycle: Cycle) -> None:
        """Add a new cycle and update all links."""
        self.sqlite.insert_cycle(cycle)
        self.emit("changed")

    def update_cycle(self, cycle: Cycle) -> None:
        """Update an existing cycle and update all links."""
        self.sqlite.update_cycle(cycle)
        self.emit("changed")

    def delete_cycle(self, cycle: Cycle) -> None:
        """Delete a cycle and update all links."""
        self.sqlite.delete_cycle(cycle)
        self.emit("changed")

    def get_pregnancies(self) -> List[Pregnancy]:
        """Return all stored pregnancies."""
        return self.sqlite.get_pregnancies()

    def get_active_pregnancy(self) -> Optional[Pregnancy]:
        """Return the currently active pregnancy, if any."""
        try:
            return self.sqlite.get_active_pregnancy()
        except ValueError:
            return None

    def add_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Add a new pregnancy and link it to the appropriate cycle."""
        self.sqlite.insert_pregnancy(pregnancy)
        self.emit("changed")

    def update_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Update an existing pregnancy and update all links."""
        self.sqlite.update_pregnancy(pregnancy)
        self.emit("changed")

    def delete_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Delete a pregnancy and update all links."""
        self.sqlite.delete_pregnancy(pregnancy)
        self.emit("changed")

    def save_all(self) -> None:
        """No-op: SQLite writes are immediate."""
        pass

    def reload(self) -> None:
        """Reload data from SQLite."""
        pass

    def _metadata_path(self) -> Path:
        return self.data_dir / "metadata.json"

    def _get_storage_version(self) -> int:
        path = self._metadata_path()
        if not path.exists():
            return 1
        return json.loads(path.read_text()).get("storage_version", 1)

    def _set_storage_version(self, version: int) -> None:
        self._metadata_path().write_text(json.dumps({"storage_version": version}))
