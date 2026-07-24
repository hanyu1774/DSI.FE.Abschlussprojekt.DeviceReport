from __future__ import annotations

from typing import Any

import pandas as pd


class ComputeTicketTrend:
    def run(self, tickets_df: pd.DataFrame, interval: str = "week") -> list[dict[str, Any]]:
        freq = {"day": "D", "week": "W-MON", "month": "MS"}.get(interval, "W-MON")

        grouped = (
            tickets_df.set_index("created_at")
            .groupby([pd.Grouper(freq=freq), "ticket_type"])
            .size()
            .unstack(fill_value=0)
        )
        for col in ("Incident", "Service Request"):
            if col not in grouped.columns:
                grouped[col] = 0

        grouped["total"] = grouped["Incident"] + grouped["Service Request"]
        grouped = grouped.reset_index().rename(
            columns={
                "created_at": "period",
                "Incident": "incident_count",
                "Service Request": "service_request_count",
            }
        )
        grouped["period"] = grouped["period"].dt.strftime("%Y-%m-%d")

        return grouped[["period", "incident_count", "service_request_count", "total"]].to_dict(orient="records")  # pyright: ignore[reportCallIssue] - same pandas-stubs gap as core/data_helpers.py
