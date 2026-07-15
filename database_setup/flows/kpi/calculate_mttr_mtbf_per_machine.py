"""Flow: calculates MTTR (mean time to repair) & MTBF (mean time between failures)."""
import pandas

from models.machine import Machine
from models.ticket import Ticket
from models.mttr_mtbf_result import MttrMtbfResult


class CalculateMttrMtbfPerMachine:
    def run(self, machines: list[Machine], tickets: list[Ticket]) -> list[MttrMtbfResult]:
        df = pandas.DataFrame([{
            "machine_id": t.machine_id,
            "created_at": t.created_at,
            "resolved_at": t.resolved_at,
        } for t in tickets])

        results = []
        for machine in machines:
            if df.empty:
                continue
            sub = df.loc[df.machine_id == machine.id].sort_values("created_at")
            if sub.empty:
                continue

            mttr = (sub.resolved_at - sub.created_at).dt.total_seconds().div(60).mean()
            gaps = sub.created_at.diff().dt.total_seconds().div(3600).dropna()
            mtbf = gaps.mean() if not gaps.empty else None

            result = MttrMtbfResult()
            result.machine_id = machine.id
            result.name = machine.name
            result.mttr_minutes = round(mttr, 1) if pandas.notna(mttr) else None
            result.mtbf_hours = round(mtbf, 1) if mtbf is not None and pandas.notna(mtbf) else None
            results.append(result)

        return results
