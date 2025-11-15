# logic.py
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
import statistics
from datetime import date, timedelta
from typing import List, Optional
from .models import Cycle

class CycleStats:
    """
    Compute statistics and predictions for menstrual cycles
    """

    def __init__(self, cycles: List[Cycle], cycle_len: int, luteal_len: int) -> None:
        self.cycles = [c for c in cycles if not c.pregnancy]
        self.cycle_len = cycle_len
        self.luteal_len = luteal_len
        
    @property
    def intervals(self) -> List[int]:
        """Calculate the list of cycle lengths in days."""
        if len(self.cycles) < 2:
            return []
        return [
            (self.cycles[i + 1].start_date - self.cycles[i].start_date).days
            for i in range(len(self.cycles) - 1)
        ]

    def average_cycle_length(self) -> float:
        """Calculate the average cycle length."""
        if not self.intervals:
            return float(self.cycle_len)
        return statistics.mean(self.intervals)
    
    def cycle_length_std_dev(self) -> float:
        """Calculate the standard deviation of cycle lengths."""
        if len(self.intervals) < 2:
            return 0.0
        return statistics.stdev(self.intervals)
    
    def cycle_length_range(self) -> str:
        """Calculate the min and max cycle lengths."""
        if not self.intervals:
            return "-"
        return f"{min(self.intervals)}-{max(self.intervals)} days"
    
    @property
    def predicted_next_period(self) -> Optional[date]:
        """Predict the next period start date."""
        if not self.cycles:
            return None
        last_cycle = self.cycles[-1]
        avg_length = self.average_cycle_length() or self.cycle_len
        return last_cycle.start_date + timedelta(days=int(avg_length))
    
    @property
    def predicted_ovulation(self) -> Optional[date]:
        """Predict the next ovulation date."""
        next_period = self.predicted_next_period
        if not next_period:
            return None
        return next_period - timedelta(days=self.luteal_len)