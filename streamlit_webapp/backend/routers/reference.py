"""Stammdaten & Referenzdaten: Hallen, Maschinentypen, Maschinen, Techniker, Fehlercodes."""

from __future__ import annotations

import sqlite3
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from database import get_db
from schemas import ErrorCode, Hall, Machine, MachineEvent, MachineType, Technician

router = APIRouter(tags=["Referenzdaten"])


@router.get("/halls", response_model=list[Hall])
def list_halls(connection: sqlite3.Connection = Depends(get_db)) -> list[Hall]:
    rows = connection.execute("SELECT hall_id AS id, name FROM halls ORDER BY name").fetchall()
    return [Hall(**dict(row)) for row in rows]


@router.get("/machine-types", response_model=list[MachineType])
def list_machine_types(connection: sqlite3.Connection = Depends(get_db)) -> list[MachineType]:
    rows = connection.execute(
        "SELECT machine_type_id AS id, name FROM machine_types ORDER BY name"
    ).fetchall()
    return [MachineType(**dict(row)) for row in rows]


@router.get("/technicians", response_model=list[Technician])
def list_technicians(connection: sqlite3.Connection = Depends(get_db)) -> list[Technician]:
    rows = connection.execute(
        "SELECT technician_id AS id, first_name, last_name, shift FROM technicians ORDER BY last_name"
    ).fetchall()
    return [Technician(**dict(row)) for row in rows]


@router.get("/error-codes", response_model=list[ErrorCode])
def list_error_codes(connection: sqlite3.Connection = Depends(get_db)) -> list[ErrorCode]:
    rows = connection.execute(
        """
        SELECT ec.error_code, ec.description, ec.severity, ec.category,
               mt.name AS machine_type
        FROM error_codes ec
        JOIN machine_types mt ON mt.machine_type_id = ec.machine_type_id
        ORDER BY ec.error_code
        """
    ).fetchall()
    return [ErrorCode(**dict(row)) for row in rows]


MACHINES_QUERY = """
    SELECT m.machine_id AS id, m.name, mt.name AS machine_type,
           h.name AS hall, m.manufacturer, m.year_built
    FROM machines m
    JOIN machine_types mt ON mt.machine_type_id = m.machine_type_id
    JOIN halls h ON h.hall_id = m.hall_id
"""


@router.get("/machines", response_model=list[Machine])
def list_machines(connection: sqlite3.Connection = Depends(get_db)) -> list[Machine]:
    rows = connection.execute(MACHINES_QUERY + " ORDER BY m.name").fetchall()
    return [Machine(**dict(row)) for row in rows]


@router.get("/machines/{machine_id}", response_model=Machine)
def get_machine(machine_id: int, connection: sqlite3.Connection = Depends(get_db)) -> Machine:
    row = connection.execute(MACHINES_QUERY + " WHERE m.machine_id = ?", (machine_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail="Maschine nicht gefunden.")
    return Machine(**dict(row))


@router.get("/machines/{machine_id}/events", response_model=list[MachineEvent])
def get_machine_events(
    machine_id: int,
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    connection: sqlite3.Connection = Depends(get_db),
) -> list[MachineEvent]:
    query = """
        SELECT e.event_log_id AS id, e.timestamp, e.status, e.error_code,
               ec.description AS error_description, e.downtime_minutes
        FROM event_log e
        LEFT JOIN error_codes ec ON ec.error_code = e.error_code
        WHERE e.machine_id = ?
    """
    params: list[object] = [machine_id]
    if start is not None:
        query += " AND e.timestamp >= ?"
        params.append(start.strftime("%Y-%m-%d %H:%M:%S"))
    if end is not None:
        query += " AND e.timestamp <= ?"
        params.append(end.strftime("%Y-%m-%d %H:%M:%S"))
    query += " ORDER BY e.timestamp DESC"

    rows = connection.execute(query, params).fetchall()
    return [MachineEvent(**dict(row)) for row in rows]
