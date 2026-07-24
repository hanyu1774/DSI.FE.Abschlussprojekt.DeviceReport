from __future__ import annotations

from typing import Sequence

from sqlalchemy import RowMapping, select
from sqlalchemy.orm import Session

from models.database_tables import Hall as HallModel
from models.database_tables import Machine as MachineModel
from models.database_tables import MachineType as MachineTypeModel


class FetchMachines:
    class _Query:
        statement = (
            select(
                MachineModel.machine_id.label("id"),
                MachineModel.machine_name.label("name"),
                MachineTypeModel.machine_type_name.label("machine_type"),
                HallModel.hall_name.label("hall"),
                MachineModel.manufacturer,
                MachineModel.year_built,
            )
            .join(MachineTypeModel, MachineTypeModel.machine_type_id == MachineModel.machine_type_id)
            .join(HallModel, HallModel.hall_id == MachineModel.hall_id)
        )

    def run(self, session: Session, machine_id: int | None = None) -> Sequence[RowMapping]:
        statement = self._Query.statement.order_by(MachineModel.machine_name)
        if machine_id is not None:
            statement = statement.where(MachineModel.machine_id == machine_id)
        return session.execute(statement).mappings().all()
