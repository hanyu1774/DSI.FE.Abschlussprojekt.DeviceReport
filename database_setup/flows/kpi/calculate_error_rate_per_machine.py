"""Flow: calculates error count & total downtime per machine."""
import pandas as pd

from models.machine import Machine
from models.event import Event
from models.error_rate_result import ErrorRateResult


class CalculateErrorRatePerMachine:
    def run(self, machines: list[Machine], events: list[Event]) -> list[ErrorRateResult]:
        machines_by_id = {m.id: m for m in machines}
        error_events = [e for e in events if e.status == "error"]

        df = pd.DataFrame([{
            "machine_id": e.machine_id,
            "downtime_minutes": e.downtime_minutes or 0.0,
        } for e in error_events])

        if df.empty:
            return []

        grouped = df.groupby("machine_id").agg(
            error_count=("machine_id", "count"),
            total_downtime_minutes=("downtime_minutes", "sum"),
        ).reset_index()

        results = []
        for _, row in grouped.iterrows():
            machine = machines_by_id.get(int(row["machine_id"]))
            if machine is None:
                continue
            result = ErrorRateResult()
            result.machine_name = machine.name
            result.machine_type = machine.machine_type
            result.error_count = int(row["error_count"])
            result.total_downtime_minutes = round(float(row["total_downtime_minutes"]), 1)
            results.append(result)

        results.sort(key=lambda r: r.error_count, reverse=True)
        return results
