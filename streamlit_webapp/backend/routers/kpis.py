"""Maschinen-KPIs auf Basis von event_log (Fehlerrate, Verfuegbarkeit, MTTR/MTBF)."""

from __future__ import annotations

from fastapi import APIRouter

from database import db
from schemas import AvailabilityKpi, ErrorRateKpi, MttrMtbfKpi
from services import kpi_service

router = APIRouter(prefix="/kpi", tags=["KPIs"])


@router.get("/error-rate", response_model=list[ErrorRateKpi])
def error_rate() -> list[dict]:
    return kpi_service.get_error_rate(db.connection_string)


@router.get("/availability", response_model=list[AvailabilityKpi])
def availability() -> list[dict]:
    return kpi_service.get_availability(db.connection_string)


@router.get("/mttr-mtbf", response_model=list[MttrMtbfKpi])
def mttr_mtbf() -> list[dict]:
    return kpi_service.get_mttr_mtbf(db.connection_string)
