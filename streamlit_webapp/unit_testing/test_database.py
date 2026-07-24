"""
Connection stability and data consistency tests.

Two different concerns, deliberately kept in one file since they're both
about core/database.py's contract with the rest of the app:

1. Stability: the Engine is a true Singleton (one shared pool for the whole
   process); each Session is a "Scoped Singleton" (independent per caller,
   but sees the same underlying data once committed).
2. Consistency: SQLite does not enforce foreign keys by default - core/
   database.py turns that on per-connection via PRAGMA. This file proves
   that setting is actually taking effect, and that every CHECK constraint
   declared in models/database_tables.py is actually enforced by the
   database itself, not just documented in a comment.
"""
from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from models.database_tables import ErrorCode, EventLog, Hall, Machine, MachineType, Measure, Technician, Ticket, TicketType


# ---------------------------------------------------------------------------
# Connection stability
# ---------------------------------------------------------------------------

def test_database_session_returns_independent_objects(engine, session_factory):
    from core.database import Database
    db = Database.__new__(Database)  # bypass __init__ - reuse the test engine instead of a real file
    db.connection_string = "unused"
    db.engine = engine
    db._session_factory = session_factory

    session_one = db.session()
    session_two = db.session()
    assert session_one is not session_two


def test_committed_data_is_visible_from_a_different_session(engine, session_factory):
    """The whole point of the Engine being a real Singleton: two separate,
    independent Sessions still see the same underlying data once one of
    them commits - they're two views onto one shared connection pool, not
    two isolated databases."""
    writer = session_factory()
    hall = Hall(hall_name="Halle Z")
    writer.add(hall)
    writer.commit()
    writer.close()

    reader = session_factory()
    found = reader.query(Hall).filter_by(hall_name="Halle Z").one_or_none()
    reader.close()
    assert found is not None


def test_get_db_closes_the_session_after_use(engine, session_factory, monkeypatch):
    from core import database as database_module

    monkeypatch.setattr(database_module.db, "engine", engine)
    monkeypatch.setattr(database_module.db, "_session_factory", session_factory)

    gen = database_module.get_db()
    session = next(gen)
    session.execute(Hall.__table__.select())  # start a transaction so there's something to close
    assert session.in_transaction()

    with pytest.raises(StopIteration):
        next(gen)  # exhausting the generator runs the finally: block

    # SQLAlchemy Sessions stay technically reusable after close() (it just
    # ends the transaction, doesn't disable the object) - in_transaction()
    # going back to False is the real signal that get_db()'s finally block ran.
    assert not session.in_transaction()


# ---------------------------------------------------------------------------
# Data consistency: foreign keys
# ---------------------------------------------------------------------------

def test_foreign_keys_are_enforced_not_just_declared(session: Session):
    """SQLite ignores foreign keys unless a connection explicitly turns
    them on - this proves core/database.py's PRAGMA actually takes effect,
    not just that the ForeignKey() is present in the model."""
    session.add(Machine(machine_name="Ghost", machine_type_id=999999, hall_id=999999,
                         manufacturer="Nobody", year_built=2020))
    with pytest.raises(IntegrityError):
        session.commit()


