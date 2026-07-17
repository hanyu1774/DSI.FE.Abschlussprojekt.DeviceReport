"""Maschinen: Stammdaten und Event-Historie (Fehler, Wartung, Offline-Zeiten)."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import api_client

st.title(":material/precision_manufacturing: Maschinen")
st.caption("Stammdaten aller Maschinen sowie Event-Historie je Maschine.")

machines = api_client.load_machines()

if not machines:
    st.info("Keine Maschinen gefunden.", icon=":material/search_off:")
else:
    machines_df = pd.DataFrame(machines)
    st.dataframe(
        machines_df,
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "name": st.column_config.TextColumn("Name"),
            "machine_type": st.column_config.TextColumn("Typ"),
            "hall": st.column_config.TextColumn("Halle"),
            "manufacturer": st.column_config.TextColumn("Hersteller"),
            "year_built": st.column_config.NumberColumn("Baujahr", format="%d"),
        },
        hide_index=True,
    )

    st.space("small")
    st.subheader("Event-Historie")
    st.caption("Fehler-, Wartungs- und Offline-Ereignisse einer einzelnen Maschine, optional in einem Zeitraum.")

    machine_options = {f"{machine['name']} \u2014 {machine['hall']}": machine["id"] for machine in machines}

    with st.container(horizontal=True, vertical_alignment="bottom"):
        selected_label = st.selectbox("Maschine", options=sorted(machine_options), key="machine_events_select")
        start_date = st.date_input("Startdatum", value=None, key="machine_events_start")
        end_date = st.date_input("Enddatum", value=None, key="machine_events_end")
        load_clicked = st.button(
            "Events laden", icon=":material/search:", type="primary", key="machine_events_load"
        )

    if load_clicked:
        machine_id = machine_options[selected_label]
        start = f"{start_date.isoformat()} 00:00:00" if start_date else None
        end = f"{end_date.isoformat()} 23:59:59" if end_date else None

        with st.spinner("Lade Events\u2026"):
            events = api_client.load_machine_events(machine_id, start=start, end=end)

        if not events:
            st.info("F\u00fcr die Auswahl wurden keine Events gefunden.", icon=":material/search_off:")
        else:
            events_df = pd.DataFrame(events)
            status_counts = events_df["status"].value_counts()

            with st.container(horizontal=True):
                st.metric("Events gesamt", len(events_df), border=True)
                st.metric("Fehler", int(status_counts.get("error", 0)), border=True)
                st.metric("Wartung", int(status_counts.get("maintenance", 0)), border=True)
                st.metric("Offline", int(status_counts.get("offline", 0)), border=True)

            st.dataframe(
                events_df,
                column_config={
                    "id": st.column_config.NumberColumn("ID", width="small"),
                    "timestamp": st.column_config.DatetimeColumn("Zeitpunkt", format="DD.MM.YYYY HH:mm"),
                    "status": st.column_config.TextColumn("Status"),
                    "error_code": st.column_config.TextColumn("Fehlercode"),
                    "error_description": st.column_config.TextColumn("Beschreibung"),
                    "downtime_minutes": st.column_config.NumberColumn("Stillstand (Min.)", format="%.1f"),
                },
                hide_index=True,
            )
