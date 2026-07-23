from __future__ import annotations

from typing import Any

import pandas as pd

from core.data_helpers import DataHelpers


class ComputeAvailability:
    def run(self, events_df: pd.DataFrame) -> list[dict[str, Any]]:
        """Verfuegbarkeit = 1 - (Stillstand durch 'error' + 'offline') / Gesamtzeitraum.
        Geplante Wartung ('maintenance') zaehlt nicht als Verfuegbarkeitsverlust."""
        if events_df.empty:
            return []

        period_minutes = (events_df["timestamp"].max() - events_df["timestamp"].min()).total_seconds() / 60
        period_days = round(period_minutes / (60 * 24), 1)

        unavailable = (
            events_df[events_df["status"].isin(["error", "offline"])]
            .groupby(["machine_id", "machine_name"])["downtime_minutes"]
            .sum()
            .rename("downtime_minutes")  # pyright: ignore[reportCallIssue, reportAttributeAccessIssue, reportArgumentType] - same pandas-stubs gap as compute_error_rate.py
            .reset_index()
        )

        machines = events_df[["machine_id", "machine_name"]].drop_duplicates()
        merged = machines.merge(unavailable, on=["machine_id", "machine_name"], how="left")
        merged["downtime_minutes"] = merged["downtime_minutes"].fillna(0.0).round(1)
        merged["availability_percent"] = (
            100 * (1 - merged["downtime_minutes"] / period_minutes)
        ).clip(lower=0, upper=100).round(2)
        merged["period_days"] = period_days

        merged = merged.sort_values("availability_percent")
        columns = ["machine_id", "machine_name", "availability_percent", "downtime_minutes", "period_days"]
        return DataHelpers.to_json_records(merged, columns)
