"""Model: one entry of the error catalogue."""


class ErrorCode:
    def __init__(self):
        self.code: str = ""
        self.description: str = ""
        self.severity: str = ""
        self.category: str = ""                 # latent root-cause category
        self.avg_downtime_minutes: float = 0.0
        self.applicable_machine_type: str = ""   # e.g. "Trockner", "Paketroboter"
