"""
SQLAlchemy models — single source of truth for the schema, built directly
from analytic_database_v4.sql. Equivalent of your EF Core entity classes
(what you'd put in DbSet<T> properties on a DbContext).
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import CheckConstraint, ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Equivalent of EF Core's DbContext base for model metadata."""
    pass


class Hall(Base):
    __tablename__ = "halls"

    hall_id: Mapped[int] = mapped_column(primary_key=True)
    hall_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    machines: Mapped[List["Machine"]] = relationship(back_populates="hall")


class MachineType(Base):
    __tablename__ = "machine_types"

    machine_type_id: Mapped[int] = mapped_column(primary_key=True)
    machine_type_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    machines: Mapped[List["Machine"]] = relationship(back_populates="machine_type")
    error_codes: Mapped[List["ErrorCode"]] = relationship(back_populates="machine_type")


class Machine(Base):
    __tablename__ = "machines"
    __table_args__ = (
        CheckConstraint("year_built BETWEEN 1990 AND 2026", name="ck_machines_year_built"),
    )

    machine_id: Mapped[int] = mapped_column(primary_key=True)
    machine_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    machine_type_id: Mapped[int] = mapped_column(ForeignKey("machine_types.machine_type_id"))
    hall_id: Mapped[int] = mapped_column(ForeignKey("halls.hall_id"))
    manufacturer: Mapped[str] = mapped_column(String, nullable=False)
    year_built: Mapped[int] = mapped_column()

    machine_type: Mapped["MachineType"] = relationship(back_populates="machines")
    hall: Mapped["Hall"] = relationship(back_populates="machines")
    measures: Mapped[List["Measure"]] = relationship(back_populates="machine")
    events: Mapped[List["EventLog"]] = relationship(back_populates="machine")
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="machine")


class Technician(Base):
    __tablename__ = "technicians"
    __table_args__ = (
        CheckConstraint("shift IN ('Frueh','Spaet','Nacht')", name="ck_technicians_shift"),
    )

    technician_id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    shift: Mapped[str] = mapped_column(String, nullable=False)

    tickets: Mapped[List["Ticket"]] = relationship(back_populates="technician")


class ErrorCode(Base):
    __tablename__ = "error_codes"
    __table_args__ = (
        CheckConstraint("severity IN ('low','medium','high','critical')", name="ck_error_codes_severity"),
        CheckConstraint(
            "category IN ('Sensorik','Mechanik','Elektrik','Software','Kuehlung','Pneumatik')",
            name="ck_error_codes_category",
        ),
    )

    error_code: Mapped[str] = mapped_column(String, primary_key=True)
    error_code_description: Mapped[str] = mapped_column(String, nullable=False)
    severity: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=False)
    machine_type_id: Mapped[int] = mapped_column(ForeignKey("machine_types.machine_type_id"))

    machine_type: Mapped["MachineType"] = relationship(back_populates="error_codes")
    events: Mapped[List["EventLog"]] = relationship(back_populates="error_code_ref")
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="error_code_ref")


class Measure(Base):
    __tablename__ = "measures"

    measure_id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.machine_id"))
    measure_description: Mapped[str] = mapped_column(String, nullable=False)
    start_date: Mapped[str] = mapped_column(String, nullable=False)

    machine: Mapped["Machine"] = relationship(back_populates="measures")


class EventLog(Base):
    __tablename__ = "event_log"
    __table_args__ = (
        CheckConstraint("status IN ('error','maintenance','offline')", name="ck_event_log_status"),
        CheckConstraint("downtime_minutes IS NULL OR downtime_minutes >= 0", name="ck_event_log_downtime"),
    )

    event_log_id: Mapped[int] = mapped_column(primary_key=True)
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.machine_id"))
    timestamp: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    error_code: Mapped[Optional[str]] = mapped_column(ForeignKey("error_codes.error_code"))
    downtime_minutes: Mapped[Optional[float]] = mapped_column()

    machine: Mapped["Machine"] = relationship(back_populates="events")
    error_code_ref: Mapped[Optional["ErrorCode"]] = relationship(back_populates="events")


class TicketType(Base):
    __tablename__ = "ticket_types"

    ticket_type_id: Mapped[int] = mapped_column(primary_key=True)
    ticket_type_name: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    tickets: Mapped[List["Ticket"]] = relationship(back_populates="ticket_type")


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint("priority IN ('low','medium','high','critical')", name="ck_tickets_priority"),
        CheckConstraint("assigned_at IS NULL OR assigned_at >= created_at", name="ck_tickets_assigned_after_created"),
        CheckConstraint("resolved_at IS NULL OR resolved_at >= assigned_at", name="ck_tickets_resolved_after_assigned"),
        CheckConstraint("closed_at IS NULL OR closed_at >= created_at", name="ck_tickets_closed_after_created"),
        CheckConstraint(
            "technician_id IS NULL OR assigned_at IS NOT NULL",
            name="ck_tickets_technician_requires_assigned",
        ),
    )

    ticket_id: Mapped[int] = mapped_column(primary_key=True)
    ticket_type_id: Mapped[int] = mapped_column(ForeignKey("ticket_types.ticket_type_id"))
    machine_id: Mapped[int] = mapped_column(ForeignKey("machines.machine_id"))
    error_code: Mapped[Optional[str]] = mapped_column(ForeignKey("error_codes.error_code"))
    technician_id: Mapped[Optional[int]] = mapped_column(ForeignKey("technicians.technician_id"))
    priority: Mapped[str] = mapped_column(String, nullable=False)
    ticket_description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[str] = mapped_column(String, nullable=False)
    assigned_at: Mapped[Optional[str]] = mapped_column(String)
    resolved_at: Mapped[Optional[str]] = mapped_column(String)
    closed_at: Mapped[Optional[str]] = mapped_column(String)

    ticket_type: Mapped["TicketType"] = relationship(back_populates="tickets")
    machine: Mapped["Machine"] = relationship(back_populates="tickets")
    error_code_ref: Mapped[Optional["ErrorCode"]] = relationship(back_populates="tickets")
    technician: Mapped[Optional["Technician"]] = relationship(back_populates="tickets")
