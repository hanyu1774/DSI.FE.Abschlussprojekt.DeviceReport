"""
Shared fixtures for the whole test suite.

Everything runs against an in-memory SQLite database (StaticPool, so every
connection opened from the same engine shares the same in-memory data
instead of each getting a blank database) - the real .db file is never
touched by these tests.

Why fixtures stay this plain: every Flow takes its dependency as a `run()`
argument (a Session or an Engine, sometimes just a DataFrame) rather than
through a constructor. That's the whole point of skipping Constructor
Injection here - there's nothing to wire up or mock, a fixture just hands
over a ready object and the test calls `.run(...)` on it directly.
"""
from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from models.database_tables import (
    Base,
    ErrorCode,
    EventLog,
    Hall,
    Machine,
    MachineType,
    Measure,
    Technician,
    Ticket,
    TicketType,
)


@pytest.fixture()
def engine() -> Engine:
    """A fresh, empty in-memory SQLite database per test."""
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(test_engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON;")
        cursor.close()

    Base.metadata.create_all(test_engine)
    return test_engine


@pytest.fixture()
def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


@pytest.fixture()
def session(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    s = session_factory()
    yield s
    s.close()


def _seed(session: Session) -> None:
    """A small, hand-picked dataset covering every table and every join
    used across the Flows: 2 halls, 2 machine types, 3 machines,
    2 technicians, 2 error codes, 1 measure, 3 events, 2 ticket types,
    and 3 tickets in three different lifecycle states (open / in-progress /
    closed) so status-derivation logic has something real to chew on."""
    hall_a = Hall(hall_name="Halle A")
    hall_b = Hall(hall_name="Halle B")
    dryer_type = MachineType(machine_type_name="Trockner")
    tunnel_type = MachineType(machine_type_name="Kuehltunnel")
    session.add_all([hall_a, hall_b, dryer_type, tunnel_type])
    session.flush()

    m1 = Machine(machine_name="Trockner-01", machine_type_id=dryer_type.machine_type_id,
                 hall_id=hall_a.hall_id, manufacturer="Veit", year_built=2018)
    m2 = Machine(machine_name="Trockner-02", machine_type_id=dryer_type.machine_type_id,
                 hall_id=hall_a.hall_id, manufacturer="Veit", year_built=2020)
    m3 = Machine(machine_name="Kuehltunnel-01", machine_type_id=tunnel_type.machine_type_id,
                 hall_id=hall_b.hall_id, manufacturer="Kolbe", year_built=2019)
    session.add_all([m1, m2, m3])
    session.flush()

    tech_a = Technician(first_name="Ada", last_name="Lovelace", shift="Frueh")
    tech_b = Technician(first_name="Grace", last_name="Hopper", shift="Spaet")
    session.add_all([tech_a, tech_b])

    ec1 = ErrorCode(error_code="E101", error_code_description="Ueberhitzung",
                     severity="high", category="Elektrik", machine_type_id=dryer_type.machine_type_id)
    ec2 = ErrorCode(error_code="E202", error_code_description="Sensorausfall",
                     severity="medium", category="Sensorik", machine_type_id=tunnel_type.machine_type_id)
    session.add_all([ec1, ec2])
    session.flush()

    session.add(Measure(machine_id=m1.machine_id, measure_description="Filterwechsel", start_date="2026-06-01"))

    session.add_all([
        EventLog(machine_id=m1.machine_id, timestamp="2026-06-01 08:00:00", status="error",
                 error_code=ec1.error_code, downtime_minutes=45.0),
        EventLog(machine_id=m1.machine_id, timestamp="2026-06-02 09:00:00", status="maintenance",
                 error_code=None, downtime_minutes=15.0),
        EventLog(machine_id=m2.machine_id, timestamp="2026-06-03 10:00:00", status="offline",
                 error_code=None, downtime_minutes=30.0),
    ])

    incident = TicketType(ticket_type_name="Incident")
    request = TicketType(ticket_type_name="Service Request")
    session.add_all([incident, request])
    session.flush()

    session.add_all([
        Ticket(ticket_type_id=incident.ticket_type_id, machine_id=m1.machine_id,
               error_code=ec1.error_code, technician_id=None, priority="critical",
               ticket_description="Trockner faellt staendig aus", created_at="2026-06-01 08:05:00"),
        Ticket(ticket_type_id=incident.ticket_type_id, machine_id=m2.machine_id,
               error_code=None, technician_id=tech_a.technician_id, priority="medium",
               ticket_description="Ungewoehnliches Geraeusch", created_at="2026-06-02 10:00:00",
               assigned_at="2026-06-02 11:00:00"),
        Ticket(ticket_type_id=request.ticket_type_id, machine_id=m3.machine_id,
               error_code=ec2.error_code, technician_id=tech_b.technician_id, priority="low",
               ticket_description="Vorsorgliche Wartung", created_at="2026-06-03 07:00:00",
               assigned_at="2026-06-03 08:00:00", resolved_at="2026-06-03 12:00:00",
               closed_at="2026-06-03 13:00:00"),
    ])
    session.commit()


@pytest.fixture()
def seeded_engine(engine: Engine, session_factory: sessionmaker[Session]) -> Engine:
    """Same engine as `engine`, but with the fixture dataset already
    committed - for Flows that take an Engine (the pandas-based ones)."""
    s = session_factory()
    _seed(s)
    s.close()
    return engine


@pytest.fixture()
def seeded_session(seeded_engine: Engine, session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """A fresh Session opened onto the already-seeded database - for Flows
    that take a Session (the ORM-based ones)."""
    s = session_factory()
    yield s
    s.close()


@pytest.fixture()
def client(seeded_engine: Engine, session_factory: sessionmaker[Session], monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """A TestClient wired to the seeded in-memory database instead of the
    real one - overrides get_db (used by reference.py/measures.py) and
    monkeypatches core.database.db.engine (used directly by kpis.py/tickets.py)."""
    from core.database import db, get_db
    from main import application

    def override_get_db() -> Iterator[Session]:
        s = session_factory()
        try:
            yield s
        finally:
            s.close()

    application.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(db, "engine", seeded_engine)

    with TestClient(application) as test_client:
        yield test_client

    application.dependency_overrides.clear()
