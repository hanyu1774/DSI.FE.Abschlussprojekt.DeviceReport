"""Flow: persists Machine models to the database."""
from sqlalchemy import insert
from sqlalchemy.engine import Connection

from models.machine import Machine
from models.sql_schemas import machines_table


class SaveMachines:
    def run(self, connection: Connection, machines: list[Machine]) -> None:
        if not machines:
            return
        rows = [self._to_row(m) for m in machines]
        # executemany inserts don't return generated IDs via inserted_primary_key_rows
        # on SQLite - RETURNING must be requested explicitly to get them back.
        statement = insert(machines_table).returning(machines_table.c.id)
        result = connection.execute(statement, rows)
        for machine, new_id in zip(machines, result.scalars().all()):
            machine.id = new_id

    def _to_row(self, machine: Machine) -> dict:
        return {
            "name": machine.name, "machine_type": machine.machine_type, "hall": machine.hall,
            "manufacturer": machine.manufacturer, "year_built": machine.year_built,
        }
