"""Model: a single error or maintenance event in a machine's status history."""
from datetime import datetime
from typing import Optional


class Event:
    def __init__(self):
        self.id: int = 0
        self.machine_id: int = 0
        self.timestamp: datetime = datetime.min
        self.status: str = ""                    # "error" / "maintenance"
        self.error_code: Optional[str] = None
        self.downtime_minutes: Optional[float] = None
