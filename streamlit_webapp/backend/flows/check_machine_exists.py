from __future__ import annotations

from sqlalchemy.orm import Session

from models.database_tables import Machine as MachineModel


class MachineNotFound(Exception):
    """Plain domain exception - deliberately not HTTPException, so Flows/
    Workflows stay importable and testable without FastAPI installed. The
    router layer is responsible for translating this into a 404."""

    def __init__(self, machine_id: int) -> None:
        self.machine_id = machine_id
        super().__init__(f"Machine {machine_id} not found.")


class CheckMachineExists:
    def run(self, session: Session, machine_id: int) -> bool:
        return session.get(MachineModel, machine_id) is not None
