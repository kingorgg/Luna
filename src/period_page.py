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

from datetime import datetime, timedelta
from gettext import gettext as gettext_

from gi.repository import Adw, GObject, Gtk  # type: ignore

from .day_row import DayRow
from .delete_period_dialog import DeletePeriodDialog
from .models import Cycle, DayEntry, Pregnancy


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
        self.pregnancy_toggle.set_active(self.cycle.pregnancy is not None)

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
        try:
            new_start = datetime.strptime(self.start_date.get_text(), "%Y-%m-%d").date()
        except ValueError:
            toast = Adw.Toast.new(gettext_("Invalid date format"))
            self.get_native().toast_overlay.add_toast(toast)
            return

        self.cycle.start_date = new_start
        self.cycle.duration = int(self.duration.get_value())
        latest_cycle = self.store.get_active_cycle()

        if latest_cycle and self.cycle.id == latest_cycle.id:
            if self.pregnancy_toggle.get_active():
                if not self.cycle.pregnancy:
                    preg = Pregnancy(start_date=new_start)
                    self.store.add_pregnancy(preg)
                    self.cycle.pregnancy = preg
                else:
                    self.cycle.pregnancy.start_date = new_start
                    self.store.update_pregnancy(self.cycle.pregnancy)
            else:
                if self.cycle.pregnancy:
                    self.store.delete_pregnancy(self.cycle.pregnancy)
                self.cycle.pregnancy = None

        new_days = []
        for i, day in enumerate(self.days):
            row = self.days_list.get_row_at_index(i)

            day.flow = row.flow.get_model().get_string(row.flow.get_selected())
            day.mood = row.mood.get_model().get_string(row.mood.get_selected())
            t = row.temp.get_text().strip()
            day.temperature = float(t) if t else None
            sym = row.symptoms.get_text().strip()
            day.symptoms = [s.strip() for s in sym.split(",")] if sym else []
            day.notes = row.notes.get_text().strip() or None

            new_days.append(day)

        self.cycle.days = new_days

        if self.cycle.id is None:
            self.store.add_cycle(self.cycle)
        else:
            self.store.update_cycle(self.cycle)

        self.emit("period-edited", self.cycle)

        nav = self.get_ancestor(Adw.NavigationView)
        if nav:
            nav.pop()

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

        nav = self.get_ancestor(Adw.NavigationView)
        if nav:
            nav.pop()
