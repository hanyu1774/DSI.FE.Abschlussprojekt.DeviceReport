from __future__ import annotations

import numpy as np
import pandas as pd

from models.ticket_status import TicketStatus


class EnrichTickets:
    def run(self, tickets_df: pd.DataFrame) -> pd.DataFrame:
        df = tickets_df.copy()

        technician = (
            df["technician_first_name"].fillna("") + " " + df["technician_last_name"].fillna("")
        ).str.strip()
        df["technician"] = technician.replace("", None)
        df = df.drop(columns=["technician_first_name", "technician_last_name"])

        # Status wird aus den vorhandenen Zeitstempeln abgeleitet (siehe die
        # CHECK-Constraints der Tabelle: created <= assigned <= resolved <= closed).
        conditions = [df["closed_at"].notna(), df["resolved_at"].notna(), df["assigned_at"].notna()]
        choices = [TicketStatus.CLOSED, TicketStatus.RESOLVED, TicketStatus.IN_PROGRESS]
        df["status"] = np.select(conditions, choices, default=TicketStatus.OPEN)

        df["resolution_hours"] = (
            (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600
        ).round(1)

        return df
