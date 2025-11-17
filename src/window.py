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

import logging
from typing import Any, List
from datetime import date, timedelta
from gi.repository import Adw, Gtk, GLib  # type: ignore

from .logic import CycleStats
from .data_store import DataStore
from .models import Pregnancy, Cycle
from .new_period import NewPeriodPage
from .period_page import PeriodPage

from gettext import gettext as _

def get_gestation(preg):
    today = date.today()
    delta = today - preg.start_date
    weeks = delta.days // 7
    days = delta.days % 7
    return weeks, days

def get_due_date(preg):
    return preg.start_date + timedelta(days=280)


@Gtk.Template(resource_path='/io/github/kingorgg/Luna/window.ui')
class LunaWindow(Adw.ApplicationWindow):
    __gtype_name__ = 'LunaWindow'

    # Template children (auto-bound from UI)
    content_view: Adw.NavigationView = Gtk.Template.Child() # type: ignore
    predicted_period: Adw.ActionRow = Gtk.Template.Child()  # type: ignore
    ovulation: Adw.ActionRow = Gtk.Template.Child()  # type: ignore
    cycle_length: Adw.ActionRow = Gtk.Template.Child()  # type: ignore
    cycle_range: Adw.ActionRow = Gtk.Template.Child()  # type: ignore
    cycle_std_dev: Adw.ActionRow = Gtk.Template.Child()  # type: ignore
    history_group_main: Adw.PreferencesGroup = Gtk.Template.Child()  # type: ignore
    history_group: Adw.PreferencesGroup = Gtk.Template.Child()  # type: ignore
    history_box_main: Gtk.ListBox = Gtk.Template.Child()  # type: ignore
    history_box: Gtk.ListBox = Gtk.Template.Child()  # type: ignore
    history_stack: Gtk.Stack = Gtk.Template.Child()  # type: ignore
    new_period_button: Gtk.Button = Gtk.Template.Child()  # type: ignore
    toast_overlay: Adw.ToastOverlay = Gtk.Template.Child()  # type: ignore

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.settings = self.get_application().settings
        self.store = DataStore()
        self.logger = logging.getLogger(__name__)
        
        self.store.connect("changed", self._on_store_changed)

        GLib.idle_add(lambda: self.update_ui(refresh=True))


    def update_ui(self, refresh: bool = False) -> None:
        """Update the UI with current data and predictions."""
        if refresh:
            try:
                self.store.reload()
            except Exception as e:
                self.toast_overlay.add_toast(
                    Adw.Toast.new(_("Error reloading data.")) # type: ignore
                )
                self.logger.error(f"Error reloading data: {e}")
                return
        
        cycles = self.store.get_cycles()
        latest = self.store.get_active_cycle()

        if latest is None:
            return self._show_empty_state()

        if latest.pregnancy:
            return self._show_pregnancy_state(latest.pregnancy, cycles)

        return self._show_cycle_prediction_state(cycles)


    def populate_history_list(self, cycles: list) -> None:
        """Populate the History list with past cycles."""
        self.history_box.remove_all()

        if not cycles:
            self.history_stack.set_visible_child_name("empty")
            return

        self.history_stack.set_visible_child_name("history")

        for cycle in reversed(cycles):
            self.history_box.append(self.build_history_row(cycle))


    def build_history_row(self, cycle: Cycle) -> Adw.ActionRow:
        """Build a history row for a given cycle."""
        start_str = cycle.start_date.strftime("%Y-%m-%d")
        end_str = (cycle.start_date + timedelta(days=cycle.duration - 1)).strftime("%Y-%m-%d")

        subtitle = f"→ {end_str} ({cycle.duration} days)"
        if cycle.pregnancy:
            subtitle += " - Pregnancy started"

        row = Adw.ActionRow(title=start_str, subtitle=subtitle)
        row.set_activatable(False)
        
        # Add an edit button to the right
        edit_button = Gtk.Button(icon_name="go-next-symbolic")
        edit_button.set_tooltip_text(_("View Period"))  # type: ignore
        edit_button.set_valign(Gtk.Align.CENTER)
        edit_button.add_css_class("flat")
        edit_button.connect("clicked", self.on_view_period_clicked, cycle)

        row.add_suffix(edit_button)
        
        return row


    @Gtk.Template.Callback()
    def on_new_period_button_clicked(self, *_args: Any) -> None:
        """Handle user clicking 'Add New Period'."""       
        page = NewPeriodPage()
        page.connect("period-saved", self.on_period_saved)
        self.content_view.push(page)
    
    def on_view_period_clicked(self, button: Gtk.Button, cycle: Cycle) -> None:
        """Handle user clicking 'View Period' for a specific cycle."""
        page = PeriodPage(cycle)
        page.connect("period-edited", self.on_period_edited)
        page.connect("period-deleted", self.on_period_deleted)
        self.content_view.push(page)
    
    def on_period_saved(self, page: NewPeriodPage, new_cycle: Cycle) -> None:
        """Handle the 'period-saved' signal from NewPeriodPage."""
        new_cycle.generate_days()
        self.store.add_cycle(new_cycle)
        self.store.save_all()
        
        self.toast_overlay.add_toast(Adw.Toast.new(_("New period saved"))) # type: ignore
        
        self.update_ui()
        
    def on_period_edited(self, page, cycle):
        """Handle the 'period-edited' signal from PeriodPage."""
        self.store.save_all()
        self.update_ui()
        
    def on_period_deleted(self, page, cycle):
        """Handle the 'period-deleted' signal from PeriodPage."""
        self.toast_overlay.add_toast(Adw.Toast.new(_("Period deleted")))  # type: ignore
        self.update_ui(refresh=True)
        
    def _on_store_changed(self, *_):
        """Handle changes in the data store."""
        GLib.idle_add(lambda: self.update_ui(refresh=True))
        
    def _show_empty_state(self):
        """Show the empty state when no cycles are recorded."""
        self.history_stack.set_visible_child_name("empty")

        self.predicted_period.set_title(_("Next Period"))
        self.ovulation.set_title(_("Ovulation"))
        self.cycle_length.set_title(_("Average Length"))

        self.predicted_period.set_subtitle(_("No data yet"))
        self.ovulation.set_subtitle(_("No data yet"))
        self.cycle_length.set_subtitle("-")
        self.cycle_range.set_subtitle("-")
        self.cycle_std_dev.set_subtitle("-")

        self.cycle_range.set_visible(True)
        self.cycle_std_dev.set_visible(True)

        self.toast(_("Add your first period to see predictions."))
        
    def _show_pregnancy_state(self, pregnancy: Pregnancy, cycles: List[Cycle]) -> None:
        """Show pregnancy information and pause predictions."""
        weeks, days = get_gestation(pregnancy)
        due = get_due_date(pregnancy)

        self.predicted_period.set_title(_("Due Date"))
        self.predicted_period.set_subtitle(due.isoformat())

        self.ovulation.set_title(_("Pregnancy Progress"))
        self.ovulation.set_subtitle(f"{weeks} weeks, {days} days")

        self.cycle_length.set_title(_("Trimester"))
        if weeks < 13:
            tri = _("1st trimester")
        elif weeks < 27:
            tri = _("2nd trimester")
        else:
            tri = _("3rd trimester")
        self.cycle_length.set_subtitle(tri)

        # Hide stats irrelevant during pregnancy
        self.cycle_range.set_visible(False)
        self.cycle_std_dev.set_visible(False)

        self.populate_history_list(cycles)
        
    def _show_cycle_prediction_state(self, cycles):
        """Show predictions and statistics based on cycles."""
        stats = CycleStats(
            cycles=cycles,
            cycle_len=self.settings.get_int("cycle-length"),
            luteal_len=self.settings.get_int("luteal-phase-length"),
        )

        self.predicted_period.set_title(_("Next Period"))
        self.ovulation.set_title(_("Ovulation Date"))
        self.cycle_length.set_title(_("Average Length"))

        self.cycle_range.set_visible(True)
        self.cycle_std_dev.set_visible(True)

        avg = stats.average_cycle_length()
        std_dev = stats.cycle_length_std_dev()
        crange = stats.cycle_length_range()

        next_period = stats.predicted_next_period
        ovulation = stats.predicted_ovulation

        self.predicted_period.set_subtitle(
            next_period.isoformat() if next_period else _("Not Available")
        )
        self.ovulation.set_subtitle(
            ovulation.isoformat() if ovulation else _("Not Available")
        )

        self.cycle_length.set_subtitle(f"{avg:.1f} days")
        self.cycle_range.set_subtitle(crange)
        self.cycle_std_dev.set_subtitle(
            f"{std_dev:.1f} days" if std_dev > 0 else "-"
        )

        self.populate_history_list(cycles)


