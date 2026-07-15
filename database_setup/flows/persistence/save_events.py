"""Flow: persists Event models to the database."""
from sqlalchemy.engine import Connection

from models.event import Event
from models.sql_schemas import events_table


class SaveEvents:
    def run(self, connection: Connection, events: list[Event]) -> None:
        if not events:
            return
        rows = [self._to_row(e) for e in events]
        connection.execute(events_table.insert(), rows)

    def _to_row(self, event: Event) -> dict:
        return {
            "machine_id": event.machine_id, "timestamp": event.timestamp,
            "status": event.status, "error_code": event.error_code,
            "downtime_minutes": event.downtime_minutes,
        }