def test_measure_rejects_unknown_machine_id(session: Session):
    session.add(Measure(machine_id=999999, measure_description="x", start_date="2026-01-01"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_ticket_rejects_unknown_error_code(session: Session):
    hall = Hall(hall_name="H")
    mtype = MachineType(machine_type_name="T")
    session.add_all([hall, mtype])
    session.flush()
    machine = Machine(machine_name="M", machine_type_id=mtype.machine_type_id,
                       hall_id=hall.hall_id, manufacturer="X", year_built=2020)
    ttype = TicketType(ticket_type_name="Incident")
    session.add_all([machine, ttype])
    session.flush()

    session.add(Ticket(ticket_type_id=ttype.ticket_type_id, machine_id=machine.machine_id,
                        error_code="DOES-NOT-EXIST", priority="low",
                        ticket_description="x", created_at="2026-01-01 00:00:00"))
    with pytest.raises(IntegrityError):
        session.commit()


# ---------------------------------------------------------------------------
# Data consistency: CHECK constraints
# ---------------------------------------------------------------------------

@pytest.fixture()
def hall_and_type(session: Session):
    hall = Hall(hall_name="H")
    mtype = MachineType(machine_type_name="T")
    session.add_all([hall, mtype])
    session.flush()
    return hall, mtype


def test_machine_rejects_year_built_out_of_range(session: Session, hall_and_type):
    hall, mtype = hall_and_type
    session.add(Machine(machine_name="M", machine_type_id=mtype.machine_type_id,
                         hall_id=hall.hall_id, manufacturer="X", year_built=1800))
    with pytest.raises(IntegrityError):
        session.commit()


def test_technician_rejects_invalid_shift(session: Session):
    session.add(Technician(first_name="A", last_name="B", shift="Nachtschicht"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_error_code_rejects_invalid_severity(session: Session, hall_and_type):
    _, mtype = hall_and_type
    session.add(ErrorCode(error_code="E1", error_code_description="x", severity="apocalyptic",
                           category="Elektrik", machine_type_id=mtype.machine_type_id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_error_code_rejects_invalid_category(session: Session, hall_and_type):
    _, mtype = hall_and_type
    session.add(ErrorCode(error_code="E1", error_code_description="x", severity="low",
                           category="Weltraum", machine_type_id=mtype.machine_type_id))
    with pytest.raises(IntegrityError):
        session.commit()


def test_event_log_rejects_invalid_status(session: Session, hall_and_type):
    hall, mtype = hall_and_type
    machine = Machine(machine_name="M", machine_type_id=mtype.machine_type_id,
                       hall_id=hall.hall_id, manufacturer="X", year_built=2020)
    session.add(machine)
    session.flush()

    session.add(EventLog(machine_id=machine.machine_id, timestamp="2026-01-01 00:00:00",
                          status="on_fire", downtime_minutes=10.0))
    with pytest.raises(IntegrityError):
        session.commit()


def test_event_log_rejects_negative_downtime(session: Session, hall_and_type):
    hall, mtype = hall_and_type
    machine = Machine(machine_name="M", machine_type_id=mtype.machine_type_id,
                       hall_id=hall.hall_id, manufacturer="X", year_built=2020)
    session.add(machine)
    session.flush()

    session.add(EventLog(machine_id=machine.machine_id, timestamp="2026-01-01 00:00:00",
                          status="error", downtime_minutes=-5.0))
    with pytest.raises(IntegrityError):
        session.commit()


def test_ticket_rejects_invalid_priority(session: Session, hall_and_type):
    hall, mtype = hall_and_type
    machine = Machine(machine_name="M", machine_type_id=mtype.machine_type_id,
                       hall_id=hall.hall_id, manufacturer="X", year_built=2020)
    ttype = TicketType(ticket_type_name="Incident")
    session.add_all([machine, ttype])
    session.flush()

    session.add(Ticket(ticket_type_id=ttype.ticket_type_id, machine_id=machine.machine_id,
                        priority="meh", ticket_description="x", created_at="2026-01-01 00:00:00"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_ticket_rejects_assigned_before_created(session: Session, hall_and_type):
    hall, mtype = hall_and_type
    machine = Machine(machine_name="M", machine_type_id=mtype.machine_type_id,
                       hall_id=hall.hall_id, manufacturer="X", year_built=2020)
    ttype = TicketType(ticket_type_name="Incident")
    session.add_all([machine, ttype])
    session.flush()

    session.add(Ticket(ticket_type_id=ttype.ticket_type_id, machine_id=machine.machine_id,
                        priority="low", ticket_description="x",
                        created_at="2026-01-02 00:00:00", assigned_at="2026-01-01 00:00:00"))
    with pytest.raises(IntegrityError):
        session.commit()


def test_ticket_rejects_technician_without_assigned_at(session: Session, hall_and_type):
    """A technician can't be attached to a ticket that was never assigned -
    the schema encodes that business rule directly as a CHECK constraint."""
    hall, mtype = hall_and_type
    machine = Machine(machine_name="M", machine_type_id=mtype.machine_type_id,
                       hall_id=hall.hall_id, manufacturer="X", year_built=2020)
    ttype = TicketType(ticket_type_name="Incident")
    tech = Technician(first_name="A", last_name="B", shift="Frueh")
    session.add_all([machine, ttype, tech])
    session.flush()

    session.add(Ticket(ticket_type_id=ttype.ticket_type_id, machine_id=machine.machine_id,
                        technician_id=tech.technician_id, priority="low",
                        ticket_description="x", created_at="2026-01-01 00:00:00",
                        assigned_at=None))
    with pytest.raises(IntegrityError):
        session.commit()


def test_valid_data_is_accepted(session: Session, hall_and_type):
    """The flip side of every rejection test above - confirms the
    constraints reject bad data without also rejecting good data."""
    hall, mtype = hall_and_type
    machine = Machine(machine_name="M", machine_type_id=mtype.machine_type_id,
                       hall_id=hall.hall_id, manufacturer="X", year_built=2020)
    ttype = TicketType(ticket_type_name="Incident")
    tech = Technician(first_name="A", last_name="B", shift="Frueh")
    session.add_all([machine, ttype, tech])
    session.flush()

    session.add(Ticket(ticket_type_id=ttype.ticket_type_id, machine_id=machine.machine_id,
                        technician_id=tech.technician_id, priority="low",
                        ticket_description="x", created_at="2026-01-01 00:00:00",
                        assigned_at="2026-01-01 01:00:00"))
    session.commit()  # should not raise
