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

from __future__ import annotations
from gi.repository import Adw, Gtk, GObject
from datetime import datetime, timedelta

from .models import Cycle, DayEntry, Pregnancy

from gettext import gettext as _

@Gtk.Template(resource_path="/io/github/kingorgg/Luna/period_page.ui")
class PeriodPage(Adw.NavigationPage):
    __gtype_name__ = "PeriodPage"

    __gsignals__ = {
        "period-edited": (
            GObject.SIGNAL_RUN_FIRST,
            None,
            (GObject.TYPE_PYOBJECT,)
        ),
        "period-deleted": (
            GObject.SIGNAL_RUN_FIRST,
            None,
            (GObject.TYPE_PYOBJECT,)
        ),
    }

    # Template children
    start_date: Adw.EntryRow = Gtk.Template.Child()
    duration: Adw.SpinRow = Gtk.Template.Child()
    pregnancy_toggle: Adw.SwitchRow = Gtk.Template.Child()

    days_list: Gtk.ListBox = Gtk.Template.Child()
    save_button: Gtk.Button = Gtk.Template.Child()

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
        """Build a single day entry row."""
        expander = Adw.ExpanderRow(
            title=day.date.isoformat(),
            subtitle="Day details"
        )

        flow = Adw.ComboRow()
        flow.set_title("Flow")
        flow.options = ["None", "Light", "Medium", "Heavy"]
        model = Gtk.StringList.new(flow.options)
        flow.set_model(model)
        
        if day.flow in flow.options:
            flow.set_selected(flow.options.index(day.flow))
        else:
            flow.set_selected(0)
        
        expander.add_row(flow)

        mood = Adw.EntryRow()
        mood.set_title("Mood")
        mood.set_text(day.mood or "")
        expander.add_row(mood)

        temp = Adw.EntryRow()
        temp.set_title("Temperature (°C)")
        temp.set_input_purpose(Gtk.InputPurpose.NUMBER)
        temp.set_text("" if day.temperature is None else str(day.temperature))
        expander.add_row(temp)

        symptoms = Adw.EntryRow()
        symptoms.set_title("Symptoms (comma-separated)")
        symptoms.set_text(", ".join(day.symptoms))
        expander.add_row(symptoms)

        notes = Adw.EntryRow()
        notes.set_title("Notes")
        notes.set_text(day.notes or "")
        expander.add_row(notes)

        expander.day_widgets = {
            "flow": flow,
            "mood": mood,
            "temp": temp,
            "symptoms": symptoms,
            "notes": notes,
        }

        return expander


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
            new_start = datetime.strptime(
                self.start_date.get_text(), "%Y-%m-%d"
            ).date()
        except ValueError:
            toast = Adw.Toast.new("Invalid date format")

            window = self.get_native()
            window.toast_overlay.add_toast(toast)
            return

        self.cycle.start_date = new_start
        self.cycle.duration = int(self.duration.get_value())
        
        latest_cycle = self.store.get_active_cycle()

        if self.cycle is not latest_cycle:
            # If editing an older cycle, force pregnancy OFF
            self.cycle.pregnancy = None
            self.cycle.pregnancy_id = None
        else:
            # Editing latest cycle normally
            if self.pregnancy_toggle.get_active():

                # Create pregnancy if none exists
                if not self.cycle.pregnancy:
                    preg = Pregnancy(start_date=new_start)
                    self.cycle.pregnancy = preg
                    self.store.add_pregnancy(preg)

                # If pregnancy already exists, update start date
                else:
                    self.cycle.pregnancy.start_date = new_start
                    self.store.pregnancies.save()

            else:
                # Toggle off on latest cycle → remove pregnancy
                self.cycle.pregnancy = None
                self.cycle.pregnancy_id = None

        new_days = []
        for expander, day in zip(self.days_list, self.days):
            widget = expander.day_widgets

            flow_row = widget["flow"]
            model = flow_row.get_model()
            idx = flow_row.get_selected()

            day.flow = model.get_string(idx) if idx >= 0 else None
            day.mood = widget["mood"].get_text() or None

            t = widget["temp"].get_text().strip()
            day.temperature = float(t) if t else None

            sym = widget["symptoms"].get_text().strip()
            day.symptoms = [s.strip() for s in sym.split(",")] if sym else []

            day.notes = widget["notes"].get_text().strip() or None

            new_days.append(day)

        self.cycle.days = new_days

        self.emit("period-edited", self.cycle)

        nav = self.get_ancestor(Adw.NavigationView)
        if nav:
            nav.pop()


    @Gtk.Template.Callback()
    def on_delete_button_clicked(self, button: Gtk.Button) -> None:
        """Handle the delete button click event."""
        dialog = Adw.AlertDialog.new()
        dialog.set_heading(_("Delete Period")) # type: ignore
        dialog.set_body(_("Are you sure you want to delete this period? This action cannot be undone.")) # type: ignore
        
        dialog.add_response("cancel", _("Cancel")) # type: ignore
        dialog.add_response("delete", _("Delete")) # type: ignore
        
        dialog.set_response_appearance(
            "delete", 
            Adw.ResponseAppearance.DESTRUCTIVE
        )
        
        dialog.set_default_response("cancel")
        dialog.set_close_response("cancel")

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


