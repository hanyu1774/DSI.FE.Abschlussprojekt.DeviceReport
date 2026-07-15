"""Model: the result of the before/after effect calculation for a measure."""
from typing import Optional


class EffectResult:
    def __init__(self):
        self.incidents_per_month_before: float = 0.0
        self.incidents_per_month_after: float = 0.0
        self.incidents_change_percent: Optional[float] = None
        self.downtime_minutes_per_month_before: float = 0.0
        self.downtime_minutes_per_month_after: float = 0.0
        self.downtime_change_percent: Optional[float] = None
        self.t_test_p_value: Optional[float] = None
        self.is_significant_at_5_percent: bool = False
        self.note: Optional[str] = None   # set when there isn't enough data to compare
