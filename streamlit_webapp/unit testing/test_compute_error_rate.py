import pandas as pd

from flows.compute_error_rate import ComputeErrorRate


def _events_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"machine_id": 1, "machine_name": "M1", "status": "error", "downtime_minutes": 30.0, "timestamp": pd.Timestamp("2026-06-01")},
        {"machine_id": 1, "machine_name": "M1", "status": "error", "downtime_minutes": 20.0, "timestamp": pd.Timestamp("2026-06-02")},
        {"machine_id": 1, "machine_name": "M1", "status": "maintenance", "downtime_minutes": 10.0, "timestamp": pd.Timestamp("2026-06-03")},
        {"machine_id": 2, "machine_name": "M2", "status": "offline", "downtime_minutes": 5.0, "timestamp": pd.Timestamp("2026-06-04")},
    ])


def test_counts_per_status_per_machine():
    result = {row["machine_id"]: row for row in ComputeErrorRate().run(_events_df())}

    assert result[1]["error_count"] == 2
    assert result[1]["maintenance_count"] == 1
    assert result[1]["offline_count"] == 0
    assert result[2]["offline_count"] == 1


def test_total_downtime_summed_correctly():
    result = {row["machine_id"]: row for row in ComputeErrorRate().run(_events_df())}
    assert result[1]["total_downtime_minutes"] == 60.0


def test_sorted_by_error_count_descending():
    rows = ComputeErrorRate().run(_events_df())
    error_counts = [row["error_count"] for row in rows]
    assert error_counts == sorted(error_counts, reverse=True)
