"""Maschinen-KPIs auf Basis von event_log (Fehlerrate, Verfuegbarkeit, MTTR/MTBF)."""

from __future__ import annotations

from fastapi import APIRouter

from core.database import db
from models.schema_models import AvailabilityKpi, ErrorRateKpi, MttrMtbfKpi
from workflows.kpi_workflows import AvailabilityWorkflow, ErrorRateWorkflow, MttrMtbfWorkflow

router = APIRouter(prefix="/kpi", tags=["KPIs"])


@router.get("/error-rate", response_model=list[ErrorRateKpi])
def error_rate() -> list[ErrorRateKpi]:
    return ErrorRateWorkflow().run(db.engine)


@router.get("/availability", response_model=list[AvailabilityKpi])
def availability() -> list[AvailabilityKpi]:
    return AvailabilityWorkflow().run(db.engine)


@router.get("/mttr-mtbf", response_model=list[MttrMtbfKpi])
def mttr_mtbf() -> list[MttrMtbfKpi]:
    return MttrMtbfWorkflow().run(db.engine)
