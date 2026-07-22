"""
Hilfsfunktionen fuer pandas-basierte EDA-Abfragen.

ACHTUNG - ANNAHME: Diese Datei wurde mir nicht mitgegeben. Ich habe sie
anhand ihrer Verwendung in kpi_service.py / ticket_service.py /
clustering_service.py rekonstruiert (Signatur `load_dataframe(query,
connection_string)` -> DataFrame, `to_json_records(df, columns)` -> list[dict],
inkl. NaN/NaT -> None fuer saubere JSON-Serialisierung durch Pydantic).

Falls dein echtes db_utils.py mehr macht (Caching, Logging, etc.), schick
es mir - ich gleiche dann nur `load_dataframe` an, der Rest bleibt wie er ist.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import Select
from sqlalchemy.engine import Engine


def load_dataframe(statement: Select[Any], engine: Engine) -> pd.DataFrame:
    """Fuehrt ein SQLAlchemy `select()`-Statement aus und gibt das Ergebnis
    als DataFrame zurueck.

    Ersetzt die bisherige Variante `load_dataframe(query: str,
    connection_string: str)`: statt eines rohen SQL-Strings + Pfad kommt
    jetzt ein typisiertes, aus den Models gebautes `select()`-Objekt + die
    gemeinsame Engine rein. pandas unterstuetzt SQLAlchemy-Statements direkt.
    """
    return pd.read_sql(statement, engine)


def to_json_records(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
    """Wandelt die angegebenen Spalten in JSON-vertraegliche dict-Records um
    (NaN/NaT -> None, sonst meckert Pydantic beim response_model)."""
    subset = df[columns].astype(object).where(df[columns].notna(), None)
    return subset.to_dict(orient="records")
