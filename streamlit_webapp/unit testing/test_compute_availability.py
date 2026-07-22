import pandas as pd

from flows.compute_availability import ComputeAvailability


def _events_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"machine_id": 1, "machine_name": "M1", "status": "error", "downtime_minutes": 60.0, "timestamp": pd.Timestamp("2026-06-01 00:00:00")},
        {"machine_id": 1, "machine_name": "M1", "status": "maintenance", "downtime_minutes": 30.0, "timestamp": pd.Timestamp("2026-06-02 00:00:00")},
        {"machine_id": 2, "machine_name": "M2", "status": "offline", "downtime_minutes": 15.0, "timestamp": pd.Timestamp("2026-06-01 12:00:00")},
    ])


def test_empty_input_returns_empty_list():
    assert ComputeAvailability().run(pd.DataFrame(columns=["machine_id", "machine_name", "status", "downtime_minutes", "timestamp"])) == []


def test_maintenance_does_not_count_against_availability():
    result = {row["machine_id"]: row for row in ComputeAvailability().run(_events_df())}
    # Machine 1 only has 60 downtime minutes counted (error), not 90 (error+maintenance)
    period_minutes = (pd.Timestamp("2026-06-02") - pd.Timestamp("2026-06-01")).total_seconds() / 60
    expected_availability = round(100 * (1 - 60.0 / period_minutes), 2)
    assert result[1]["availability_percent"] == expected_availability


def test_availability_bounded_between_0_and_100():
    rows = ComputeAvailability().run(_events_df())
    for row in rows:
        assert 0 <= row["availability_percent"] <= 100
