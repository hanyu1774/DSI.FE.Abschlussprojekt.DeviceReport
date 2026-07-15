"""Model: pure master data for one machine. No SQL knowledge, no logic."""


class Machine:
    def __init__(self):
        self.id: int = 0
        self.name: str = ""
        self.machine_type: str = ""
        self.hall: str = ""
        self.manufacturer: str = ""
        self.year_built: int = 0
