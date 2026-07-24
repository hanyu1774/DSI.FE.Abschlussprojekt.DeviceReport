from __future__ import annotations

from typing import Any

import pandas as pd

from core.data_helpers import DataHelpers

TICKET_COLUMNS = [
    "id", "ticket_type", "machine_id", "machine_name", "error_code",
    "error_description", "technician", "priority", "status", "description",
    "created_at", "assigned_at", "resolved_at", "closed_at", "resolution_hours",
]


class FilterTickets:
    def run(
        self,
        tickets_df: pd.DataFrame,
        machine_id: int | None = None,
        ticket_type: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        df: pd.DataFrame = tickets_df

        if machine_id is not None:
            df = df.loc[df["machine_id"] == machine_id]
        if ticket_type is not None:
            df = df.loc[df["ticket_type"] == ticket_type]
        if priority is not None:
            df = df.loc[df["priority"] == priority]
        if status is not None:
            df = df.loc[df["status"] == status]

        df = df.sort_values("created_at", ascending=False).head(limit)
        return DataHelpers.to_json_records(df, TICKET_COLUMNS)
