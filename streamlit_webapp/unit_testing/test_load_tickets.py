import pandas as pd

from flows.load_tickets import LoadTickets


def test_loads_all_tickets_with_joins(seeded_engine):
    df = LoadTickets().run(seeded_engine)
    assert len(df) == 3
    assert set(df["ticket_type"]) == {"Incident", "Service Request"}


def test_date_columns_parsed_to_datetime(seeded_engine):
    df = LoadTickets().run(seeded_engine)
    for col in ("created_at", "assigned_at", "resolved_at", "closed_at"):
        assert pd.api.types.is_datetime64_any_dtype(df[col])


def test_unassigned_technician_is_null(seeded_engine):
    df = LoadTickets().run(seeded_engine)
    critical_row = df[df["priority"] == "critical"].iloc[0]
    assert pd.isna(critical_row["technician_first_name"])
