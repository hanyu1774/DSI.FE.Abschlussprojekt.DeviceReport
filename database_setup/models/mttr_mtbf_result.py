"""Model: MTTR/MTBF figures for one machine (KPI)."""
from typing import Optional


class MttrMtbfResult:
    def __init__(self):
        self.machine_id: int = 0
        self.name: str = ""
        self.mttr_minutes: Optional[float] = None
        self.mtbf_hours: Optional[float] = None
