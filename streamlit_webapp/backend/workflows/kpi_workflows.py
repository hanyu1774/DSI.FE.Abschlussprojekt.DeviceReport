from __future__ import annotations

from sqlalchemy.engine import Engine

from flows.compute_availability import ComputeAvailability
from flows.compute_error_rate import ComputeErrorRate
from flows.compute_mttr_mtbf import ComputeMttrMtbf
from flows.load_kpi_events import LoadKpiEvents
from models.schema_models import AvailabilityKpi, ErrorRateKpi, MttrMtbfKpi


class ErrorRateWorkflow:
    def run(self, engine: Engine) -> list[ErrorRateKpi]:
        events_df = LoadKpiEvents().run(engine)
        records = ComputeErrorRate().run(events_df)
        return [ErrorRateKpi(**record) for record in records]


class AvailabilityWorkflow:
    def run(self, engine: Engine) -> list[AvailabilityKpi]:
        events_df = LoadKpiEvents().run(engine)
        records = ComputeAvailability().run(events_df)
        return [AvailabilityKpi(**record) for record in records]


class MttrMtbfWorkflow:
    def run(self, engine: Engine) -> list[MttrMtbfKpi]:
        events_df = LoadKpiEvents().run(engine)
        records = ComputeMttrMtbf().run(events_df)
        return [MttrMtbfKpi(**record) for record in records]
