"""Flow: persists a single Measure to the database."""
from sqlalchemy.engine import Connection

from models.measure import Measure
from models.sql_schemas import measures_table


class SaveMeasure:
    def run(self, connection: Connection, measure: Measure) -> int:
        result = connection.execute(measures_table.insert(), [self._to_row(measure)])
        inserted_primary_key = result.inserted_primary_key
        if inserted_primary_key is None:
            raise ValueError("Insert did not return a primary key for the measure.")

        new_id = inserted_primary_key[0]
        measure.id = new_id
        return new_id

    def _to_row(self, measure: Measure) -> dict:
        return {
            "machine_id": measure.machine_id,
            "description": measure.description,
            "start_date": measure.start_date,
        }
