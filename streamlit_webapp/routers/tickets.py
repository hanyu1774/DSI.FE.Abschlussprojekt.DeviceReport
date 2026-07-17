"""Incidents & Service Requests: Liste, Zusammenfassung, Zeitverlauf, Clustering."""

from __future__ import annotations

from fastapi import APIRouter, Query

from database import db
from schemas import Ticket, TicketCluster, TicketResponseTimes, TicketSummary, TrendPoint
from services import clustering_service, ticket_service

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get("/summary", response_model=TicketSummary)
def summary() -> dict:
    return ticket_service.get_summary(db.connection_string)


@router.get("/trend", response_model=list[TrendPoint])
def trend(interval: str = Query(default="week", pattern="^(day|week|month)$")) -> list[dict]:
    return ticket_service.get_trend(db.connection_string, interval=interval)


@router.get("/response-times", response_model=TicketResponseTimes)
def response_times() -> dict:
    return ticket_service.get_response_times(db.connection_string)


@router.get("/clusters", response_model=list[TicketCluster])
def clusters(n_clusters: int = Query(default=5, ge=2, le=20)) -> list[dict]:
    return clustering_service.cluster_tickets(db.connection_string, n_clusters=n_clusters)


@router.get("", response_model=list[Ticket])
def list_tickets(
    limit: int = Query(default=100, ge=1, le=1000),
    machine_id: int | None = None,
    ticket_type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
) -> list[dict]:
    return ticket_service.list_tickets(
        db.connection_string,
        machine_id=machine_id,
        ticket_type=ticket_type,
        priority=priority,
        status=status,
        limit=limit,
    )
