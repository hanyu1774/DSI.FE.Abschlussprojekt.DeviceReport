from __future__ import annotations

from typing import Any

import pandas as pd

from models.ticket_status import TicketStatus


class SummarizeTickets:
    def run(self, tickets_df: pd.DataFrame) -> dict[str, Any]:
        df: pd.DataFrame = tickets_df

        def value_counts_list(series: pd.Series) -> list[dict[str, Any]]:
            return [{"name": str(name), "count": int(count)} for name, count in series.value_counts().items()]

        category_series = df.loc[:, "error_category"].fillna("Ohne Fehlercode")

        return {
            "total": int(len(df)),
            "open_count": int((df["status"] != TicketStatus.CLOSED).sum()),
            "critical_count": int((df["priority"] == "critical").sum()),
            "by_type": value_counts_list(df.loc[:, "ticket_type"]),
            "by_priority": sorted(
                value_counts_list(df.loc[:, "priority"]),
                key=lambda item: TicketStatus.PRIORITY_ORDER.get(item["name"], 99),
            ),
            "by_status": value_counts_list(df.loc[:, "status"]),
            "by_category": value_counts_list(category_series),
        }
