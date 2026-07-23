from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.engine import Engine

from core.data_helpers import DataHelpers
from models.database_tables import ErrorCode, Machine, Technician, Ticket, TicketType


class LoadTickets:
    class _Query:
        statement = (
            select(
                Ticket.ticket_id.label("id"),
                TicketType.ticket_type_name.label("ticket_type"),
                Ticket.machine_id,
                Machine.machine_name.label("machine_name"),
                Ticket.error_code,
                ErrorCode.error_code_description.label("error_description"),
                ErrorCode.category.label("error_category"),
                Technician.first_name.label("technician_first_name"),
                Technician.last_name.label("technician_last_name"),
                Ticket.priority,
                Ticket.ticket_description.label("description"),
                Ticket.created_at,
                Ticket.assigned_at,
                Ticket.resolved_at,
                Ticket.closed_at,
            )
            .join(TicketType, TicketType.ticket_type_id == Ticket.ticket_type_id)
            .join(Machine, Machine.machine_id == Ticket.machine_id)
            .outerjoin(ErrorCode, ErrorCode.error_code == Ticket.error_code)
            .outerjoin(Technician, Technician.technician_id == Ticket.technician_id)
        )

    def run(self, engine: Engine) -> pd.DataFrame:
        df = DataHelpers.load_dataframe(self._Query.statement, engine)
        for col in ("created_at", "assigned_at", "resolved_at", "closed_at"):
            df[col] = pd.to_datetime(df[col])
        return df
