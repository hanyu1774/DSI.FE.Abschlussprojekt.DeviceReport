"""Model: a single root-cause cluster from the NLP clustering (Feature 2)."""
from typing import Optional


class ClusterResult:
    def __init__(self):
        self.cluster: int = 0
        self.label: str = ""
        self.ticket_count: int = 0
        self.ticket_share_percent: float = 0.0
        self.downtime_share_percent: Optional[float] = None
        self.example_ticket: str = ""
