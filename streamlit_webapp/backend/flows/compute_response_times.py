from __future__ import annotations

from typing import Any

import pandas as pd

from models.ticket_status import TicketStatus


def _round_or_none(value: float) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 1)


class ComputeResponseTimes:
    def run(self, tickets_df: pd.DataFrame) -> dict[str, Any]:
        df = tickets_df.copy()
        df["time_to_assign_hours"] = (df["assigned_at"] - df["created_at"]).dt.total_seconds() / 3600
        df["time_to_resolve_hours"] = (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600
        df["time_to_close_hours"] = (df["closed_at"] - df["created_at"]).dt.total_seconds() / 3600

        def summarize(subset: pd.DataFrame, label: str) -> dict[str, Any]:
            return {
                "label": label,
                "avg_time_to_assign_hours": _round_or_none(subset.loc[:, "time_to_assign_hours"].mean()),
                "avg_time_to_resolve_hours": _round_or_none(subset.loc[:, "time_to_resolve_hours"].mean()),
                "avg_time_to_close_hours": _round_or_none(subset.loc[:, "time_to_close_hours"].mean()),
                "ticket_count": int(len(subset)),
            }

        overall = summarize(df, "Gesamt")
        by_priority = [summarize(group, str(priority)) for priority, group in df.groupby("priority")]
        by_priority.sort(key=lambda item: TicketStatus.PRIORITY_ORDER.get(item["label"], 99))

        return {"overall": overall, "by_priority": by_priority}
