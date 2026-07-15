"""
Workflow: ProductionReportingWorkflow.

This is the single Workflow that main.py is allowed to know about. It acts
as a "Flow provider" (compare the TravelExpenseService example in the Flow
Design document): it wires together whichever Flows a given use case needs
and exposes one method per use case. main.py never talks to a Flow or to
the database directly - it only ever calls a method on this one object.
"""
from datetime import datetime
from typing import Optional

from flows.persistence.connect_with_database import ConnectWithDatabase
from flows.persistence.load_machines import LoadMachines
from flows.persistence.load_events import LoadEvents
from flows.persistence.load_tickets import LoadTickets
from flows.persistence.load_error_codes import LoadErrorCodes
from flows.persistence.load_measures import LoadMeasures
from flows.persistence.save_measure import SaveMeasure

from flows.kpi.calculate_error_rate_per_machine import CalculateErrorRatePerMachine
from flows.kpi.calculate_availability_per_machine import CalculateAvailabilityPerMachine
from flows.kpi.calculate_mttr_mtbf_per_machine import CalculateMttrMtbfPerMachine

from flows.effect_analysis.calculate_before_after_statistics import CalculateBeforeAfterStatistics
from flows.effect_analysis.run_significance_test import RunSignificanceTest

from flows.ticket_clustering.calculate_ticket_downtime import CalculateTicketDowntime
from flows.ticket_clustering.clean_ticket_text import CleanTicketText
from flows.ticket_clustering.vectorize_ticket_text import VectorizeTicketText
from flows.ticket_clustering.cluster_tickets import ClusterTickets
from flows.ticket_clustering.label_clusters import LabelClusters
from flows.ticket_clustering.calculate_cluster_shares import CalculateClusterShares

from models.machine import Machine
from models.event import Event
from models.ticket import Ticket
from models.measure import Measure
from models.effect_result import EffectResult
from models.cluster_result import ClusterResult
from models.error_rate_result import ErrorRateResult
from models.availability_result import AvailabilityResult
from models.mttr_mtbf_result import MttrMtbfResult


class ProductionReportingWorkflow:
    def __init__(self):
        self._engine = ConnectWithDatabase().run()

    # -- machines / events / tickets -----------------------------------

    def get_machines(self) -> list[Machine]:
        with self._engine.connect() as connection:
            return LoadMachines().run(connection)

    def get_machine_events(self, machine_id: int, start: Optional[datetime] = None,
                            end: Optional[datetime] = None) -> list[Event]:
        with self._engine.connect() as connection:
            return LoadEvents().run(connection, machine_id=machine_id, start=start, end=end)

    def get_tickets(self, machine_id: Optional[int] = None, limit: int = 50) -> list[Ticket]:
        with self._engine.connect() as connection:
            return LoadTickets().run(connection, machine_id=machine_id, limit=limit)

    # -- KPIs -------------------------------------------------------------

    def get_error_rate_kpi(self) -> list[ErrorRateResult]:
        with self._engine.connect() as connection:
            machines = LoadMachines().run(connection)
            events = LoadEvents().run(connection)
        return CalculateErrorRatePerMachine().run(machines, events)

    def get_availability_kpi(self) -> list[AvailabilityResult]:
        with self._engine.connect() as connection:
            machines = LoadMachines().run(connection)
            events = LoadEvents().run(connection)
        return CalculateAvailabilityPerMachine().run(machines, events)

    def get_mttr_mtbf_kpi(self) -> list[MttrMtbfResult]:
        with self._engine.connect() as connection:
            machines = LoadMachines().run(connection)
            tickets = LoadTickets().run(connection)
        return CalculateMttrMtbfPerMachine().run(machines, tickets)

    # -- Feature 1: measure tracking & effect analysis ---------------------

    def create_measure(self, machine_id: int, description: str,
                        start_date: datetime) -> Optional[tuple[str, Measure, EffectResult]]:
        """Returns None if the machine does not exist."""
        with self._engine.begin() as connection:
            matching_machines = LoadMachines().run(connection, machine_id=machine_id)
            if not matching_machines:
                return None

            measure = Measure()
            measure.machine_id = machine_id
            measure.description = description
            measure.start_date = start_date
            SaveMeasure().run(connection, measure)

            effect = self._calculate_measure_effect(connection, machine_id, start_date)

        return matching_machines[0].name, measure, effect

    def list_measures(self) -> list[tuple[str, Measure, EffectResult]]:
        with self._engine.connect() as connection:
            measures = LoadMeasures().run(connection)
            machines_by_id = {m.id: m for m in LoadMachines().run(connection)}

            return [
                (machines_by_id[m.machine_id].name, m,
                 self._calculate_measure_effect(connection, m.machine_id, m.start_date))
                for m in measures
            ]

    def _calculate_measure_effect(self, connection, machine_id: int, start_date: datetime) -> EffectResult:
        events = LoadEvents().run(connection, machine_id=machine_id)

        result = CalculateBeforeAfterStatistics().run(events, start_date)
        if result.note:
            return result

        result.t_test_p_value = RunSignificanceTest().run(events, start_date)
        result.is_significant_at_5_percent = bool(
            result.t_test_p_value is not None and result.t_test_p_value < 0.05
        )
        return result

    # -- Feature 2: NLP root-cause clustering ------------------------------

    def get_ticket_clusters(self, n_clusters: int = 5) -> list[ClusterResult]:
        with self._engine.connect() as connection:
            tickets = LoadTickets().run(connection)
            error_codes = LoadErrorCodes().run(connection)

        if len(tickets) < n_clusters:
            raise ValueError("Not enough tickets for this number of clusters")

        error_codes_by_code = {ec.code: ec for ec in error_codes}
        downtime_by_ticket_id = CalculateTicketDowntime().run(tickets, error_codes_by_code)

        descriptions = [t.description for t in tickets]
        cleaned_texts = CleanTicketText().run(descriptions)
        vectorization = VectorizeTicketText().run(cleaned_texts)
        clustering = ClusterTickets().run(vectorization, n_clusters)
        labels_by_cluster = LabelClusters().run(clustering, vectorization, n_clusters)

        return CalculateClusterShares().run(
            tickets, clustering, labels_by_cluster, downtime_by_ticket_id, n_clusters
        )
