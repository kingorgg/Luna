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

from __future__ import annotations
from typing import Any
from gi.repository import Adw, Gtk # type: ignore

@Gtk.Template(resource_path='/io/github/kingorgg/Luna/window.ui')
class LunaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'LunaWindow'

    # Template children (GTK widgets defined in window.ui)
    predicted_period: Gtk.Widget = Gtk.Template.Child() # type: ignore
    ovulation: Gtk.Widget = Gtk.Template.Child() # type: ignore
    cycle_length: Gtk.Widget = Gtk.Template.Child() # type: ignore
    cycle_range: Gtk.Widget = Gtk.Template.Child() # type: ignore
    cycle_std_dev: Gtk.Widget = Gtk.Template.Child() # type: ignore
    history_group_main: Gtk.Widget = Gtk.Template.Child() # type: ignore
    history_box_main: Gtk.Widget = Gtk.Template.Child() # type: ignore
    history_stack: Gtk.Widget = Gtk.Template.Child() # type: ignore
    history_box: Gtk.Widget = Gtk.Template.Child() # type: ignore
    history_group: Gtk.Widget = Gtk.Template.Child() # type: ignore
    empty_history: Gtk.Widget = Gtk.Template.Child() # type: ignore
    new_period_button: Gtk.Widget = Gtk.Template.Child() # type: ignore
    main_content: Gtk.Widget = Gtk.Template.Child() # type: ignore
    split_view: Gtk.Widget = Gtk.Template.Child() # type: ignore
    toast_overlay: Gtk.Widget = Gtk.Template.Child() # type: ignore

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
