"""Flow: persists Ticket models to the database."""
from sqlalchemy.engine import Connection

from models.ticket import Ticket
from models.sql_schemas import tickets_table


class SaveTickets:
    def run(self, connection: Connection, tickets: list[Ticket]) -> None:
        if not tickets:
            return
        rows = [self._to_row(t) for t in tickets]
        connection.execute(tickets_table.insert(), rows)

    def _to_row(self, ticket: Ticket) -> dict:
        return {
            "machine_id": ticket.machine_id, "error_code": ticket.error_code,
            "description": ticket.description, "priority": ticket.priority,
            "technician": ticket.technician, "created_at": ticket.created_at,
            "assigned_at": ticket.assigned_at, "resolved_at": ticket.resolved_at,
            "closed_at": ticket.closed_at,
        }
