from __future__ import annotations

from sqlalchemy.engine import Engine

from flows.cluster_ticket_texts import ClusterTicketTexts
from flows.compute_response_times import ComputeResponseTimes
from flows.compute_ticket_trend import ComputeTicketTrend
from flows.enrich_tickets import EnrichTickets
from flows.filter_tickets import FilterTickets
from flows.load_ticket_texts import LoadTicketTexts
from flows.load_tickets import LoadTickets
from flows.summarize_tickets import SummarizeTickets
from models.schema_models import (
    Ticket,
    TicketCluster,
    TicketResponseTimes,
    TicketSummary,
    TrendPoint,
)


class ListTicketsWorkflow:
    def run(
        self,
        engine: Engine,
        machine_id: int | None = None,
        ticket_type: str | None = None,
        priority: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[Ticket]:
        tickets_df = LoadTickets().run(engine)
        tickets_df = EnrichTickets().run(tickets_df)
        records = FilterTickets().run(
            tickets_df,
            machine_id=machine_id,
            ticket_type=ticket_type,
            priority=priority,
            status=status,
            limit=limit,
        )
        return [Ticket(**record) for record in records]


class TicketSummaryWorkflow:
    def run(self, engine: Engine) -> TicketSummary:
        tickets_df = LoadTickets().run(engine)
        tickets_df = EnrichTickets().run(tickets_df)
        summary = SummarizeTickets().run(tickets_df)
        return TicketSummary(**summary)


class TicketTrendWorkflow:
    def run(self, engine: Engine, interval: str = "week") -> list[TrendPoint]:
        tickets_df = LoadTickets().run(engine)
        records = ComputeTicketTrend().run(tickets_df, interval=interval)
        return [TrendPoint(**record) for record in records]


class TicketResponseTimesWorkflow:
    def run(self, engine: Engine) -> TicketResponseTimes:
        tickets_df = LoadTickets().run(engine)
        result = ComputeResponseTimes().run(tickets_df)
        return TicketResponseTimes(**result)


class TicketClustersWorkflow:
    def run(self, engine: Engine, n_clusters: int) -> list[TicketCluster]:
        descriptions_df = LoadTicketTexts().run(engine)
        clusters = ClusterTicketTexts().run(descriptions_df, n_clusters)
        return [TicketCluster(**cluster) for cluster in clusters]
