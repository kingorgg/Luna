# main.py
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

import sys
import gi
from typing import Any, Callable, Iterable, Optional
from .constants import ColorSchemeMode

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw #type: ignore
from .window import LunaWindow

from gettext import gettext as _

class LunaApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, application_id: str, version: str) -> None:
        super().__init__(flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        
        self.application_id = application_id
        self.version = version
        self.settings = Gio.Settings.new(self.application_id)
        
        self.apply_color_scheme()
        
        self.settings.connect(
            "changed::color-scheme",
            lambda *_: self.apply_color_scheme(),
        )
        
        self.create_action('quit', lambda *_: self.quit(), ['<control>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)

    def do_activate(self) -> None:
        self.new_window()

    def new_window(self) -> None:
        win = LunaWindow(application=self)
        win.present()

    def on_about_action(self, *args: Any) -> None:
        """Callback for the app.about action."""
        about = Adw.AboutDialog(
            application_name='luna',
            application_icon=self.application_id,
            developer_name='Daniel Taylor',
            version=self.version,
            website="https://github.com/kingorgg/Luna",
            issue_url="https://github.com/kingorgg/Luna/issues",
            license_type=Gtk.License.GPL_3_0,
            comments=_("A simple utility to keep track of your menstrual cycle and to predict ovulation dates. Also helps track your estimated due date and trimester, if you are pregnant."), # type: ignore
            developers=['Daniel Taylor'],
            designers=["Daniel Taylor"],
            copyright='© 2025 Daniel Taylor',
            support_url="https://github.com/kingorgg/Luna/discussions",
        )
        
        about.set_translator_credits(_('translator-credits')) # type: ignore
        about.set_artists(["Daniel Taylor"])
        about.present(self.props.active_window)

    def on_preferences_action(self, *args: Any) -> None:
        """Callback for the app.preferences action."""
        preferences = Adw.PreferencesDialog()

        settings_page = Adw.PreferencesPage()
        settings_page.set_icon_name("applications-system-symbolic")
        preferences.add(settings_page)
        
        appearance_group = Adw.PreferencesGroup(title=_("Appearance"))
        settings_page.add(appearance_group)

        color_row = Adw.ComboRow(
            title=_("Colour Scheme"),
            subtitle=_("Choose light, dark, or follow system"), # type: ignore
            model=Gtk.StringList.new(["System", "Light", "Dark"])
        )
        appearance_group.add(color_row)

        # Bind GSettings <-> ComboRow
        self.settings.bind(
            "color-scheme",
            color_row,
            "selected",
            Gio.SettingsBindFlags.DEFAULT,
        )

        cycle_group = Adw.PreferencesGroup(title=_("Cycle Tracking")) # type: ignore
        settings_page.add(cycle_group)

        luteal_phase = Adw.SpinRow.new_with_range(9,16,1)
        luteal_phase.set_title(_("Luteal Phase Length (days)")) # type: ignore
        luteal_phase.set_value(14)
        luteal_phase.set_numeric(True)
        cycle_group.add(luteal_phase)

        cycle_length = Adw.SpinRow.new_with_range(21,35,1)
        cycle_length.set_title(_("Cycle Length (days)")) # type: ignore
        cycle_length.set_value(28)
        cycle_length.set_numeric(True)
        cycle_group.add(cycle_length)

        period_length = Adw.SpinRow.new_with_range(2, 8, 1)
        period_length.set_title(_("Period Length (days)")) # type: ignore
        period_length.set_value(5)
        period_length.set_numeric(True)
        cycle_group.add(period_length)

        self.settings.bind(
            "luteal-phase-length", luteal_phase, "value", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "cycle-length", cycle_length, "value", Gio.SettingsBindFlags.DEFAULT
        )
        self.settings.bind(
            "period-length", period_length, "value", Gio.SettingsBindFlags.DEFAULT
        )

        preferences.present(self.props.active_window)

    def create_action(
            self, 
            name: str, 
            callback: Callable[..., None], 
            shortcuts: Optional[Iterable[str]] = None
    ) -> None:
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)
            
    def apply_color_scheme(self):
        style = Adw.StyleManager.get_default()
        mode = self.settings.get_int("color-scheme")

        if mode == ColorSchemeMode.LIGHT:
            style.set_color_scheme(Adw.ColorScheme.FORCE_LIGHT)
        elif mode == ColorSchemeMode.DARK:
            style.set_color_scheme(Adw.ColorScheme.FORCE_DARK)
        else:
            style.set_color_scheme(Adw.ColorScheme.DEFAULT)


def main(version: str) -> int:
    """The application's entry point."""
    from .constants import APP_ID
    app = LunaApplication(application_id=APP_ID, version=version)
    return app.run(sys.argv)
