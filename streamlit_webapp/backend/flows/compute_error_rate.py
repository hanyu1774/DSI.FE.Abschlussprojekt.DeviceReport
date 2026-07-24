from __future__ import annotations

from typing import Any

import pandas as pd

from core.data_helpers import DataHelpers


class ComputeErrorRate:
    def run(self, events_df: pd.DataFrame) -> list[dict[str, Any]]:
        counts = events_df.pivot_table(
            index=["machine_id", "machine_name"],
            columns="status",
            values="timestamp",
            aggfunc="count",
            fill_value=0,
        )
        for status_col, out_col in (
            ("error", "error_count"),
            ("maintenance", "maintenance_count"),
            ("offline", "offline_count"),
        ):
            counts[out_col] = counts[status_col] if status_col in counts.columns else 0

        downtime = (
            events_df.groupby(["machine_id", "machine_name"])["downtime_minutes"]
            .sum()
            .rename("total_downtime_minutes")  # pyright: ignore[reportCallIssue, reportAttributeAccessIssue, reportArgumentType] - pandas-stubs can't narrow groupby().sum()'s return past a huge scalar union; it's always a Series here
        )

        result = counts.join(downtime).reset_index()
        result["total_downtime_minutes"] = result["total_downtime_minutes"].round(1)
        result = result.sort_values("error_count", ascending=False)

        columns = [
            "machine_id", "machine_name", "error_count",
            "maintenance_count", "offline_count", "total_downtime_minutes",
        ]
        return DataHelpers.to_json_records(result, columns)
