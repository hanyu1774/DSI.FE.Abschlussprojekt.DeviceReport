from __future__ import annotations

from typing import Sequence

from sqlalchemy import RowMapping, select
from sqlalchemy.orm import Session

from models.database_tables import Hall as HallModel


class FetchHalls:
    def run(self, session: Session) -> Sequence[RowMapping]:
        statement = select(
            HallModel.hall_id.label("id"), HallModel.hall_name.label("name")
        ).order_by(HallModel.hall_name)
        return session.execute(statement).mappings().all()
