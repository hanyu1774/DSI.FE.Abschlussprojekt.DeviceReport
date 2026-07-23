"""Maschinen: Stammdaten und Event-Historie (Fehler, Wartung, Offline-Zeiten)."""

from __future__ import annotations

import pandas
import streamlit

from components import api_client

streamlit.title(":material/precision_manufacturing: Maschinen")
streamlit.caption("Stammdaten aller Maschinen sowie Event-Historie je Maschine.")

machines = api_client.load_machines()

if not machines:
    streamlit.info("Keine Maschinen gefunden.", icon=":material/search_off:")
else:
    machines_df = pandas.DataFrame(machines)
    streamlit.dataframe(
        machines_df,
        column_config={
            "id": streamlit.column_config.NumberColumn("ID", width="small"),
            "name": streamlit.column_config.TextColumn("Name"),
            "machine_type": streamlit.column_config.TextColumn("Typ"),
            "hall": streamlit.column_config.TextColumn("Halle"),
            "manufacturer": streamlit.column_config.TextColumn("Hersteller"),
            "year_built": streamlit.column_config.NumberColumn("Baujahr", format="%d"),
        },
        hide_index=True,
    )

    streamlit.space("small")
    streamlit.subheader("Event-Historie")
    streamlit.caption("Fehler-, Wartungs- und Offline-Ereignisse einer einzelnen Maschine, optional in einem Zeitraum.")

    machine_options = {f"{machine['name']} \u2014 {machine['hall']}": machine["id"] for machine in machines}

    with streamlit.container(horizontal=True, vertical_alignment="bottom"):
        selected_label = streamlit.selectbox("Maschine", options=sorted(machine_options), key="machine_events_select")
        start_date = streamlit.date_input("Startdatum", value=None, key="machine_events_start")
        end_date = streamlit.date_input("Enddatum", value=None, key="machine_events_end")
        load_clicked = streamlit.button(
            "Events laden", icon=":material/search:", type="primary", key="machine_events_load"
        )

    if load_clicked:
        machine_id = machine_options[selected_label]
        start = f"{start_date.isoformat()} 00:00:00" if start_date else None
        end = f"{end_date.isoformat()} 23:59:59" if end_date else None

        with streamlit.spinner("Lade Events\u2026"):
            events = api_client.load_machine_events(machine_id, start=start, end=end)

        if not events:
            streamlit.info("F\u00fcr die Auswahl wurden keine Events gefunden.", icon=":material/search_off:")
        else:
            events_df = pandas.DataFrame(events)
            status_counts = events_df["status"].value_counts()

            with streamlit.container(horizontal=True):
                streamlit.metric("Events gesamt", len(events_df), border=True)
                streamlit.metric("Fehler", int(status_counts.get("error", 0)), border=True)
                streamlit.metric("Wartung", int(status_counts.get("maintenance", 0)), border=True)
                streamlit.metric("Offline", int(status_counts.get("offline", 0)), border=True)

            streamlit.dataframe(
                events_df,
                column_config={
                    "id": streamlit.column_config.NumberColumn("ID", width="small"),
                    "timestamp": streamlit.column_config.DatetimeColumn("Zeitpunkt", format="DD.MM.YYYY HH:mm"),
                    "status": streamlit.column_config.TextColumn("Status"),
                    "error_code": streamlit.column_config.TextColumn("Fehlercode"),
                    "error_description": streamlit.column_config.TextColumn("Beschreibung"),
                    "downtime_minutes": streamlit.column_config.NumberColumn("Stillstand (Min.)", format="%.1f"),
                },
                hide_index=True,
            )
