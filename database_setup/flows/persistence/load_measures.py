"""Flow: loads all recorded measures."""
from sqlalchemy.engine import Connection
from sqlalchemy import select

from models.measure import Measure
from models.sql_schemas import measures_table


class LoadMeasures:
    def run(self, connection: Connection) -> list[Measure]:
        rows = connection.execute(select(measures_table)).mappings().all()
        return [self._to_model(row) for row in rows]

    def _to_model(self, row) -> Measure:
        measure = Measure()
        measure.id = row["id"]
        measure.machine_id = row["machine_id"]
        measure.description = row["description"]
        measure.start_date = row["start_date"]
        return measure
