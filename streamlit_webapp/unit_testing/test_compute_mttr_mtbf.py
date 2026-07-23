import pandas as pd

from flows.compute_mttr_mtbf import ComputeMttrMtbf


def _events_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"machine_id": 1, "machine_name": "M1", "status": "error", "downtime_minutes": 60.0, "timestamp": pd.Timestamp("2026-06-01 00:00:00")},
        {"machine_id": 1, "machine_name": "M1", "status": "error", "downtime_minutes": 20.0, "timestamp": pd.Timestamp("2026-06-05 00:00:00")},
        {"machine_id": 2, "machine_name": "M2", "status": "maintenance", "downtime_minutes": 10.0, "timestamp": pd.Timestamp("2026-06-02 00:00:00")},
    ])


def test_empty_input_returns_empty_list():
    assert ComputeMttrMtbf().run(pd.DataFrame(columns=["machine_id", "machine_name", "status", "downtime_minutes", "timestamp"])) == []


def test_mttr_is_average_downtime_of_error_events_only():
    result = {row["machine_id"]: row for row in ComputeMttrMtbf().run(_events_df())}
    assert result[1]["failure_count"] == 2
    assert result[1]["mttr_minutes"] == 40.0  # (60 + 20) / 2


def test_machine_with_no_errors_has_zero_failures_and_no_mtbf():
    result = {row["machine_id"]: row for row in ComputeMttrMtbf().run(_events_df())}
    assert result[2]["failure_count"] == 0
    assert result[2]["mtbf_hours"] is None
