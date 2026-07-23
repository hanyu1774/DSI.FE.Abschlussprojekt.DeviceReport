import pandas as pd

from flows.compute_response_times import ComputeResponseTimes


def _tickets_df() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "priority": "critical",
            "created_at": pd.Timestamp("2026-06-01 00:00:00"),
            "assigned_at": pd.Timestamp("2026-06-01 01:00:00"),
            "resolved_at": pd.Timestamp("2026-06-01 05:00:00"),
            "closed_at": pd.Timestamp("2026-06-01 06:00:00"),
        },
        {
            "priority": "low",
            "created_at": pd.Timestamp("2026-06-01 00:00:00"),
            "assigned_at": pd.NaT,
            "resolved_at": pd.NaT,
            "closed_at": pd.NaT,
        },
    ])


def test_overall_ticket_count():
    result = ComputeResponseTimes().run(_tickets_df())
    assert result["overall"]["ticket_count"] == 2


def test_average_resolve_time_for_resolved_ticket():
    result = ComputeResponseTimes().run(_tickets_df())
    critical = next(p for p in result["by_priority"] if p["label"] == "critical")
    assert critical["avg_time_to_resolve_hours"] == 5.0


def test_unresolved_ticket_gives_none_not_nan():
    result = ComputeResponseTimes().run(_tickets_df())
    low = next(p for p in result["by_priority"] if p["label"] == "low")
    assert low["avg_time_to_resolve_hours"] is None
