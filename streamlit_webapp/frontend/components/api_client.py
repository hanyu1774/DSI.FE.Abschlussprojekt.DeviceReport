"""
API-Client fuer das FastAPI-Backend.

`ApiClient` kapselt die Basis-URL der Verbindung zum Backend - das
Frontend-Pendant zum `Database`-Connection-String-Muster im Backend
(siehe backend/database.py: dort wird der Connection String gekapselt
und wiederverwendet, hier ist es die Basis-URL). Die Instanz `api`
weiter unten wird von allen Ladefunktionen dieser Datei sowie den
einzelnen Seiten wiederverwendet.
"""

from __future__ import annotations

from typing import Any

import requests
import streamlit

API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 15.0


class ApiClient:
    """Kapselt die Basis-URL der Reporting-API und stellt get/post bereit."""

    def __init__(self, base_url: str, timeout: float = REQUEST_TIMEOUT) -> None:
        self.base_url = base_url
        self.timeout = timeout

    def get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = requests.get(f"{self.base_url}{endpoint}", params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError:
            streamlit.error(
                "Die FastAPI ist nicht erreichbar. Bitte zuerst den API-Server starten "
                "(`uvicorn main:app`, siehe README).",
                icon=":material/cloud_off:",
            )
        except requests.Timeout:
            streamlit.error("Die API-Anfrage hat zu lange gedauert.", icon=":material/timer_off:")
        except requests.HTTPError:
            streamlit.error(f"API-Fehler: {response.text}", icon=":material/error:")
        except requests.RequestException as error:
            streamlit.error(f"Verbindungsfehler: {error}", icon=":material/error:")
        return None

    def post(self, endpoint: str, payload: dict[str, Any]) -> Any:
        try:
            response = requests.post(f"{self.base_url}{endpoint}", json=payload, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.ConnectionError:
            streamlit.error(
                "Die FastAPI ist nicht erreichbar. Bitte zuerst den API-Server starten "
                "(`uvicorn main:app`, siehe README).",
                icon=":material/cloud_off:",
            )
        except requests.Timeout:
            streamlit.error("Die API-Anfrage hat zu lange gedauert.", icon=":material/timer_off:")
        except requests.HTTPError:
            streamlit.error(f"API-Fehler: {response.text}", icon=":material/error:")
        except requests.RequestException as error:
            streamlit.error(f"Verbindungsfehler: {error}", icon=":material/error:")
        return None


# Einzige Instanz der Anwendung - analog zu `db` in backend/database.py.
api = ApiClient(base_url=API_BASE_URL)


# ---------------------------------------------------------------------------
# Gecachte Ladefunktionen je Ressource. Kurze TTL: Daten bleiben nah an
# "live", ohne bei jedem Rerun (jeder Widget-Interaktion) die API neu zu
# belasten. Reine Stammdaten (Hallen, Maschinentypen) aendern sich praktisch
# nie und bekommen daher eine laengere TTL.
# ---------------------------------------------------------------------------


@streamlit.cache_data(ttl="60s")
def load_machines() -> list[dict]:
    result = api.get("/machines")
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="5m")
def load_halls() -> list[dict]:
    result = api.get("/halls")
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="5m")
def load_machine_types() -> list[dict]:
    result = api.get("/machine-types")
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="60s")
def load_technicians() -> list[dict]:
    result = api.get("/technicians")
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="10m")
def load_error_codes() -> list[dict]:
    result = api.get("/error-codes")
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="60s")
def load_error_rate() -> list[dict]:
    result = api.get("/kpi/error-rate")
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="60s")
def load_availability() -> list[dict]:
    result = api.get("/kpi/availability")
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="60s")
def load_mttr_mtbf() -> list[dict]:
    result = api.get("/kpi/mttr-mtbf")
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="60s")
def load_ticket_summary() -> dict:
    result = api.get("/tickets/summary")
    return result if isinstance(result, dict) else {}


@streamlit.cache_data(ttl="60s")
def load_ticket_trend(interval: str = "week") -> list[dict]:
    result = api.get("/tickets/trend", params={"interval": interval})
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="60s")
def load_response_times() -> dict:
    result = api.get("/tickets/response-times")
    return result if isinstance(result, dict) else {}


@streamlit.cache_data(ttl="30s", max_entries=50)
def load_tickets(
    limit: int = 100,
    machine_id: int | None = None,
    ticket_type: str | None = None,
    priority: str | None = None,
    status: str | None = None,
) -> list[dict]:
    params: dict[str, Any] = {"limit": limit}
    if machine_id is not None:
        params["machine_id"] = machine_id
    if ticket_type is not None:
        params["ticket_type"] = ticket_type
    if priority is not None:
        params["priority"] = priority
    if status is not None:
        params["status"] = status
    result = api.get("/tickets", params=params)
    return result if isinstance(result, list) else []


@streamlit.cache_data(ttl="5m")
def load_clusters(n_clusters: int) -> list[dict]:
    result = api.get("/tickets/clusters", params={"n_clusters": n_clusters})
    return result if isinstance(result, list) else []


def load_machine_events(machine_id: int, start: str | None = None, end: str | None = None) -> list[dict]:
    # Bewusst nicht gecacht: haengt vom interaktiv gewaehlten Datumsbereich
    # ab und wird erst nach Knopfdruck geladen, nicht bei jedem Rerun.
    params: dict[str, Any] = {}
    if start:
        params["start"] = start
    if end:
        params["end"] = end
    result = api.get(f"/machines/{machine_id}/events", params=params)
    return result if isinstance(result, list) else []


def load_measures() -> list[dict]:
    # Bewusst nicht gecacht, damit eine neu gespeicherte Massnahme sofort
    # in der Liste erscheint.
    result = api.get("/measures")
    return result if isinstance(result, list) else []


def create_measure(machine_id: int, description: str, start_date: str) -> dict | None:
    return api.post(
        "/measures",
        {"machine_id": machine_id, "description": description, "start_date": start_date},
    )
