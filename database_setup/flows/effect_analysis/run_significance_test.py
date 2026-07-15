"""Flow: runs a t-test to check whether the before/after difference is statistically significant."""
from datetime import datetime, timedelta
from typing import Optional, cast

import pandas
from scipy import stats

from models.event import Event


class RunSignificanceTest:
    def run(self, events: list[Event], start_date: datetime) -> Optional[float]:
        error_events = [e for e in events if e.status == "error"]
        if not error_events:
            return None

        df = pandas.DataFrame([{"timestamp": e.timestamp} for e in error_events])
        before = df[df.timestamp < start_date]
        after = df[df.timestamp >= start_date]
        if before.empty or after.empty:
            return None

        daily_before = before.groupby(before.timestamp.dt.date).size()
        daily_after = after.groupby(after.timestamp.dt.date).size()

        date_range_before = [timestamp.date() for timestamp in
                              pandas.date_range(df.timestamp.min().date(), start_date.date() - timedelta(days=1))]
        date_range_after = [timestamp.date() for timestamp in
                             pandas.date_range(start_date.date(), df.timestamp.max().date())]
        if len(date_range_before) < 2 or len(date_range_after) < 2:
            return None

        series_before = daily_before.reindex(date_range_before, fill_value=0)
        series_after = daily_after.reindex(date_range_after, fill_value=0)

        significance_test_result = stats.ttest_ind(series_before, series_after, equal_var=False)
        p_value = cast(float, significance_test_result[1])
        return round(p_value, 5)
