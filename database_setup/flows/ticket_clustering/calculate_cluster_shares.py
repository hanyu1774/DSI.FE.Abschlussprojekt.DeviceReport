"""Flow: calculates each cluster's share of tickets and of total downtime."""
from models.ticket import Ticket
from models.clustering_result import ClusteringResult
from models.cluster_result import ClusterResult


class CalculateClusterShares:
    """Classic Pareto logic: 'cluster X causes Y% of downtime, despite only
    Z% of tickets' - derived automatically from free text instead of from a
    manually maintained category column."""

    def run(self, tickets: list[Ticket], clustering: ClusteringResult,
            labels_by_cluster: dict[int, str], downtime_by_ticket_id: dict[int, float],
            n_clusters: int) -> list[ClusterResult]:
        total_downtime = sum(downtime_by_ticket_id.values()) or 1.0
        total_tickets = len(tickets) or 1

        results = []
        for cluster_id in range(n_clusters):
            indices = [i for i, label in enumerate(clustering.labels) if label == cluster_id]
            cluster_tickets = [tickets[i] for i in indices]
            cluster_downtime = sum(downtime_by_ticket_id[t.id] for t in cluster_tickets)

            result = ClusterResult()
            result.cluster = cluster_id
            result.label = labels_by_cluster[cluster_id]
            result.ticket_count = len(cluster_tickets)
            result.ticket_share_percent = round(len(cluster_tickets) / total_tickets * 100, 1)
            result.downtime_share_percent = round(cluster_downtime / total_downtime * 100, 1)
            result.example_ticket = cluster_tickets[0].description if cluster_tickets else ""
            results.append(result)

        results.sort(key=lambda r: r.downtime_share_percent or 0, reverse=True)
        return results
