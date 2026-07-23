"""Wartungsmassnahmen: auflisten und anlegen."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from core.database import get_db
from flows.check_machine_exists import MachineNotFound
from models.schema_models import Measure, MeasureCreate
from workflows.measures_workflows import CreateMeasureWorkflow, ListMeasuresWorkflow

router = APIRouter(prefix="/measures", tags=["Wartungsmassnahmen"])


@router.get("", response_model=list[Measure])
def list_measures(session: Session = Depends(get_db)) -> list[Measure]:
    return ListMeasuresWorkflow().run(session)


@router.post("", response_model=Measure, status_code=201)
def create_measure(payload: MeasureCreate, session: Session = Depends(get_db)) -> Measure:
    try:
        return CreateMeasureWorkflow().run(session, payload)
    except MachineNotFound as exc:
        raise HTTPException(status_code=404, detail="Maschine nicht gefunden.") from exc
