"""Flow: generates tickets (with free text) for a portion of the error events."""
import random
from datetime import timedelta

import numpy

from models.event import Event
from models.error_code import ErrorCode
from models.ticket import Ticket


class GenerateTicketsForEvents:
    """
    Generates a ticket with realistic free text for a portion of the error
    events. The free-text templates use consistent domain vocabulary per
    root-cause category so that a later NLP clustering step (Feature 2) has
    a real chance of recovering the categories. Description text and
    technician names stay in German, since that is the realistic business
    language used by the (German) maintenance team this data simulates.
    """


    class _DescriptionTemplates:
        BY_CATEGORY = {
            "Sensor": [
                "Sensor an {m} liefert keine plausiblen Werte mehr",
                "Sensor an {m} verschmutzt, Kalibrierung verloren",
                "Sensor an {m} stark verschmutzt, Reinigung notwendig",
                "Sensor-Messwerte von {m} weichen deutlich vom Soll ab",
            ],
            "Mechanical": [
                "Verschleiss am Lager von {m} festgestellt, laeuft heiss",
                "Verschleiss am Antrieb von {m} festgestellt",
                "Verschleiss am Greifer von {m}, schliesst nicht mehr richtig",
                "Verschleiss an {m} festgestellt, Teil muss ausgetauscht werden",
                "Verschleiss und Leckage an {m} festgestellt, sofort melden",
            ],
            "Blockage": [
                "Foerderstrecke an {m} blockiert, Stillstand seit Schichtbeginn",
                "Stau und Blockade in der Uebergabe an {m}",
                "Foerderstrecke an {m} blockiert, Material staut sich",
            ],
            "Software": [
                "Steuerungssoftware von {m} abgestuerzt, Neustart erforderlich",
                "Steuerungssoftware an {m} hat Not-Stopp ausgeloest",
                "Steuerungssoftware-Kalibrierung an {m} fehlgeschlagen",
                "Steuerungssoftware von {m} reagiert nicht mehr",
            ],
            "Cooling": [
                "Kuehlung von {m} erreicht Solltemperatur nicht mehr",
                "Temperaturabweichung an {m} ueber Grenzwert",
                "Kuehlleistung von {m} durch Temperaturproblem reduziert",
            ],
        }

    def run(self, events: list[Event], machine_name: str,
            error_codes_by_code: dict[str, ErrorCode]) -> list[Ticket]:

        TICKET_PROBABILITY = 0.8
        TECHNICIANS = ["Mike Becker", "Sandra Klein", "Ali Demir", "Julia Hoffmann"]
        tickets: list[Ticket] = []
        for event in events:
            if event.status != "error" or not event.error_code or random.random() >= TICKET_PROBABILITY:
                continue

            error_code = error_codes_by_code[event.error_code]
            tickets.append(self._build_ticket(event, error_code, machine_name, TECHNICIANS))
        return tickets

    def _build_ticket(self, event: Event, error_code: ErrorCode, machine_name: str,
                       technicians: list[str]) -> Ticket:
        created = event.timestamp + timedelta(minutes=random.randint(1, 15))
        assigned = created + timedelta(minutes=random.randint(10, 240))
        repair_minutes = max(5.0, numpy.random.lognormal(numpy.log(error_code.avg_downtime_minutes), 0.35))
        resolved = assigned + timedelta(minutes=repair_minutes)
        closed = resolved + timedelta(minutes=random.randint(10, 600))

        template = random.choice(self._DescriptionTemplates.BY_CATEGORY[error_code.category])

        ticket = Ticket()
        ticket.machine_id = event.machine_id
        ticket.error_code = error_code.code
        ticket.description = template.format(m=machine_name)
        ticket.priority = error_code.severity
        ticket.technician = random.choice(technicians)
        ticket.created_at = created
        ticket.assigned_at = assigned
        ticket.resolved_at = resolved
        ticket.closed_at = closed
        return ticket
