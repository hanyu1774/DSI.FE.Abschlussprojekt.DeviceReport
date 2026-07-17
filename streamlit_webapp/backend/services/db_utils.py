"""
Kleine, wiederverwendete Hilfsfunktionen fuer die Services.

`load_dataframe` zeigt bewusst die zweite vom Auftraggeber gewuenschte
Variante: statt den Connection String global zu importieren, wird er
explizit als Argument uebergeben (typischerweise `db.connection_string`
aus `database.py`). Das macht die Funktion unabhaengig von FastAPI
testbar und wiederverwendbar (z. B. auch aus einem Notebook heraus).
"""

from __future__ import annotations

import sqlite3
from typing import Any, Sequence

import pandas as pd


def load_dataframe(
    query: str,
    connection_string: str,
    params: Sequence[Any] | dict[str, Any] = (),
) -> pd.DataFrame:
    """Fuehrt `query` gegen die durch `connection_string` beschriebene
    SQLite-Datenbank aus und gibt das Ergebnis als DataFrame zurueck."""
    with sqlite3.connect(connection_string) as connection:
        return pd.read_sql_query(query, connection, params=params)


def to_json_records(df: pd.DataFrame, columns: list[str] | None = None) -> list[dict]:
    """Wandelt ein DataFrame in eine Liste JSON-tauglicher dicts um.

    - Timestamp-Spalten werden zu ISO-8601-Strings.
    - NaN / NaT / None werden einheitlich zu `None`, damit Pydantic sie
      sauber als optionale Felder validieren kann (rohe NaN/NaT-Werte
      wuerden das sonst nicht tun).
    """
    out = df[columns].copy() if columns is not None else df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    out = out.astype(object).where(pd.notna(out), None)
    return out.to_dict("records")
