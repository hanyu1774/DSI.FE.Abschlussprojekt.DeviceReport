"""Flow: generates the error/maintenance history for a single machine."""
from datetime import datetime, timedelta
from typing import Optional

import numpy

from models.machine import Machine
from models.error_code import ErrorCode
from models.event import Event


class GenerateEventsForMachine:
    """
    Generates event log entries for ONE machine over a time range.

    Error events are simulated as a Poisson process (more realistic than
    plain random()). A measure can optionally be supplied that lowers this
    machine's failure rate from a given start date onward (used for Feature 1).
    """

    class _Distributions:
        """Constants for the distributions - only relevant to this Flow."""
        PROBLEMATIC_MACHINES = {"Paketroboter-02": 0.55, "Foerderband-01": 0.45, "Kuehltunnel-01": 0.4}
        STANDARD_LAMBDA = 0.22
        MAINTENANCE_PROBABILITY_PER_DAY = 1 / 30

    def run(
        self,
        machine: Machine,
        valid_error_codes: list[ErrorCode],
        start_date: datetime,
        end_date: datetime,
        measure_machine_name: Optional[str] = None,
        measure_start_date: Optional[datetime] = None,
        measure_effect_factor: float = 1.0,
    ) -> list[Event]:
        events: list[Event] = []
        n_days = (end_date - start_date).days

        for day_offset in range(n_days):
            day = start_date + timedelta(days=day_offset)
            lam = self._lambda_for_day(machine.name, day, measure_machine_name,
                                        measure_start_date, measure_effect_factor)

            for _ in range(numpy.random.poisson(lam)):
                error_code_index = int(numpy.random.choice(len(valid_error_codes)))
                error_code = valid_error_codes[error_code_index]
                hour = int(numpy.clip(numpy.random.normal(13, 6), 0, 23))
                timestamp = day + timedelta(hours=hour, minutes=int(numpy.random.randint(0, 60)))
                downtime = self._sample_downtime(error_code.avg_downtime_minutes, hour)

                event = Event()
                event.machine_id = machine.id
                event.timestamp = timestamp
                event.status = "error"
                event.error_code = error_code.code
                event.downtime_minutes = round(downtime, 1)
                events.append(event)

            if numpy.random.random() < self._Distributions.MAINTENANCE_PROBABILITY_PER_DAY:
                event = Event()
                event.machine_id = machine.id
                event.timestamp = day + timedelta(hours=int(numpy.random.randint(6, 19)))
                event.status = "maintenance"
                event.downtime_minutes = round(float(numpy.random.uniform(20, 60)), 1)
                events.append(event)

        return events

    def _lambda_for_day(self, machine_name: str, day: datetime,
                         measure_machine_name: Optional[str],
                         measure_start_date: Optional[datetime],
                         measure_effect_factor: float) -> float:
        lam = self._Distributions.PROBLEMATIC_MACHINES.get(machine_name, self._Distributions.STANDARD_LAMBDA)
        if measure_machine_name == machine_name and measure_start_date and day >= measure_start_date:
            lam *= measure_effect_factor
        return lam

    def _sample_downtime(self, avg_downtime_minutes: float, hour: int) -> float:
        downtime = max(5.0, numpy.random.lognormal(numpy.log(avg_downtime_minutes), 0.4))
        is_night_shift = hour >= 22 or hour < 6
        return downtime * 1.15 if is_night_shift else downtime
