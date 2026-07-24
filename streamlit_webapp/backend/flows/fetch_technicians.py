from __future__ import annotations

from typing import Sequence

from sqlalchemy import RowMapping, select
from sqlalchemy.orm import Session

from models.database_tables import Technician as TechnicianModel


class FetchTechnicians:
    def run(self, session: Session) -> Sequence[RowMapping]:
        statement = select(
            TechnicianModel.technician_id.label("id"),
            TechnicianModel.first_name,
            TechnicianModel.last_name,
            TechnicianModel.shift,
        ).order_by(TechnicianModel.last_name)
        return session.execute(statement).mappings().all()
