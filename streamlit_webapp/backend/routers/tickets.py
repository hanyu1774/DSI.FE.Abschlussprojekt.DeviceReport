"""Incidents & Service Requests: Liste, Zusammenfassung, Zeitverlauf, Clustering."""

from __future__ import annotations

from fastapi import APIRouter, Query

from core.database import db
from models.schema_models import Ticket, TicketCluster, TicketResponseTimes, TicketSummary, TrendPoint
from workflows.ticket_workflows import (
    ListTicketsWorkflow,
    TicketClustersWorkflow,
    TicketResponseTimesWorkflow,
    TicketSummaryWorkflow,
    TicketTrendWorkflow,
)

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/summary", response_model=TicketSummary)
def summary() -> TicketSummary:
    return TicketSummaryWorkflow().run(db.engine)


@router.get("/trend", response_model=list[TrendPoint])
def trend(interval: str = Query(default="week", pattern="^(day|week|month)$")) -> list[TrendPoint]:
    return TicketTrendWorkflow().run(db.engine, interval=interval)


@router.get("/response-times", response_model=TicketResponseTimes)
def response_times() -> TicketResponseTimes:
    return TicketResponseTimesWorkflow().run(db.engine)


@router.get("/clusters", response_model=list[TicketCluster])
def clusters(n_clusters: int = Query(default=5, ge=2, le=20)) -> list[TicketCluster]:
    return TicketClustersWorkflow().run(db.engine, n_clusters)


@router.get("", response_model=list[Ticket])
def list_tickets(
    limit: int = Query(default=100, ge=1, le=1000),
    machine_id: int | None = None,
    ticket_type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
) -> list[Ticket]:
    return ListTicketsWorkflow().run(
        db.engine,
        machine_id=machine_id,
        ticket_type=ticket_type,
        priority=priority,
        status=status,
        limit=limit,
    )
