import pandas as pd

from flows.filter_tickets import FilterTickets

COLUMNS = [
    "id", "ticket_type", "machine_id", "machine_name", "error_code",
    "error_description", "technician", "priority", "status", "description",
    "created_at", "assigned_at", "resolved_at", "closed_at", "resolution_hours",
]


def _tickets_df() -> pd.DataFrame:
    base = {c: None for c in COLUMNS}
    rows = [
        {**base, "id": 1, "machine_id": 1, "ticket_type": "Incident", "priority": "critical", "status": "Offen", "created_at": pd.Timestamp("2026-06-03")},
        {**base, "id": 2, "machine_id": 2, "ticket_type": "Incident", "priority": "low", "status": "Geschlossen", "created_at": pd.Timestamp("2026-06-02")},
        {**base, "id": 3, "machine_id": 1, "ticket_type": "Service Request", "priority": "low", "status": "Offen", "created_at": pd.Timestamp("2026-06-01")},
    ]
    return pd.DataFrame(rows)


def test_no_filters_returns_all_sorted_newest_first():
    result = FilterTickets().run(_tickets_df())
    assert [r["id"] for r in result] == [1, 2, 3]


def test_filter_by_machine_id():
    result = FilterTickets().run(_tickets_df(), machine_id=1)
    assert {r["id"] for r in result} == {1, 3}


def test_filter_by_priority():
    result = FilterTickets().run(_tickets_df(), priority="low")
    assert {r["id"] for r in result} == {2, 3}


def test_filter_by_status():
    result = FilterTickets().run(_tickets_df(), status="Offen")
    assert {r["id"] for r in result} == {1, 3}


def test_limit_truncates_results():
    result = FilterTickets().run(_tickets_df(), limit=1)
    assert len(result) == 1
    assert result[0]["id"] == 1
