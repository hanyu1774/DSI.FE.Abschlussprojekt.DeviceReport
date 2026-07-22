from __future__ import annotations

from typing import Sequence

from sqlalchemy import RowMapping, select
from sqlalchemy.orm import Session

from models.database_tables import MachineType as MachineTypeModel


class FetchMachineTypes:
    def run(self, session: Session) -> Sequence[RowMapping]:
        statement = select(
            MachineTypeModel.machine_type_id.label("id"),
            MachineTypeModel.machine_type_name.label("name"),
        ).order_by(MachineTypeModel.machine_type_name)
        return session.execute(statement).mappings().all()
