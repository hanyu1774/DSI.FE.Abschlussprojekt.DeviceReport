"""Model: error count & total downtime for one machine (KPI)."""


class ErrorRateResult:
    def __init__(self):
        self.machine_name: str = ""
        self.machine_type: str = ""
        self.error_count: int = 0
        self.total_downtime_minutes: float = 0.0
