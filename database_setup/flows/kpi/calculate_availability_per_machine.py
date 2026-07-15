"""Flow: estimates the availability of each machine over the observed time range."""
from typing import Any, cast

import pandas

from models.machine import Machine
from models.event import Event
from models.availability_result import AvailabilityResult


class CalculateAvailabilityPerMachine:
    def run(self, machines: list[Machine], events: list[Event]) -> list[AvailabilityResult]:
        machines_by_id = {m.id: m for m in machines}

        df = pandas.DataFrame([{
            "machine_id": e.machine_id,
            "timestamp": e.timestamp,
            "downtime_minutes": e.downtime_minutes or 0.0,
        } for e in events])

        if df.empty:
            return []

        grouped = df.groupby("machine_id").agg(
            start=("timestamp", "min"),
            end=("timestamp", "max"),
            total_downtime=("downtime_minutes", "sum"),
        ).reset_index()

        results = []
        for _, row in grouped.iterrows():
            machine = machines_by_id.get(int(cast(Any, row["machine_id"])))
            if machine is None:
                continue

            start_timestamp = pandas.Timestamp(cast(Any, row["start"]))
            end_timestamp = pandas.Timestamp(cast(Any, row["end"]))
            total_downtime_minutes = float(cast(Any, row["total_downtime"]))
            total_minutes = max((end_timestamp - start_timestamp).total_seconds() / 60, 1)
            availability = max(0.0, 1 - total_downtime_minutes / total_minutes)

            result = AvailabilityResult()
            result.machine_id = machine.id
            result.name = machine.name
            result.availability_percent = round(availability * 100, 2)
            results.append(result)

        results.sort(key=lambda r: r.availability_percent)
        return results
