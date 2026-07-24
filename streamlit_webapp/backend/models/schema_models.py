
"""Pydantic-Modelle fuer die API-Responses (Requests/Responses der FastAPI-Routen)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Hall(BaseModel):
    id: int
    name: str


class MachineType(BaseModel):
    id: int
    name: str


class Machine(BaseModel):
    id: int
    name: str
    machine_type: str
    hall: str
    manufacturer: str
    year_built: int


class Technician(BaseModel):
    id: int
    first_name: str
    last_name: str
    shift: str


class ErrorCode(BaseModel):
    error_code: str
    description: str
    severity: str
    category: str
    machine_type: str


class MachineEvent(BaseModel):
    id: int
    timestamp: datetime
    status: str
    error_code: str | None = None
    error_description: str | None = None
    downtime_minutes: float | None = None


class ErrorRateKpi(BaseModel):
    machine_id: int
    machine_name: str
    error_count: int
    maintenance_count: int
    offline_count: int
    total_downtime_minutes: float


class AvailabilityKpi(BaseModel):
    machine_id: int
    machine_name: str
    availability_percent: float
    downtime_minutes: float
    period_days: float


class MttrMtbfKpi(BaseModel):
    machine_id: int
    machine_name: str
    failure_count: int
    mttr_minutes: float | None = None
    mtbf_hours: float | None = None


class Ticket(BaseModel):
    id: int
    ticket_type: str
    machine_id: int
    machine_name: str
    error_code: str | None = None
    error_description: str | None = None
    technician: str | None = None
    priority: str
    status: str
    description: str
    created_at: datetime
    assigned_at: datetime | None = None
    resolved_at: datetime | None = None
    closed_at: datetime | None = None
    resolution_hours: float | None = None


class CountItem(BaseModel):
    name: str
    count: int


class TicketSummary(BaseModel):
    total: int
    open_count: int
    critical_count: int
    by_type: list[CountItem]
    by_priority: list[CountItem]
    by_status: list[CountItem]
    by_category: list[CountItem]


class TrendPoint(BaseModel):
    period: str
    incident_count: int
    service_request_count: int
    total: int


class ResponseTimeStats(BaseModel):
    label: str
    avg_time_to_assign_hours: float | None = None
    avg_time_to_resolve_hours: float | None = None
    avg_time_to_close_hours: float | None = None
    ticket_count: int


class TicketResponseTimes(BaseModel):
    overall: ResponseTimeStats
    by_priority: list[ResponseTimeStats]


class TicketCluster(BaseModel):
    cluster_id: int
    size: int
    top_keywords: list[str]
    dominant_category: str | None = None
    example_descriptions: list[str]


class Measure(BaseModel):
    id: int
    machine_id: int
    machine_name: str
    description: str
    start_date: str


class MeasureCreate(BaseModel):
    machine_id: int
    description: str = Field(min_length=1, max_length=2000)
    start_date: str = Field(description="ISO-Datum, z. B. 2026-07-16")
