"""Flow: loads error/maintenance events, optionally filtered by machine and time range."""
from datetime import datetime
from typing import Optional

from sqlalchemy.engine import Connection
from sqlalchemy import select

from models.event import Event
from models.sql_schemas import events_table


class LoadEvents:
    def run(self, connection: Connection, machine_id: Optional[int] = None,
            start: Optional[datetime] = None, end: Optional[datetime] = None) -> list[Event]:
        query = select(events_table)
        if machine_id is not None:
            query = query.where(events_table.c.machine_id == machine_id)
        if start is not None:
            query = query.where(events_table.c.timestamp >= start)
        if end is not None:
            query = query.where(events_table.c.timestamp <= end)
        query = query.order_by(events_table.c.timestamp)

        rows = connection.execute(query).mappings().all()
        return [self._to_model(row) for row in rows]

    def _to_model(self, row) -> Event:
        event = Event()
        event.id = row["id"]
        event.machine_id = row["machine_id"]
        event.timestamp = row["timestamp"]
        event.status = row["status"]
        event.error_code = row["error_code"]
        event.downtime_minutes = row["downtime_minutes"]
        return event
