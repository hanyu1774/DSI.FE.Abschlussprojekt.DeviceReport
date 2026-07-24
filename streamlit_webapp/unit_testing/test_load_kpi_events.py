import pandas as pd

from flows.load_kpi_events import LoadKpiEvents


def test_loads_events_with_machine_names(seeded_engine):
    df = LoadKpiEvents().run(seeded_engine)
    assert len(df) == 3
    assert set(df["machine_name"]) == {"Trockner-01", "Trockner-02"}


def test_timestamp_column_is_parsed_to_datetime(seeded_engine):
    df = LoadKpiEvents().run(seeded_engine)
    assert pd.api.types.is_datetime64_any_dtype(df["timestamp"])
