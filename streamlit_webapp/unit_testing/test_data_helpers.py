import pandas as pd
from sqlalchemy import select

from core.data_helpers import DataHelpers
from models.database_tables import Hall


def test_load_dataframe_runs_a_select_statement(seeded_engine):
    statement = select(Hall.hall_name)
    df = DataHelpers.load_dataframe(statement, seeded_engine)
    assert len(df) == 2


def test_to_json_records_converts_nan_to_none():
    df = pd.DataFrame({"a": [1, None], "b": ["x", "y"]})
    records = DataHelpers.to_json_records(df, ["a", "b"])
    assert records[1]["a"] is None


def test_to_json_records_only_includes_requested_columns():
    df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
    records = DataHelpers.to_json_records(df, ["a", "c"])
    assert set(records[0].keys()) == {"a", "c"}
