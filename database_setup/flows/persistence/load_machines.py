"""Flow: loads machines from the database, optionally filtered by ID."""
from typing import Optional

from sqlalchemy.engine import Connection
from sqlalchemy import select

from models.machine import Machine
from models.sql_schemas import machines_table


class LoadMachines:
    def run(self, connection: Connection, machine_id: Optional[int] = None) -> list[Machine]:
        query = select(machines_table)
        if machine_id is not None:
            query = query.where(machines_table.c.id == machine_id)

        rows = connection.execute(query).mappings().all()
        return [self._to_model(row) for row in rows]

    def _to_model(self, row) -> Machine:
        machine = Machine()
        machine.id = row["id"]
        machine.name = row["name"]
        machine.machine_type = row["machine_type"]
        machine.hall = row["hall"]
        machine.manufacturer = row["manufacturer"]
        machine.year_built = row["year_built"]
        return machine
