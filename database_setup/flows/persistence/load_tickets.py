"""Flow: loads tickets, optionally filtered by machine, optionally limited."""
from typing import Optional

from sqlalchemy.engine import Connection
from sqlalchemy import select

from models.ticket import Ticket
from models.sql_schemas import tickets_table


class LoadTickets:
    def run(self, connection: Connection, machine_id: Optional[int] = None,
            limit: Optional[int] = None) -> list[Ticket]:
        query = select(tickets_table)
        if machine_id is not None:
            query = query.where(tickets_table.c.machine_id == machine_id)
        query = query.order_by(tickets_table.c.created_at.desc())
        if limit is not None:
            query = query.limit(limit)

        rows = connection.execute(query).mappings().all()
        return [self._to_model(row) for row in rows]

    def _to_model(self, row) -> Ticket:
        ticket = Ticket()
        ticket.id = row["id"]
        ticket.machine_id = row["machine_id"]
        ticket.error_code = row["error_code"]
        ticket.description = row["description"]
        ticket.priority = row["priority"]
        ticket.technician = row["technician"]
        ticket.created_at = row["created_at"]
        ticket.assigned_at = row["assigned_at"]
        ticket.resolved_at = row["resolved_at"]
        ticket.closed_at = row["closed_at"]
        return ticket
