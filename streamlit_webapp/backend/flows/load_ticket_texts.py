from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.engine import Engine

from core.data_helpers import DataHelpers
from models.database_tables import ErrorCode, Ticket, TicketType


class LoadTicketTexts:
    class _Query:
        statement = (
            select(
                Ticket.ticket_id.label("id"),
                TicketType.ticket_type_name.label("ticket_type"),
                Ticket.ticket_description.label("description"),
                ErrorCode.category.label("error_category"),
            )
            .join(TicketType, TicketType.ticket_type_id == Ticket.ticket_type_id)
            .outerjoin(ErrorCode, ErrorCode.error_code == Ticket.error_code)
        )

    def run(self, engine: Engine) -> pd.DataFrame:
        return DataHelpers.load_dataframe(self._Query.statement, engine)
