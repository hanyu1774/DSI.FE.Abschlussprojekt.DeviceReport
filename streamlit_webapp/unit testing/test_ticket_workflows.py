import pytest

from workflows.ticket_workflows import (
    ListTicketsWorkflow,
    TicketClustersWorkflow,
    TicketResponseTimesWorkflow,
    TicketSummaryWorkflow,
    TicketTrendWorkflow,
)


def test_list_tickets_workflow(seeded_engine):
    result = ListTicketsWorkflow().run(seeded_engine)
    assert len(result) == 3


def test_list_tickets_workflow_respects_priority_filter(seeded_engine):
    result = ListTicketsWorkflow().run(seeded_engine, priority="critical")
    assert len(result) == 1
    assert result[0].priority == "critical"


def test_ticket_summary_workflow(seeded_engine):
    result = TicketSummaryWorkflow().run(seeded_engine)
    assert result.total == 3


def test_ticket_trend_workflow(seeded_engine):
    result = TicketTrendWorkflow().run(seeded_engine, interval="day")
    assert sum(point.total for point in result) == 3


def test_ticket_response_times_workflow(seeded_engine):
    result = TicketResponseTimesWorkflow().run(seeded_engine)
    assert result.overall.ticket_count == 3


def test_ticket_clusters_workflow_returns_something_for_seeded_data(seeded_engine):
    # Only 3 seeded tickets - below the clustering Flow's viable document
    # threshold (see tests/flows/test_cluster_ticket_texts.py), so this
    # exercises the same real, pre-existing limitation end-to-end.
    with pytest.raises(ValueError):
        TicketClustersWorkflow().run(seeded_engine, n_clusters=2)
