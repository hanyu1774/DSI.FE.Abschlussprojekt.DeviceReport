from __future__ import annotations

from typing import Any

import pandas as pd

from core.data_helpers import DataHelpers


class ComputeMttrMtbf:
    def run(self, events_df: pd.DataFrame) -> list[dict[str, Any]]:
        """MTTR (mittlere Reparaturzeit) und MTBF (mittlere Zeit zwischen
        Ausfaellen) je Maschine, jeweils basierend auf 'error'-Events."""
        if events_df.empty:
            return []

        period_hours = (events_df["timestamp"].max() - events_df["timestamp"].min()).total_seconds() / 3600
        errors = events_df[events_df["status"] == "error"]

        failure_count = errors.groupby(["machine_id", "machine_name"]).size().rename("failure_count")  # pyright: ignore[reportCallIssue, reportArgumentType] - same pandas-stubs gap as compute_error_rate.py
        mttr = errors.groupby(["machine_id", "machine_name"])["downtime_minutes"].mean().rename("mttr_minutes")  # pyright: ignore[reportCallIssue, reportAttributeAccessIssue, reportArgumentType] - same pandas-stubs gap

        machines = events_df[["machine_id", "machine_name"]].drop_duplicates().set_index(["machine_id", "machine_name"])
        result = machines.join(failure_count).join(mttr).reset_index()
        result["failure_count"] = result["failure_count"].fillna(0).astype(int)
        result["mttr_minutes"] = result["mttr_minutes"].round(1)
        result["mtbf_hours"] = result["failure_count"].apply(
            lambda n: round(period_hours / n, 1) if n > 0 else None
        )

        result = result.sort_values("failure_count", ascending=False)
        columns = ["machine_id", "machine_name", "failure_count", "mttr_minutes", "mtbf_hours"]
        return DataHelpers.to_json_records(result, columns)
