"""
Ticket-bezogene EDA-/Reporting-Funktionen fuer Incidents & Service Requests:
Liste (mit Filtern), Zusammenfassung fuer Kreis-/Balkendiagramme,
Zeitverlauf und durchschnittliche Bearbeitungszeiten.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from services.db_utils import load_dataframe, to_json_records

TICKETS_QUERY = """
    SELECT
        t.ticket_id AS id,
        tt.name AS ticket_type,
        t.machine_id,
        m.name AS machine_name,
        t.error_code,
        ec.description AS error_description,
        ec.category AS error_category,
        te.first_name AS technician_first_name,
        te.last_name AS technician_last_name,
        t.priority,
        t.description,
        t.created_at,
        t.assigned_at,
        t.resolved_at,
        t.closed_at
    FROM tickets t
    JOIN ticket_types tt ON tt.ticket_type_id = t.ticket_type_id
    JOIN machines m ON m.machine_id = t.machine_id
    LEFT JOIN error_codes ec ON ec.error_code = t.error_code
    LEFT JOIN technicians te ON te.technician_id = t.technician_id
"""

STATUS_OPEN = "Offen"
STATUS_IN_PROGRESS = "In Bearbeitung"
STATUS_RESOLVED = "Gel\u00f6st"
STATUS_CLOSED = "Geschlossen"

PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}


def _load_tickets(connection_string: str) -> pd.DataFrame:
    df = load_dataframe(TICKETS_QUERY, connection_string)

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
    connection_string: str,
    *,
    machine_id: int | None = None,
    ticket_type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict]:
    df = _load_tickets(connection_string)

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


def get_summary(connection_string: str) -> dict:
    """Aggregierte Kennzahlen fuer Dashboard-Kacheln sowie Kreis-/
    Balkendiagramme (nach Typ, Prioritaet, Status, Fehlerkategorie)."""
    df = _load_tickets(connection_string)

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


def get_trend(connection_string: str, interval: str = "week") -> list[dict]:
    """Anzahl neu erstellter Tickets je Zeitintervall, aufgeteilt nach Typ."""
    df = _load_tickets(connection_string)
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


def get_response_times(connection_string: str) -> dict:
    """Durchschnittliche Zeit bis Zuweisung/Loesung/Abschluss, gesamt und je Prioritaet."""
    df = _load_tickets(connection_string).copy()
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
