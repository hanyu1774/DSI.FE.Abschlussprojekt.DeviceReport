"""Model: estimated availability of one machine (KPI)."""


class AvailabilityResult:
    def __init__(self):
        self.machine_id: int = 0
        self.name: str = ""
        self.availability_percent: float = 0.0
