"""Flow: calculates the downtime per ticket (from handling time, falling back to the error catalogue)."""
from models.ticket import Ticket
from models.error_code import ErrorCode


class CalculateTicketDowntime:
    def run(self, tickets: list[Ticket], error_codes_by_code: dict[str, ErrorCode]) -> dict[int, float]:
        downtime_by_ticket_id: dict[int, float] = {}
        for ticket in tickets:
            if ticket.assigned_at and ticket.resolved_at:
                minutes = (ticket.resolved_at - ticket.assigned_at).total_seconds() / 60
            else:
                error_code = error_codes_by_code.get(ticket.error_code)
                minutes = error_code.avg_downtime_minutes if error_code else 0.0
            downtime_by_ticket_id[ticket.id] = minutes
        return downtime_by_ticket_id
