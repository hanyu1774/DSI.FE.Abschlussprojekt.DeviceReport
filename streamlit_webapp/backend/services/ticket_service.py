"""
Ticket-bezogene EDA-/Reporting-Funktionen fuer Incidents & Service Requests:
Liste (mit Filtern), Zusammenfassung fuer Kreis-/Balkendiagramme,
Zeitverlauf und durchschnittliche Bearbeitungszeiten.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sqlalchemy import select
from sqlalchemy.engine import Engine

from models import ErrorCode, Machine, Technician, Ticket, TicketType
from services.db_utils import load_dataframe, to_json_records

# Equivalent of the old TICKETS_QUERY string constant. Built from the real
# model columns, so `t.description` (which doesn't exist - the column is
# `ticket_description`) and `tt.name` / `m.name` (which are actually
# `ticket_type_name` / `machine_name`) can't silently typo their way in.
TICKETS_SELECT = (
    select(
        Ticket.ticket_id.label("id"),
        TicketType.ticket_type_name.label("ticket_type"),
        Ticket.machine_id,
        Machine.machine_name.label("machine_name"),
        Ticket.error_code,
        ErrorCode.error_code_description.label("error_description"),
        ErrorCode.category.label("error_category"),
        Technician.first_name.label("technician_first_name"),
        Technician.last_name.label("technician_last_name"),
        Ticket.priority,
        Ticket.ticket_description.label("description"),
        Ticket.created_at,
        Ticket.assigned_at,
        Ticket.resolved_at,
        Ticket.closed_at,
    )
    .join(TicketType, TicketType.ticket_type_id == Ticket.ticket_type_id)
    .join(Machine, Machine.machine_id == Ticket.machine_id)
    .outerjoin(ErrorCode, ErrorCode.error_code == Ticket.error_code)
    .outerjoin(Technician, Technician.technician_id == Ticket.technician_id)
)

STATUS_OPEN = "Offen"
STATUS_IN_PROGRESS = "In Bearbeitung"
STATUS_RESOLVED = "Gel\u00f6st"
STATUS_CLOSED = "Geschlossen"

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _load_tickets(engine: Engine) -> pd.DataFrame:
    df = load_dataframe(TICKETS_SELECT, engine)

    for col in ("created_at", "assigned_at", "resolved_at", "closed_at"):
        df[col] = pd.to_datetime(df[col])

    technician = (
        df["technician_first_name"].fillna("") + " " + df["technician_last_name"].fillna("")
    ).str.strip()
    df["technician"] = technician.replace("", None)
    df = df.drop(columns=["technician_first_name", "technician_last_name"])

    # Status wird aus den vorhandenen Zeitstempeln abgeleitet (siehe die
    # CHECK-Constraints der Tabelle: created <= assigned <= resolved <= closed).
    conditions = [df["closed_at"].notna(), df["resolved_at"].notna(), df["assigned_at"].notna()]
    choices = [STATUS_CLOSED, STATUS_RESOLVED, STATUS_IN_PROGRESS]
    df["status"] = np.select(conditions, choices, default=STATUS_OPEN)

    df["resolution_hours"] = ((df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600).round(1)

    return df


TICKET_COLUMNS = [
    "id", "ticket_type", "machine_id", "machine_name", "error_code",
    "error_description", "technician", "priority", "status", "description",
    "created_at", "assigned_at", "resolved_at", "closed_at", "resolution_hours",
]


def list_tickets(
    engine: Engine,
    *,
    machine_id: int | None = None,
    ticket_type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    df = _load_tickets(engine)

    if machine_id is not None:
        df = df[df["machine_id"] == machine_id]
    if ticket_type is not None:
        df = df[df["ticket_type"] == ticket_type]
    if priority is not None:
        df = df[df["priority"] == priority]
    if status is not None:
        df = df[df["status"] == status]

    df = df.sort_values("created_at", ascending=False).head(limit)
    return to_json_records(df, TICKET_COLUMNS)


def get_summary(engine: Engine) -> dict:
    """Aggregierte Kennzahlen fuer Dashboard-Kacheln sowie Kreis-/
    Balkendiagramme (nach Typ, Prioritaet, Status, Fehlerkategorie)."""
    df = _load_tickets(engine)

    def value_counts_list(series: pd.Series) -> list[dict]:
        return [{"name": str(name), "count": int(count)} for name, count in series.value_counts().items()]

    category_series = df["error_category"].fillna("Ohne Fehlercode")

    return {
        "total": int(len(df)),
        "open_count": int((df["status"] != STATUS_CLOSED).sum()),
        "critical_count": int((df["priority"] == "critical").sum()),
        "by_type": value_counts_list(df["ticket_type"]),
        "by_priority": sorted(
            value_counts_list(df["priority"]),
            key=lambda item: PRIORITY_ORDER.get(item["name"], 99),
        ),
        "by_status": value_counts_list(df["status"]),
        "by_category": value_counts_list(category_series),
    }


def get_trend(engine: Engine, interval: str = "week") -> list[dict]:
    """Anzahl neu erstellter Tickets je Zeitintervall, aufgeteilt nach Typ."""
    df = _load_tickets(engine)
    freq = {"day": "D", "week": "W-MON", "month": "MS"}.get(interval, "W-MON")

    grouped = (
        df.set_index("created_at")
        .groupby([pd.Grouper(freq=freq), "ticket_type"])
        .size()
        .unstack(fill_value=0)
    )
    for col in ("Incident", "Service Request"):
        if col not in grouped.columns:
            grouped[col] = 0

    grouped["total"] = grouped["Incident"] + grouped["Service Request"]
    grouped = grouped.reset_index().rename(
        columns={
            "created_at": "period",
            "Incident": "incident_count",
            "Service Request": "service_request_count",
        }
    )
    grouped["period"] = grouped["period"].dt.strftime("%Y-%m-%d")

    return grouped[["period", "incident_count", "service_request_count", "total"]].to_dict("records")


def _round_or_none(value: float) -> float | None:
    if pd.isna(value):
        return None
    return round(float(value), 1)


def get_response_times(engine: Engine) -> dict:
    """Durchschnittliche Zeit bis Zuweisung/Loesung/Abschluss, gesamt und je Prioritaet."""
    df = _load_tickets(engine).copy()
    df["time_to_assign_hours"] = (df["assigned_at"] - df["created_at"]).dt.total_seconds() / 3600
    df["time_to_resolve_hours"] = (df["resolved_at"] - df["created_at"]).dt.total_seconds() / 3600
    df["time_to_close_hours"] = (df["closed_at"] - df["created_at"]).dt.total_seconds() / 3600

    def summarize(subset: pd.DataFrame, label: str) -> dict:
        return {
            "label": label,
            "avg_time_to_assign_hours": _round_or_none(subset["time_to_assign_hours"].mean()),
            "avg_time_to_resolve_hours": _round_or_none(subset["time_to_resolve_hours"].mean()),
            "avg_time_to_close_hours": _round_or_none(subset["time_to_close_hours"].mean()),
            "ticket_count": int(len(subset)),
        }

    overall = summarize(df, "Gesamt")
    by_priority = [summarize(group, str(priority)) for priority, group in df.groupby("priority")]
    by_priority.sort(key=lambda item: PRIORITY_ORDER.get(item["label"], 99))

    return {"overall": overall, "by_priority": by_priority}
