"""
Streamlit frontend for the Production Hall Reporting API.

Data flow:
Streamlit -> FastAPI -> ProductionReportingWorkflow -> Flows -> SQLite
"""

from typing import Any

import pandas as pd
import requests
import streamlit as st
import altair as alt

API_BASE_URL = "http://127.0.0.1:8000"
REQUEST_TIMEOUT = 15

st.set_page_config(
    page_title="Production Hall Reporting",
    page_icon="🏭",
    layout="wide",
)


def api_get(endpoint: str, params: dict[str, Any] | None = None) -> Any:
    try:
        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            params=params,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.ConnectionError:
        st.error("FastAPI ist nicht erreichbar. Starte zuerst den API-Server.")
    except requests.Timeout:
        st.error("Die API-Anfrage hat zu lange gedauert.")
    except requests.HTTPError:
        st.error(f"API-Fehler: {response.text}")
    except requests.RequestException as error:
        st.error(f"Verbindungsfehler: {error}")
    return None


def api_post(endpoint: str, payload: dict[str, Any]) -> Any:
    try:
        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        return response.json()
    except requests.ConnectionError:
        st.error("FastAPI ist nicht erreichbar. Starte zuerst den API-Server.")
    except requests.Timeout:
        st.error("Die API-Anfrage hat zu lange gedauert.")
    except requests.HTTPError:
        st.error(f"API-Fehler: {response.text}")
    except requests.RequestException as error:
        st.error(f"Verbindungsfehler: {error}")
    return None


@st.cache_data(ttl=60)
def load_machines() -> list[dict[str, Any]]:
    result = api_get("/machines")
    return result if isinstance(result, list) else []


def show_dashboard() -> None:
    st.header("Dashboard")

    machines = load_machines()
    error_rates = api_get("/kpi/error-rate")
    #availability = api_get("/kpi/availability")
    #mttr_mtbf = api_get("/kpi/mttr-mtbf")

    col1, col2, col3 = st.columns(3)
    col1.metric("Maschinen", len(machines))

    total_errors = 0
    total_downtime = 0.0
    if isinstance(error_rates, list):
        total_errors = sum(item.get("error_count", 0) for item in error_rates)
        total_downtime = sum(
            item.get("total_downtime_minutes", 0) or 0
            for item in error_rates
        )

    col2.metric("Fehler", total_errors)
    col3.metric("Stillstand", f"{total_downtime:,.0f} Min.")


    if isinstance(error_rates, list) and error_rates:
        st.subheader("Fehler pro Maschine")

        error_df = pd.DataFrame(error_rates)

        if {"machine_name", "error_count"}.issubset(error_df.columns):

            error_df = error_df.sort_values("error_count", ascending=True)

            chart = (
                alt.Chart(error_df)
                .mark_bar()
                .encode(
                    x=alt.X("error_count:Q", title="Error Count"),
                    y=alt.Y(
                        "machine_name:N",
                        sort=None,
                        title="Machine",
                    ),
                    tooltip=["machine_name", "error_count"],
                )
                .properties(height=500)
            )

            text = (
                alt.Chart(error_df)
                .mark_text(
                    align="left",
                    baseline="middle",
                    dx=5,
                )
                .encode(
                    x="error_count:Q",
                    y=alt.Y("machine_name:N", sort=None),
                    text="error_count:Q",
                )
            )

            st.altair_chart(chart + text, use_container_width=True)

        st.dataframe(error_df, use_container_width=True)


def show_machines() -> None:
    st.header("Maschinen")
    machines = load_machines()

    if not machines:
        st.info("Keine Maschinen gefunden.")
        return

    machines_df = pd.DataFrame(machines)
    st.dataframe(machines_df, use_container_width=True)

    machine_options = {
        f'{machine["name"]} (ID {machine["id"]})': machine["id"]
        for machine in machines
    }

    selected_label = st.selectbox(
        "Maschine für Event-Historie auswählen",
        options=list(machine_options),
    )

    col1, col2 = st.columns(2)
    start_date = col1.date_input("Startdatum", value=None)
    end_date = col2.date_input("Enddatum", value=None)

    if st.button("Events laden", type="primary"):
        params: dict[str, Any] = {}
        if start_date:
            params["start"] = f"{start_date.isoformat()}T00:00:00"
        if end_date:
            params["end"] = f"{end_date.isoformat()}T23:59:59"

        machine_id = machine_options[selected_label]
        events = api_get(f"/machines/{machine_id}/events", params=params)

        if isinstance(events, list) and events:
            st.dataframe(pd.DataFrame(events), use_container_width=True)
        elif events is not None:
            st.info("Für die Auswahl wurden keine Events gefunden.")


