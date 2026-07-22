from __future__ import annotations

from sqlalchemy.orm import Session

from flows.check_machine_exists import CheckMachineExists, MachineNotFound
from flows.fetch_measures import FetchMeasures
from flows.insert_measure import InsertMeasure
from models.schema_models import Measure, MeasureCreate


class ListMeasuresWorkflow:
    def run(self, session: Session) -> list[Measure]:
        rows = FetchMeasures().run(session)
        return [Measure(**row) for row in rows]


class CreateMeasureWorkflow:
    def run(self, session: Session, payload: MeasureCreate) -> Measure:
        if not CheckMachineExists().run(session, payload.machine_id):
            raise MachineNotFound(payload.machine_id)

        new_id = InsertMeasure().run(
            session,
            machine_id=payload.machine_id,
            description=payload.description,
            start_date=payload.start_date,
        )
        rows = FetchMeasures().run(session, measure_id=new_id)
        return Measure(**rows[0])
