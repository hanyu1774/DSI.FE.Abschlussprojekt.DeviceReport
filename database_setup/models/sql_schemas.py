"""
SQL schema definitions via SQLAlchemy Core.

This belongs to the Models layer: a Table() object holds no behavior and no
run() method - it purely describes the shape of data. That is exactly the
definition of a Model in Flow Design. There is no separate "infrastructure"
layer; if something doesn't act (Flow) and doesn't orchestrate (Workflow),
it's data, and data belongs here.

Deliberately built with SQLAlchemy Core (Table()), not the ORM. There is no
class inheriting from a declarative "Base" - no metaclass magic, no
relationship(), no Session tracking. Just plain data structures.
"""
from sqlalchemy import MetaData, Table, Column, Integer, String, Float, DateTime, ForeignKey

metadata = MetaData()

machines_table = Table(
    "machines", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("name", String, nullable=False),
    Column("machine_type", String, nullable=False),
    Column("hall", String, nullable=False),
    Column("manufacturer", String),
    Column("year_built", Integer),
)

error_codes_table = Table(
    "error_codes", metadata,
    Column("code", String, primary_key=True),
    Column("description", String),
    Column("severity", String),
    Column("category", String),
    Column("avg_downtime_minutes", Float),
    Column("applicable_machine_type", String),
)

events_table = Table(
    "event_log", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("machine_id", Integer, ForeignKey("machines.id")),
    Column("timestamp", DateTime),
    Column("status", String),
    Column("error_code", String, ForeignKey("error_codes.code"), nullable=True),
    Column("downtime_minutes", Float, nullable=True),
)

tickets_table = Table(
    "tickets", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("machine_id", Integer, ForeignKey("machines.id")),
    Column("error_code", String, ForeignKey("error_codes.code")),
    Column("description", String),
    Column("priority", String),
    Column("technician", String),
    Column("created_at", DateTime),
    Column("assigned_at", DateTime),
    Column("resolved_at", DateTime),
    Column("closed_at", DateTime),
)

measures_table = Table(
    "measures", metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("machine_id", Integer, ForeignKey("machines.id")),
    Column("description", String),
    Column("start_date", DateTime),
)
