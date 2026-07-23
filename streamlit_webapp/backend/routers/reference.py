"""Stammdaten & Referenzdaten: Hallen, Maschinentypen, Maschinen, Techniker, Fehlercodes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from core.database import get_db
from flows.check_machine_exists import MachineNotFound
from models.schema_models import ErrorCode, Hall, Machine, MachineEvent, MachineType, Technician
from workflows.reference_workflows import (
    GetMachineWorkflow,
    ListErrorCodesWorkflow,
    ListHallsWorkflow,
    ListMachineEventsWorkflow,
    ListMachinesWorkflow,
    ListMachineTypesWorkflow,
    ListTechniciansWorkflow,
)

router = APIRouter(tags=["Referenzdaten"])


@router.get("/halls", response_model=list[Hall])
def list_halls(session: Session = Depends(get_db)) -> list[Hall]:
    return ListHallsWorkflow().run(session)


@router.get("/machine-types", response_model=list[MachineType])
def list_machine_types(session: Session = Depends(get_db)) -> list[MachineType]:
    return ListMachineTypesWorkflow().run(session)


@router.get("/technicians", response_model=list[Technician])
def list_technicians(session: Session = Depends(get_db)) -> list[Technician]:
    return ListTechniciansWorkflow().run(session)


@router.get("/error-codes", response_model=list[ErrorCode])
def list_error_codes(session: Session = Depends(get_db)) -> list[ErrorCode]:
    return ListErrorCodesWorkflow().run(session)


@router.get("/machines", response_model=list[Machine])
def list_machines(session: Session = Depends(get_db)) -> list[Machine]:
    return ListMachinesWorkflow().run(session)


@router.get("/machines/{machine_id}", response_model=Machine)
def get_machine(machine_id: int, session: Session = Depends(get_db)) -> Machine:
    try:
        return GetMachineWorkflow().run(session, machine_id)
    except MachineNotFound as exc:
        raise HTTPException(status_code=404, detail="Maschine nicht gefunden.") from exc


@router.get("/machines/{machine_id}/events", response_model=list[MachineEvent])
def get_machine_events(
    machine_id: int,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session: Session = Depends(get_db),
) -> list[MachineEvent]:
    return ListMachineEventsWorkflow().run(session, machine_id, start=start, end=end)
