from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.engine import Engine

from core.data_helpers import DataHelpers
from models.database_tables import EventLog
from models.database_tables import Machine as MachineModel


class LoadKpiEvents:
    class _Query:
        statement = select(
            EventLog.machine_id,
            MachineModel.machine_name.label("machine_name"),
            EventLog.status,
            EventLog.downtime_minutes,
            EventLog.timestamp,
        ).join(MachineModel, MachineModel.machine_id == EventLog.machine_id)

    def run(self, engine: Engine) -> pd.DataFrame:
        df = DataHelpers.load_dataframe(self._Query.statement, engine)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        return df
