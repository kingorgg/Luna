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

from datetime import date
from typing import List, Optional, Dict
import logging

from .models import Cycle, Pregnancy
from .storage import CycleStore, PregnancyStore
from .constants import APP_ID

from gi.repository import GObject  # type: ignore


class DataStore(GObject.GObject):

    __gsignals__ = {
        "changed": (GObject.SIGNAL_RUN_FIRST, None, ()),
    }

    def __init__(self) -> None:
        """Main data store managing cycles and pregnancies."""
        super().__init__()
        self.logger = logging.getLogger(__name__)

        self.cycles = CycleStore(app_id=APP_ID)
        self.pregnancies = PregnancyStore(app_id=APP_ID)

        self._restore_links()

    def _restore_links(self) -> None:
        """Restore links between cycles and pregnancies after loading from storage."""
        preg_dict: Dict[str, Pregnancy] = {
            preg.id: preg for preg in self.pregnancies.items
        }

        for cycle in self.cycles.items:
            if cycle.pregnancy_id:
                cycle.pregnancy = preg_dict.get(cycle.pregnancy_id, None)

    def _auto_link_all(self) -> None:
        """Automatically link all pregnancies to their appropriate cycles."""
        if not self.pregnancies.items or not self.cycles.items:
            return

        self.cycles.items.sort(key=lambda c: c.start_date)

        for cycle in self.cycles.items:
            cycle.pregnancy = None

        for preg in self.pregnancies.items:
            self._link_single_pregnancy(preg)

    def _link_single_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Link a single pregnancy to the appropriate cycle based on start dates."""
        if not self.cycles.items:
            return

        self.cycles.items.sort(key=lambda c: c.start_date)
        
        # link to the first cycle if pregnancy starts before it
        if pregnancy.start_date < self.cycles.items[0].start_date:
            self.cycles.items[0].pregnancy = pregnancy
            return

        for i, cycle in enumerate(self.cycles.items):
            start = cycle.start_date

            if i + 1 < len(self.cycles.items):
                end = self.cycles.items[i + 1].start_date
            else:
                end = date.today()

            if start <= pregnancy.start_date < end:
                self.logger.debug(
                    f"Linking pregnancy {pregnancy.start_date} to cycle {cycle.start_date}"
                )
                cycle.pregnancy = pregnancy
                return

    def get_cycles(self) -> List[Cycle]:
        """Return all stored cycles."""
        return self.cycles.items

    def get_active_cycle(self) -> Optional[Cycle]:
        """Return the most recent (active) cycle, or None if none exist."""
        try:
            return self.cycles.get_active_cycle()
        except ValueError:
            return None

    def add_cycle(self, cycle: Cycle) -> None:
        """Add a new cycle and update all links."""
        self.cycles.add_cycle(cycle)
        self._auto_link_all()

        # Persist links
        self.cycles.save()
        self.pregnancies.save()
        self.emit("changed")

    def delete_cycle(self, cycle: Cycle) -> None:
        """Delete a cycle and update all links."""
        self.cycles.delete_cycle(cycle)

        # After deleting a cycle, all pregnancy links may have changed
        self._auto_link_all()

        # Persist
        self.cycles.save()
        self.pregnancies.save()
        self.emit("changed")

    def get_pregnancies(self) -> List[Pregnancy]:
        """Return all stored pregnancies."""
        return self.pregnancies.items

    def get_active_pregnancy(self) -> Optional[Pregnancy]:
        """Return the currently active pregnancy, if any."""
        return self.pregnancies.get_active_pregnancy()

    def add_pregnancy(self, pregnancy: Pregnancy) -> None:
        """Add a new pregnancy and link it to the appropriate cycle."""
        self.pregnancies.add_pregnancy(pregnancy)
        self._link_single_pregnancy(pregnancy)

        # Persist links
        self.cycles.save()
        self.pregnancies.save()
        self.emit("changed")

    def save_all(self) -> None:
        """Persist all data to storage."""
        self.cycles.save()
        self.pregnancies.save()

    def reload(self) -> None:
        """Reload all data from storage."""
        self.cycles.load()
        self.pregnancies.load()
        self._restore_links()
