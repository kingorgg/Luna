# new_period.py
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

from datetime import datetime
from gettext import gettext as _

from gi.repository import Adw, GLib, GObject, Gtk  # type: ignore

from .models import Cycle


@Gtk.Template(resource_path="/io/github/kingorgg/Luna/new_period.ui")
class NewPeriodPage(Adw.NavigationPage):
    __gtype_name__ = "NewPeriodPage"

    __gsignals__ = {
        # The signal will be emitted after a period is successfully saved
        "period-saved": (GObject.SIGNAL_RUN_FIRST, None, (GObject.TYPE_PYOBJECT,)),
    }

    # Template children (auto-bound from UI)
    start_date: Adw.EntryRow = Gtk.Template.Child()  # type: ignore
    duration: Adw.SpinRow = Gtk.Template.Child()  # type: ignore
    save_button: Gtk.Button = Gtk.Template.Child()  # type: ignore

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.connect("map", self.on_map)

    def on_map(self, widget: Adw.NavigationPage) -> None:
        app = self.get_root().get_application()
        self.settings = app.settings

        default_period_len = self.settings.get_int("period-length")

        now = GLib.DateTime.new_now_local()
        self.start_date.set_text(now.format("%Y-%m-%d"))
        self.duration.set_value(default_period_len)

    @Gtk.Template.Callback()
    def on_save_button_clicked(self, button: Gtk.Button) -> None:
        """Callback for the save button click event."""
        # Implement saving logic here
        start_date_str = self.start_date.get_text()
        duration = int(self.duration.get_value())

        try:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
        except ValueError:
            toast_overlay = self.get_root().get_content()
            toast = Adw.Toast.new(_("Invalid date format (use YYYY-MM-DD)"))
            toast_overlay.add_toast(toast)
            return

        new_cycle = Cycle(start_date=start_date, duration=duration)
        self.emit("period-saved", new_cycle)

        navigation_view = self.get_parent()
        if isinstance(navigation_view, Adw.NavigationView):
            navigation_view.pop()
