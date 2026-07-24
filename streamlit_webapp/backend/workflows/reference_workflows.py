from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from flows.check_machine_exists import MachineNotFound
from flows.fetch_error_codes import FetchErrorCodes
from flows.fetch_halls import FetchHalls
from flows.fetch_machine_events import FetchMachineEvents
from flows.fetch_machine_types import FetchMachineTypes
from flows.fetch_machines import FetchMachines
from flows.fetch_technicians import FetchTechnicians
from models.schema_models import ErrorCode, Hall, Machine, MachineEvent, MachineType, Technician


class ListHallsWorkflow:
    def run(self, session: Session) -> list[Hall]:
        rows = FetchHalls().run(session)
        return [Hall(**row) for row in rows]


class ListMachineTypesWorkflow:
    def run(self, session: Session) -> list[MachineType]:
        rows = FetchMachineTypes().run(session)
        return [MachineType(**row) for row in rows]


class ListTechniciansWorkflow:
    def run(self, session: Session) -> list[Technician]:
        rows = FetchTechnicians().run(session)
        return [Technician(**row) for row in rows]


class ListErrorCodesWorkflow:
    def run(self, session: Session) -> list[ErrorCode]:
        rows = FetchErrorCodes().run(session)
        return [ErrorCode(**row) for row in rows]


class ListMachinesWorkflow:
    def run(self, session: Session) -> list[Machine]:
        rows = FetchMachines().run(session)
        return [Machine(**row) for row in rows]


class GetMachineWorkflow:
    def run(self, session: Session, machine_id: int) -> Machine:
        rows = FetchMachines().run(session, machine_id=machine_id)
        if not rows:
            raise MachineNotFound(machine_id)
        return Machine(**rows[0])


class ListMachineEventsWorkflow:
    def run(
        self,
        session: Session,
        machine_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> list[MachineEvent]:
        start_text = start.strftime("%Y-%m-%d %H:%M:%S") if start is not None else None
        end_text = end.strftime("%Y-%m-%d %H:%M:%S") if end is not None else None
        rows = FetchMachineEvents().run(session, machine_id, start=start_text, end=end_text)
        return [MachineEvent(**row) for row in rows]
