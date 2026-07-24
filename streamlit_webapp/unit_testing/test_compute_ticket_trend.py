import pandas as pd

from flows.compute_ticket_trend import ComputeTicketTrend


def _tickets_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"created_at": pd.Timestamp("2026-06-01"), "ticket_type": "Incident"},
        {"created_at": pd.Timestamp("2026-06-01"), "ticket_type": "Incident"},
        {"created_at": pd.Timestamp("2026-06-01"), "ticket_type": "Service Request"},
        {"created_at": pd.Timestamp("2026-06-08"), "ticket_type": "Incident"},
    ])


def test_daily_interval_buckets_by_day():
    result = ComputeTicketTrend().run(_tickets_df(), interval="day")
    day_one = next(r for r in result if r["period"] == "2026-06-01")
    assert day_one["incident_count"] == 2
    assert day_one["service_request_count"] == 1
    assert day_one["total"] == 3


def test_second_week_shows_up_separately():
    result = ComputeTicketTrend().run(_tickets_df(), interval="day")
    periods = {r["period"] for r in result}
    assert "2026-06-08" in periods
