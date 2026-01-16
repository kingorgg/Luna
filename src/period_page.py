# period_page.py
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

from __future__ import annotations, print_function

from datetime import date as DateType
from datetime import datetime, timedelta
from gettext import gettext as gettext_
from typing import Optional

from gi.repository import Adw, GObject, Gtk  # type: ignore

from .day_row import DayRow
from .delete_period_dialog import DeletePeriodDialog
from .models import Cycle, DayEntry, Pregnancy


class _InvalidDueDate:
    __slots__ = ()


_INVALID_DUE_DATE = _InvalidDueDate()


@Gtk.Template(resource_path="/io/github/kingorgg/Luna/period_page.ui")
class PeriodPage(Adw.NavigationPage):
    __gtype_name__ = "PeriodPage"

    __gsignals__ = {
        "period-edited": (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
        "period-deleted": (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    }

    # Template children
    start_date: Adw.EntryRow = Gtk.Template.Child()
    duration: Adw.SpinRow = Gtk.Template.Child()
    pregnancy_toggle: Adw.SwitchRow = Gtk.Template.Child()
    edd_date: Adw.EntryRow = Gtk.Template.Child()

    days_list: Gtk.ListBox = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()
    delete_button: Gtk.Button = Gtk.Template.Child()

    def __init__(self, cycle: Cycle, **kwargs):
        super().__init__(**kwargs)
        self.cycle = cycle
        self.days = list(cycle.days)

        self.connect("map", self.on_map)

    def on_map(self, *_):
        self.store = self.get_root().store

        self.start_date.set_text(self.cycle.start_date.isoformat())
        self.duration.set_value(self.cycle.duration)

        pregnancy = self.cycle.pregnancy
        self.pregnancy_toggle.set_active(pregnancy is not None)

        if pregnancy and pregnancy.custom_due_date:
            self.edd_date.set_text(pregnancy.custom_due_date.isoformat())
        else:
            self.edd_date.set_text("")

        self.days = list(self.cycle.days)
        self.rebuild_days()

        self.duration.connect("changed", self.on_duration_changed)

    def rebuild_days(self):
        """Rebuild the list of day entries in the UI."""
        self.days_list.remove_all()

        for idx, day in enumerate(self.days):
            row = self.build_day_row(idx, day)
            self.days_list.append(row)

    def build_day_row(self, index: int, day: DayEntry) -> Adw.ExpanderRow:
        return DayRow(day)

    def on_duration_changed(self, spin: Adw.SpinRow):
        """Handle changes to the duration spin row."""
        new_len = int(spin.get_value())
        current_len = len(self.days)

        if new_len > current_len:
            start = self.cycle.start_date
            for i in range(current_len, new_len):
                self.days.append(DayEntry(date=start + timedelta(days=i)))
        elif new_len < current_len:
            self.days = self.days[:new_len]

        self.rebuild_days()

    @Gtk.Template.Callback()
    def on_save_button_clicked(self, *_):
        """Callback for the save button click event."""
        new_start = self._get_valid_start_date()
        if not new_start:
            return

        self._update_cycle_core(new_start)

        if not self._is_latest_cycle():
            return

        if not self._handle_pregnancy(new_start):
            return

        self._update_days()
        self._persist_cycle()
        self._finish_edit()

    @Gtk.Template.Callback()
    def on_delete_button_clicked(self, button: Gtk.Button) -> None:
        """Handle the delete button click event."""
        dialog = DeletePeriodDialog()
        dialog.connect("response", self._on_delete_dialog_response)
        dialog.present(self.get_root())

    def _on_delete_dialog_response(self, dialog, response):
        """Handle the response from the delete confirmation dialog."""
        if response != "delete":
            return

        self.store.delete_cycle(self.cycle)

        # Emit signal so the main window can refresh itself
        self.emit("period-deleted", self.cycle)

        self._pop_navigation()

    # === HELPERS ===

    def _show_toast(self, message: str) -> None:
        """Show a toast with the given message."""
        toast = Adw.Toast.new(message)
        self.get_native().toast_overlay.add_toast(toast)

    def _parse_date_or_toast(self, text: str, error_msg: str) -> Optional[DateType]:
        """Parse a date string or show a toast with an error message."""
        try:
            return datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            self._show_toast(error_msg)
            return None

    def _get_valid_date(
        self, text: str, error_msg: str, allow_empty=False
    ) -> Optional[DateType]:
        """Get a valid date."""
        text = text.strip()
        if allow_empty and not text:
            return None

        return self._parse_date_or_toast(text, error_msg)

    def _get_valid_start_date(self) -> Optional[DateType]:
        """Get a valid start date from the start date entry."""
        return self._get_valid_date(
            self.start_date.get_text(),
            gettext_("Invalid start date format"),
        )

    def _get_valid_due_date(self) -> Optional[DateType] | _InvalidDueDate:
        """Get a valid due date."""
        result = self._get_valid_date(
            self.edd_date.get_text(),
            gettext_("Invalid EDD format"),
            allow_empty=True,
        )

        return result if result is not None else _INVALID_DUE_DATE

    def _update_cycle_core(self, start_date: DateType) -> None:
        """Update the cycle core with the given start date."""
        self.cycle.start_date = start_date
        self.cycle.duration = int(self.duration.get_value())

    def _is_latest_cycle(self) -> bool:
        """Check if the current cycle is the latest one."""
        latest = self.store.get_active_cycle()
        return bool(latest and self.cycle.id == latest.id)

    def _handle_pregnancy(self, start_date: DateType) -> bool:
        """Handle pregnancy status."""
        if not self.pregnancy_toggle.get_active():
            return self._clear_pregnancy()

        return self._upsert_pregnancy(start_date)

    def _clear_pregnancy(self) -> bool:
        """Clear pregnancy status."""
        if self.cycle.pregnancy:
            self.store.delete_pregnancy(self.cycle.pregnancy)
        self.cycle.pregnancy = None
        return True

    def _upsert_pregnancy(self, start_date: DateType) -> bool:
        """Upsert pregnancy status."""
        pregnancy = self.cycle.pregnancy or self._create_pregnancy(start_date)
        pregnancy.start_date = start_date

        due_date = self._get_valid_due_date()
        if isinstance(due_date, _InvalidDueDate):
            return False

        pregnancy.custom_due_date = due_date
        self.store.update_pregnancy(pregnancy)
        return True

    def _create_pregnancy(self, start_date: DateType) -> Pregnancy:
        """Create a new pregnancy."""
        preg = Pregnancy(start_date=start_date)
        self.store.add_pregnancy(preg)
        self.cycle.pregnancy = preg
        return preg

    def _update_days(self) -> None:
        """Update the days in the cycle."""
        self.cycle.days = [
            self._read_day_row(i, day) for i, day in enumerate(self.days)
        ]

    def _read_day_row(self, index: int, day: DayEntry) -> DayEntry:
        """Read a day row."""
        row = self.days_list.get_row_at_index(index)

        day.flow = row.flow.get_model().get_string(row.flow.get_selected())
        day.mood = row.mood.get_model().get_string(row.mood.get_selected())

        temp = row.temp.get_text().strip()
        day.temperature = float(temp) if temp else None

        symptoms = row.symptoms.get_text().strip()
        day.symptoms = [s.strip() for s in symptoms.split(",")] if symptoms else []

        day.notes = row.notes.get_text().strip() or None

        return day

    def _persist_cycle(self) -> None:
        """Persist the cycle."""
        if self.cycle.id is None:
            self.store.add_cycle(self.cycle)
        else:
            self.store.update_cycle(self.cycle)

    def _pop_navigation(self) -> None:
        """Pop the navigation view."""
        nav = self.get_ancestor(Adw.NavigationView)
        if nav:
            nav.pop()

    def _finish_edit(self) -> None:
        """Finish editing the cycle."""
        self.emit("period-edited", self.cycle)

        self._pop_navigation()
