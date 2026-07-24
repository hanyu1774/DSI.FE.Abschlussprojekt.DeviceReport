import pandas as pd

from flows.summarize_tickets import SummarizeTickets
from models.ticket_status import TicketStatus


def _tickets_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"ticket_type": "Incident", "priority": "critical", "status": TicketStatus.OPEN, "error_category": "Elektrik"},
        {"ticket_type": "Incident", "priority": "low", "status": TicketStatus.CLOSED, "error_category": None},
        {"ticket_type": "Service Request", "priority": "low", "status": TicketStatus.OPEN, "error_category": "Sensorik"},
    ])


def test_total_and_open_count():
    summary = SummarizeTickets().run(_tickets_df())
    assert summary["total"] == 3
    assert summary["open_count"] == 2  # everything not TicketStatus.CLOSED


def test_critical_count():
    summary = SummarizeTickets().run(_tickets_df())
    assert summary["critical_count"] == 1


def test_by_priority_sorted_by_severity_order():
    summary = SummarizeTickets().run(_tickets_df())
    names_in_order = [item["name"] for item in summary["by_priority"]]
    assert names_in_order == ["critical", "low"]


def test_missing_error_category_grouped_as_ohne_fehlercode():
    summary = SummarizeTickets().run(_tickets_df())
    by_category = {item["name"]: item["count"] for item in summary["by_category"]}
    assert by_category["Ohne Fehlercode"] == 1
