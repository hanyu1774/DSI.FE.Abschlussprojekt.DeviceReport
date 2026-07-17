"""
KPI-Berechnungen auf Basis von `event_log` / `machines` (pandas-EDA).

Alle Funktionen erwarten den Connection String explizit als Argument
(siehe `database.py` und `db_utils.py`), damit sie unabhaengig von
FastAPI aufrufbar und testbar bleiben.
"""

from __future__ import annotations

import pandas as pd

from services.db_utils import load_dataframe, to_json_records

EVENTS_QUERY = """
    SELECT e.machine_id, m.name AS machine_name, e.status,
           e.downtime_minutes, e.timestamp
    FROM event_log e
    JOIN machines m ON m.machine_id = e.machine_id
"""


def _load_events(connection_string: str) -> pd.DataFrame:
    df = load_dataframe(EVENTS_QUERY, connection_string)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


def get_error_rate(connection_string: str) -> list[dict]:
    """Fehler-/Wartungs-/Offline-Anzahl sowie Gesamtstillstand je Maschine."""
    events = _load_events(connection_string)

    counts = events.pivot_table(
        index=["machine_id", "machine_name"],
        columns="status",
        values="timestamp",
        aggfunc="count",
        fill_value=0,
    )
    for status_col, out_col in (
        ("error", "error_count"),
        ("maintenance", "maintenance_count"),
        ("offline", "offline_count"),
    ):
        counts[out_col] = counts[status_col] if status_col in counts.columns else 0

    downtime = (
        events.groupby(["machine_id", "machine_name"])["downtime_minutes"]
        .sum()
        .rename("total_downtime_minutes")
    )

    result = counts.join(downtime).reset_index()
    result["total_downtime_minutes"] = result["total_downtime_minutes"].round(1)
    result = result.sort_values("error_count", ascending=False)

    columns = [
        "machine_id", "machine_name", "error_count",
        "maintenance_count", "offline_count", "total_downtime_minutes",
    ]
    return to_json_records(result, columns)


def get_availability(connection_string: str) -> list[dict]:
    """Verfuegbarkeit je Maschine ueber den beobachteten Zeitraum.

    Verfuegbarkeit = 1 - (Stillstand durch 'error' + 'offline') / Gesamtzeitraum.
    Geplante Wartung ('maintenance') zaehlt nicht als Verfuegbarkeitsverlust,
    da sie geplant statt ungeplant/stoerungsbedingt ist.
    """
    events = _load_events(connection_string)
    if events.empty:
        return []

    period_minutes = (events["timestamp"].max() - events["timestamp"].min()).total_seconds() / 60
    period_days = round(period_minutes / (60 * 24), 1)

    unavailable = (
        events[events["status"].isin(["error", "offline"])]
        .groupby(["machine_id", "machine_name"])["downtime_minutes"]
        .sum()
        .rename("downtime_minutes")
        .reset_index()
    )

    machines = events[["machine_id", "machine_name"]].drop_duplicates()
    merged = machines.merge(unavailable, on=["machine_id", "machine_name"], how="left")
    merged["downtime_minutes"] = merged["downtime_minutes"].fillna(0.0).round(1)
    merged["availability_percent"] = (
        100 * (1 - merged["downtime_minutes"] / period_minutes)
    ).clip(lower=0, upper=100).round(2)
    merged["period_days"] = period_days

    merged = merged.sort_values("availability_percent")
    columns = ["machine_id", "machine_name", "availability_percent", "downtime_minutes", "period_days"]
    return to_json_records(merged, columns)


def get_mttr_mtbf(connection_string: str) -> list[dict]:
    """MTTR (mittlere Reparaturzeit) und MTBF (mittlere Zeit zwischen
    Ausfaellen) je Maschine, jeweils basierend auf 'error'-Events."""
    events = _load_events(connection_string)
    if events.empty:
        return []

    period_hours = (events["timestamp"].max() - events["timestamp"].min()).total_seconds() / 3600
    errors = events[events["status"] == "error"]

    failure_count = errors.groupby(["machine_id", "machine_name"]).size().rename("failure_count")
    mttr = errors.groupby(["machine_id", "machine_name"])["downtime_minutes"].mean().rename("mttr_minutes")

    machines = events[["machine_id", "machine_name"]].drop_duplicates().set_index(["machine_id", "machine_name"])
    result = machines.join(failure_count).join(mttr).reset_index()
    result["failure_count"] = result["failure_count"].fillna(0).astype(int)
    result["mttr_minutes"] = result["mttr_minutes"].round(1)
    result["mtbf_hours"] = result["failure_count"].apply(
        lambda n: round(period_hours / n, 1) if n > 0 else None
    )

    result = result.sort_values("failure_count", ascending=False)
    columns = ["machine_id", "machine_name", "failure_count", "mttr_minutes", "mtbf_hours"]
    return to_json_records(result, columns)
