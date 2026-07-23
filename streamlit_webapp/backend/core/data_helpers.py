"""
Globale Hilfsfunktionen fuer pandas-basierte EDA-Flows (kpi/ticket/clustering).

Static, side-effect-free, no shared/global state touched — everything comes
in as an argument and goes out as a return value. Per your rule: global
helpers are fine outside the Model/Flow/Workflow ceremony as long as they
never mutate global state and never perform a "global task" on their own.
Both methods here just mechanically run a query or reshape a DataFrame —
zero domain awareness, so they don't qualify as Flows either.
"""
from __future__ import annotations

from typing import Any

import pandas as pd
from sqlalchemy import Select
from sqlalchemy.engine import Engine


class DataHelpers:
    @staticmethod
    def load_dataframe(statement: Select[Any], engine: Engine) -> pd.DataFrame:
        """Runs a SQLAlchemy select() statement and returns the result as a
        DataFrame."""
        return pd.read_sql(statement, engine)

    @staticmethod
    def to_json_records(df: pd.DataFrame, columns: list[str]) -> list[dict[str, Any]]:
        """Converts the given columns to JSON-safe dict records (NaN/NaT -> None)."""
        subset = df[columns].astype(object).where(df[columns].notna(), None)
        return subset.to_dict(orient="records")  # pyright: ignore[reportCallIssue] - pandas-stubs' to_dict overloads don't resolve orient="records" cleanly; it's always list[dict] at runtime for this orient
