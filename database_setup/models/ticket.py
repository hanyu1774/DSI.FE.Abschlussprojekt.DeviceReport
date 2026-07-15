"""Model: a ticket including its free-text description."""
from datetime import datetime
from typing import Optional


class Ticket:
    def __init__(self):
        self.id: int = 0
        self.machine_id: int = 0
        self.error_code: str = ""
        self.description: str = ""
        self.priority: str = ""
        self.technician: str = ""
        self.created_at: datetime = datetime.min
        self.assigned_at: Optional[datetime] = None
        self.resolved_at: Optional[datetime] = None
        self.closed_at: Optional[datetime] = None
