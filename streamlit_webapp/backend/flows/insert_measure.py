from __future__ import annotations

from sqlalchemy.orm import Session

from models.database_tables import Measure as MeasureModel


class InsertMeasure:
    def run(self, session: Session, machine_id: int, description: str, start_date: str) -> int:
        measure = MeasureModel(
            machine_id=machine_id,
            measure_description=description,
            start_date=start_date,
        )
        session.add(measure)
        session.commit()
        session.refresh(measure)
        return measure.measure_id
