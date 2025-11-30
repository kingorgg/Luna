# day_row.py
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

from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gtk  # type: ignore


@Gtk.Template(resource_path="/io/github/kingorgg/Luna/day_row.ui")
class DayRow(Adw.ExpanderRow):
    __gtype_name__ = "DayRow"

    # Children from template
    flow: Adw.ComboRow = Gtk.Template.Child()
    mood: Adw.ComboRow = Gtk.Template.Child()
    temp: Adw.EntryRow = Gtk.Template.Child()
    symptoms: Adw.EntryRow = Gtk.Template.Child()
    notes: Adw.EntryRow = Gtk.Template.Child()

    def __init__(self, day, **kwargs):
        super().__init__(**kwargs)
        self.day = day
        self.set_title(self.day.date.isoformat())

        # Fill rows with data
        self._init_flow()
        self._init_mood()

        self.temp.set_text("" if day.temperature is None else str(day.temperature))
        self.symptoms.set_text(", ".join(day.symptoms))
        self.notes.set_text(day.notes or "")

    def _init_flow(self):
        options = [
            _("None"),
            _("Light"),
            _("Medium"),
            _("Heavy"),
        ]
        model = Gtk.StringList.new(options)
        self.flow.set_model(model)

        if self.day.flow in options:
            self.flow.set_selected(options.index(self.day.flow))
        else:
            self.flow.set_selected(0)

    def _init_mood(self):
        options = [
            _("Neutral"),
            _("Calm"),
            _("Sad"),
            _("Irritable"),
            _("Tired"),
            _("Sensitive"),
        ]
        model = Gtk.StringList.new(options)
        self.mood.set_model(model)

        if self.day.mood in options:
            self.mood.set_selected(options.index(self.day.mood))
        else:
            self.mood.set_selected(0)
