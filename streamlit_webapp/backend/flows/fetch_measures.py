from __future__ import annotations

from typing import Sequence

from sqlalchemy import RowMapping, select
from sqlalchemy.orm import Session

from models.database_tables import Machine as MachineModel
from models.database_tables import Measure as MeasureModel


class FetchMeasures:
    def run(self, session: Session, measure_id: int | None = None) -> Sequence[RowMapping]:
        statement = (
            select(
                MeasureModel.measure_id.label("id"),
                MeasureModel.machine_id,
                MachineModel.machine_name.label("machine_name"),
                MeasureModel.measure_description.label("description"),
                MeasureModel.start_date,
            )
            .join(MachineModel, MachineModel.machine_id == MeasureModel.machine_id)
        )
        if measure_id is not None:
            statement = statement.where(MeasureModel.measure_id == measure_id)
        else:
            statement = statement.order_by(MeasureModel.start_date.desc())
        return session.execute(statement).mappings().all()
