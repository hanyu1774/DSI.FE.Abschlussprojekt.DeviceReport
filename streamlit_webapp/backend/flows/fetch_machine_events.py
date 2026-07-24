from __future__ import annotations

from typing import Sequence

from sqlalchemy import RowMapping, select
from sqlalchemy.orm import Session

from models.database_tables import ErrorCode as ErrorCodeModel
from models.database_tables import EventLog


class FetchMachineEvents:
    def run(
        self,
        session: Session,
        machine_id: int,
        start: str | None = None,
        end: str | None = None,
    ) -> Sequence[RowMapping]:
        statement = (
            select(
                EventLog.event_log_id.label("id"),
                EventLog.timestamp,
                EventLog.status,
                EventLog.error_code,
                ErrorCodeModel.error_code_description.label("error_description"),
                EventLog.downtime_minutes,
            )
            .outerjoin(ErrorCodeModel, ErrorCodeModel.error_code == EventLog.error_code)
            .where(EventLog.machine_id == machine_id)
        )
        if start is not None:
            statement = statement.where(EventLog.timestamp >= start)
        if end is not None:
            statement = statement.where(EventLog.timestamp <= end)
        statement = statement.order_by(EventLog.timestamp.desc())
        return session.execute(statement).mappings().all()
