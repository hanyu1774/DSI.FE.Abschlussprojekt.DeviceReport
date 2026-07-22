from __future__ import annotations

from typing import Sequence

from sqlalchemy import RowMapping, select
from sqlalchemy.orm import Session

from models.database_tables import ErrorCode as ErrorCodeModel
from models.database_tables import MachineType as MachineTypeModel


class FetchErrorCodes:
    def run(self, session: Session) -> Sequence[RowMapping]:
        statement = (
            select(
                ErrorCodeModel.error_code,
                ErrorCodeModel.error_code_description.label("description"),
                ErrorCodeModel.severity,
                ErrorCodeModel.category,
                MachineTypeModel.machine_type_name.label("machine_type"),
            )
            .join(MachineTypeModel, MachineTypeModel.machine_type_id == ErrorCodeModel.machine_type_id)
            .order_by(ErrorCodeModel.error_code)
        )
        return session.execute(statement).mappings().all()
