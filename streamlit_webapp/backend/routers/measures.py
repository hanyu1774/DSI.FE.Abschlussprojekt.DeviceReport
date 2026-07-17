"""Wartungsmassnahmen: auflisten und anlegen."""

from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from database import get_db
from schemas import Measure, MeasureCreate

router = APIRouter(prefix="/measures", tags=["Wartungsmassnahmen"])

MEASURES_QUERY = """
    SELECT me.measure_id AS id, me.machine_id, m.name AS machine_name,
           me.description, me.start_date
    FROM measures me
    JOIN machines m ON m.machine_id = me.machine_id
"""


@router.get("", response_model=list[Measure])
def list_measures(connection: sqlite3.Connection = Depends(get_db)) -> list[Measure]:
    rows = connection.execute(MEASURES_QUERY + " ORDER BY me.start_date DESC").fetchall()
    return [Measure(**dict(row)) for row in rows]


@router.post("", response_model=Measure, status_code=201)
def create_measure(
    payload: MeasureCreate, connection: sqlite3.Connection = Depends(get_db)
) -> Measure:
    exists = connection.execute(
        "SELECT 1 FROM machines WHERE machine_id = ?", (payload.machine_id,)
    ).fetchone()
    if exists is None:
        raise HTTPException(status_code=404, detail="Maschine nicht gefunden.")

    cursor = connection.execute(
        "INSERT INTO measures (machine_id, description, start_date) VALUES (?, ?, ?)",
        (payload.machine_id, payload.description, payload.start_date),
    )
    connection.commit()

    row = connection.execute(
        MEASURES_QUERY + " WHERE me.measure_id = ?", (cursor.lastrowid,)
    ).fetchone()
    return Measure(**dict(row))