def show_kpis() -> None:
    st.header("Production Reporting")
    tab1, tab2, tab3 = st.tabs(
        ["Fehler und Stillstand", "Verfügbarkeit", "MTTR / MTBF"]
    )

    with tab1:
        data = api_get("/kpi/error-rate")
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            if {"machine_name", "error_count"}.issubset(df.columns):
                st.bar_chart(
                    df[["machine_name", "error_count"]].set_index("machine_name")
                )

    with tab2:
        data = api_get("/kpi/availability")
        if isinstance(data, list) and data:
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True)
            availability_column = next(
                (
                    column
                    for column in ["availability_percent", "availability"]
                    if column in df.columns
                ),
                None,
            )
            if availability_column and "machine_name" in df.columns:
                st.bar_chart(
                    df[["machine_name", availability_column]].set_index("machine_name")
                )

    with tab3:
        data = api_get("/kpi/mttr-mtbf")
        if isinstance(data, list) and data:
            st.dataframe(pd.DataFrame(data), use_container_width=True)


def show_tickets() -> None:
    st.header("Tickets")
    machines = load_machines()

    filter_options = {"Alle Maschinen": None}
    filter_options.update({machine["name"]: machine["id"] for machine in machines})

    selected_machine = st.selectbox("Maschine filtern", options=list(filter_options))
    limit = st.slider(
        "Maximale Anzahl Tickets",
        min_value=10,
        max_value=500,
        value=50,
        step=10,
    )

    params: dict[str, Any] = {"limit": limit}
    machine_id = filter_options[selected_machine]
    if machine_id is not None:
        params["machine_id"] = machine_id

    tickets = api_get("/tickets", params=params)
    if isinstance(tickets, list) and tickets:
        st.dataframe(pd.DataFrame(tickets), use_container_width=True)
    else:
        st.info("Keine Tickets gefunden.")


def show_measures() -> None:
    st.header("Wartungsmaßnahmen")
    machines = load_machines()

    if not machines:
        st.info("Keine Maschinen verfügbar.")
        return

    machine_options = {machine["name"]: machine["id"] for machine in machines}

    with st.form("measure_form"):
        selected_machine = st.selectbox("Maschine", options=list(machine_options))
        description = st.text_area(
            "Beschreibung der Maßnahme",
            placeholder="Zum Beispiel: Sensorik gereinigt und neu kalibriert",
        )
        start_date = st.date_input("Startdatum")
        submitted = st.form_submit_button("Maßnahme speichern", type="primary")

    if submitted:
        if not description.strip():
            st.warning("Bitte gib eine Beschreibung ein.")
        else:
            payload = {
                "machine_id": machine_options[selected_machine],
                "description": description.strip(),
                "start_date": f"{start_date.isoformat()}T00:00:00",
            }
            result = api_post("/measures", payload)
            if result is not None:
                st.success("Die Maßnahme wurde gespeichert.")
                st.json(result)

    st.subheader("Vorhandene Maßnahmen")
    measures = api_get("/measures")
    if isinstance(measures, list) and measures:
        st.dataframe(pd.DataFrame(measures), use_container_width=True)
    else:
        st.info("Keine Maßnahmen gefunden.")


def show_clusters() -> None:
    st.header("Ticket-Clustering")
    n_clusters = st.slider("Anzahl Cluster", 2, 10, 5)

    if st.button("Cluster berechnen", type="primary"):
        clusters = api_get(
            "/tickets/clusters",
            params={"n_clusters": n_clusters},
        )
        if isinstance(clusters, list) and clusters:
            st.dataframe(pd.DataFrame(clusters), use_container_width=True)


st.title("🏭 Production Hall Reporting")

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Maschinen",
        "Production Reporting",
        "Tickets",
        "Maßnahmen",
        "Ticket-Clustering",
    ],
)

if st.sidebar.button("Daten aktualisieren"):
    st.cache_data.clear()
    st.rerun()

if page == "Dashboard":
    show_dashboard()
elif page == "Maschinen":
    show_machines()
elif page == "Production Reporting":
    show_kpis()
elif page == "Tickets":
    show_tickets()
elif page == "Maßnahmen":
    show_measures()
elif page == "Ticket-Clustering":
    show_clusters()
