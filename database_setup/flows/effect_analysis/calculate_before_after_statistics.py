"""Flow: calculates average incidents/month and average downtime/month before and after a date."""
from datetime import datetime

import pandas as pd

from models.event import Event
from models.effect_result import EffectResult


class CalculateBeforeAfterStatistics:
    def run(self, events: list[Event], start_date: datetime) -> EffectResult:
        result = EffectResult()

        error_events = [e for e in events if e.status == "error"]
        if not error_events:
            result.note = "No error events available for this machine."
            return result

        df = pd.DataFrame([{"timestamp": e.timestamp, "downtime": e.downtime_minutes or 0.0}
                            for e in error_events])

        before = df[df.timestamp < start_date]
        after = df[df.timestamp >= start_date]
        if before.empty or after.empty:
            result.note = "Not enough data before or after the start date for a comparison."
            return result

        days_before = max((start_date - df.timestamp.min()).days, 1)
        days_after = max((df.timestamp.max() - start_date).days, 1)

        result.incidents_per_month_before = round(len(before) / days_before * 30, 2)
        result.incidents_per_month_after = round(len(after) / days_after * 30, 2)
        if result.incidents_per_month_before:
            result.incidents_change_percent = round(
                (result.incidents_per_month_after - result.incidents_per_month_before)
                / result.incidents_per_month_before * 100, 1)

        result.downtime_minutes_per_month_before = round(before.downtime.sum() / days_before * 30, 1)
        result.downtime_minutes_per_month_after = round(after.downtime.sum() / days_after * 30, 1)
        if result.downtime_minutes_per_month_before:
            result.downtime_change_percent = round(
                (result.downtime_minutes_per_month_after - result.downtime_minutes_per_month_before)
                / result.downtime_minutes_per_month_before * 100, 1)

        return result
