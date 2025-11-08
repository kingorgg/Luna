# window.py
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

from gi.repository import Adw
from gi.repository import Gtk

@Gtk.Template(resource_path='/io/github/kingorgg/Luna/window.ui')
class LunaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'LunaWindow'

    predicted_period = Gtk.Template.Child()
    ovulation = Gtk.Template.Child()
    cycle_length = Gtk.Template.Child()
    cycle_range = Gtk.Template.Child()
    cycle_std_dev = Gtk.Template.Child()

    history_group_main = Gtk.Template.Child()
    history_box_main = Gtk.Template.Child()
    history_stack = Gtk.Template.Child()
    history_box = Gtk.Template.Child()
    history_group = Gtk.Template.Child()
    empty_history = Gtk.Template.Child()

    new_period_button = Gtk.Template.Child()

    main_content = Gtk.Template.Child()
    split_view = Gtk.Template.Child()
    toast_overlay = Gtk.Template.Child()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
