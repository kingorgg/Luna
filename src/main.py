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

import sys
import gi

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Gio, Adw
from .window import LunaWindow


class LunaApplication(Adw.Application):
    """The main application singleton class."""

    def __init__(self, version):
        super().__init__(application_id='io.github.kingorgg.Luna',
                         flags=Gio.ApplicationFlags.DEFAULT_FLAGS)
        self.create_action('quit', lambda *_: self.quit(), ['<control>q'])
        self.create_action('about', self.on_about_action)
        self.create_action('preferences', self.on_preferences_action)
        self.version = version
        self.settings = Gio.Settings.new("io.github.kingorgg.Luna")

    def do_activate(self):
        self.new_window()

    def new_window(self):
        win = LunaWindow(application=self)
        win.present()

    def on_about_action(self, *args):
        """Callback for the app.about action."""
        about = Adw.AboutDialog(application_name='luna',
                                application_icon='io.github.kingorgg.Luna',
                                developer_name='Daniel Taylor',
                                version=self.version,
                                developers=['Daniel Taylor'],
                                copyright='© 2025 Daniel Taylor')
        # Translators: Replace "translator-credits" with your name/username, and optionally an email or URL.
        about.set_translator_credits(_('translator-credits'))
        about.present(self.props.active_window)

    def on_preferences_action(self, *args):
        """Callback for the app.preferences action."""
        preferences = Adw.PreferencesDialog()

        settings_page = Adw.PreferencesPage()
        settings_page.set_icon_name("applications-system-symbolic")
        preferences.add(settings_page)

        cycle_group = Adw.PreferencesGroup(title=_("Cycle Tracking"))
        settings_page.add(cycle_group)

        luteal_phase = Adw.SpinRow.new_with_range(9,16,1)
        luteal_phase.set_title(_("Luteal Phase Length (days)"))
        luteal_phase.set_value(14)
        luteal_phase.set_numeric(True)
        cycle_group.add(luteal_phase)

        cycle_length = Adw.SpinRow.new_with_range(21,35,1)
        cycle_length.set_title(_("Cycle Length (days)"))
        cycle_length.set_value(28)
        cycle_length.set_numeric(True)
        cycle_group.add(cycle_length)

        period_length = Adw.SpinRow.new_with_range(2, 8, 1)
        period_length.set_title(_("Period Length (days)"))
        period_length.set_value(5)
        period_length.set_numeric(True)
        cycle_group.add(period_length)

        self.settings.bind("luteal-phase-length", luteal_phase, "value", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("cycle-length", cycle_length, "value", Gio.SettingsBindFlags.DEFAULT)
        self.settings.bind("period-length", period_length, "value", Gio.SettingsBindFlags.DEFAULT)

        preferences.present(self.props.active_window)

    def create_action(self, name, callback, shortcuts=None):
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
        if shortcuts:
            self.set_accels_for_action(f"app.{name}", shortcuts)

def main(version):
    """The application's entry point."""
    app = LunaApplication(version)
    return app.run(sys.argv)
