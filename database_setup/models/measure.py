"""Model: a maintenance measure entered by the team (Feature 1)."""
from datetime import datetime
from pydantic import BaseModel


class Measure:
    def __init__(self):
        self.id: int = 0
        self.machine_id: int = 0
        self.description: str = ""
        self.start_date: datetime = datetime.min

class MeasureIn(BaseModel):
    machine_id: int
    description: str
    start_date: datetime
