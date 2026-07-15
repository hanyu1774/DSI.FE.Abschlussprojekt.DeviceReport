"""
Workflow: SeedMockDataWorkflow.

A separate workflow from ProductionReportingWorkflow on purpose: seeding the
database with demo data is a different application than serving the API
(it runs once, offline, before the API starts), not another use case the
running API needs to expose. main.py never imports this.

Run directly:  python -m workflows.seed_mock_data_workflow
"""
import random
from datetime import datetime

import numpy
from sqlalchemy.engine import Connection

from flows.persistence.connect_with_database import ConnectWithDatabase
from flows.persistence.create_all_tables import CreateAllTables
from flows.mock_data.generate_machines import GenerateMachines
from flows.mock_data.generate_error_codes import GenerateErrorCodes
from flows.mock_data.generate_events_for_machine import GenerateEventsForMachine
from flows.mock_data.generate_tickets_for_events import GenerateTicketsForEvents
from flows.persistence.save_machines import SaveMachines
from flows.persistence.save_error_codes import SaveErrorCodes
from flows.persistence.save_events import SaveEvents
from flows.persistence.save_tickets import SaveTickets
from flows.persistence.save_measure import SaveMeasure

from models.machine import Machine
from models.measure import Measure


class SeedMockDataWorkflow:
    """
    Orchestrates: build master data -> persist it -> per machine, generate
    events & persist them -> generate tickets for those events & persist
    them -> record one demo measure whose effect becomes visible through
    Feature 1 later.
    """


    def run(self) -> None:

        START_DATE = datetime(2026, 1, 1)
        END_DATE = datetime(2026, 6, 28)

        # Demo scenario for Feature 1: this measure visibly lowers the failure rate
        MEASURE_MACHINE_NAME = "Paketroboter-02"
        MEASURE_START_DATE = datetime(2026, 4, 1)
        MEASURE_EFFECT_FACTOR = 0.35
        MEASURE_DESCRIPTION = "Vorbeugende Wartung der Sensorik + Neukalibrierung"
        random.seed(42)
        numpy.random.seed(42)

        engine = ConnectWithDatabase().run()
        CreateAllTables().run(engine)

        with engine.begin() as connection:
            machines = GenerateMachines().run()
            error_codes = GenerateErrorCodes().run()

            SaveMachines().run(connection, machines)
            SaveErrorCodes().run(connection, error_codes)

            error_codes_by_type = self._group_by_machine_type(error_codes)
            error_codes_by_code = {ec.code: ec for ec in error_codes}

            total_events, total_tickets = 0, 0
            for machine in machines:
                events = GenerateEventsForMachine().run(
                    machine=machine,
                    valid_error_codes=error_codes_by_type[machine.machine_type],
                    start_date=START_DATE,
                    end_date=END_DATE,
                    measure_machine_name=MEASURE_MACHINE_NAME,
                    measure_start_date=MEASURE_START_DATE,
                    measure_effect_factor=MEASURE_EFFECT_FACTOR,
                )
                SaveEvents().run(connection, events)

                tickets = GenerateTicketsForEvents().run(events, machine.name, error_codes_by_code)
                SaveTickets().run(connection, tickets)

                total_events += len(events)
                total_tickets += len(tickets)

            self._save_demo_measure(connection, machines, MEASURE_MACHINE_NAME,
                                     MEASURE_DESCRIPTION, MEASURE_START_DATE)

        print(f"OK - {len(machines)} machines, {total_events} events, {total_tickets} tickets created.")
        print("Database: analytic_database.db")

    def _group_by_machine_type(self, error_codes):
        grouped = {}
        for ec in error_codes:
            grouped.setdefault(ec.applicable_machine_type, []).append(ec)
        return grouped

    def _save_demo_measure(self, connection: Connection, machines: list[Machine],
                            measure_machine_name: str, measure_description: str,
                            measure_start_date: datetime) -> None:
        target_machine = next(m for m in machines if m.name == measure_machine_name)
        measure = Measure()
        measure.machine_id = target_machine.id
        measure.description = measure_description
        measure.start_date = measure_start_date
        SaveMeasure().run(connection, measure)


if __name__ == "__main__":
    SeedMockDataWorkflow().run()
