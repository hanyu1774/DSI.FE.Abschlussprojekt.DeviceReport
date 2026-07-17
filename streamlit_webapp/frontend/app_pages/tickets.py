"""Tickets: filterbare \u00dcbersicht aller Incidents & Service Requests mit Detailansicht."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import api_client, status
from components.formatting import format_datetime, format_hours

st.title(":material/confirmation_number: Tickets")
st.caption("Incidents und Service Requests durchsuchen, filtern und im Detail ansehen.")

machines = api_client.load_machines()
machine_options = {machine["name"]: machine["id"] for machine in machines}

filter_row = st.container(horizontal=True, vertical_alignment="center")
with filter_row:
    ticket_type_choice = st.segmented_control(
        "Typ",
        options=["Alle", "Incident", "Service Request"],
        default="Alle",
        key="tickets_type_filter",
    )
    with st.popover("Weitere Filter", icon=":material/filter_list:"):
        priority_choice = st.selectbox(
            "Priorit\u00e4t",
            options=["Alle"] + [status.PRIORITY_LABELS[p] for p in status.PRIORITY_ORDER],
            key="tickets_priority_filter",
        )
        status_choice = st.selectbox(
            "Status", options=["Alle"] + status.STATUS_ORDER, key="tickets_status_filter"
        )
        machine_choice = st.selectbox(
            "Maschine", options=["Alle"] + sorted(machine_options), key="tickets_machine_filter"
        )
        limit = st.slider("Max. Anzahl geladener Tickets", 20, 500, 150, step=10, key="tickets_limit_filter")

priority_reverse = {label: key for key, label in status.PRIORITY_LABELS.items()}

tickets = api_client.load_tickets(
    limit=limit,
    machine_id=machine_options.get(machine_choice) if machine_choice != "Alle" else None,
    ticket_type=None if ticket_type_choice in (None, "Alle") else ticket_type_choice,
    priority=priority_reverse.get(priority_choice) if priority_choice != "Alle" else None,
    status=None if status_choice == "Alle" else status_choice,
)

summary = api_client.load_ticket_summary()
total_tickets = summary.get("total", 0)

if not tickets:
    st.info("F\u00fcr die gew\u00e4hlten Filter wurden keine Tickets gefunden.", icon=":material/search_off:")
else:
    tickets_df = pd.DataFrame(tickets)
    tickets_df["priority_label"] = tickets_df["priority"].map(status.PRIORITY_LABELS).fillna(tickets_df["priority"])
    tickets_df["technician"] = tickets_df["technician"].fillna("\u2013")

    open_count = int((tickets_df["status"] != "Geschlossen").sum())
    critical_count = int((tickets_df["priority"] == "critical").sum())

    with st.container(horizontal=True):
        st.metric("Angezeigt", f"{len(tickets_df)} / {total_tickets}", border=True)
        st.metric("Davon offen", open_count, border=True)
        st.metric("Davon kritisch", critical_count, border=True)

    st.space("small")

    display_columns = [
        "id", "ticket_type", "machine_name", "priority_label", "status",
        "description", "technician", "created_at", "resolution_hours",
    ]
    event = st.dataframe(
        tickets_df[display_columns],
        column_config={
            "id": st.column_config.NumberColumn("ID", width="small"),
            "ticket_type": st.column_config.TextColumn("Typ"),
            "machine_name": st.column_config.TextColumn("Maschine"),
            "priority_label": st.column_config.TextColumn("Priorit\u00e4t"),
            "status": st.column_config.TextColumn("Status"),
            "description": st.column_config.TextColumn("Beschreibung", width="large"),
            "technician": st.column_config.TextColumn("Techniker"),
            "created_at": st.column_config.DatetimeColumn("Erstellt", format="DD.MM.YYYY HH:mm"),
            "resolution_hours": st.column_config.NumberColumn("L\u00f6sungszeit (Std.)", format="%.1f"),
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="tickets_table",
    )

    st.caption("Zeile anklicken f\u00fcr Details.")

    if event.selection.rows:
        selected = tickets_df.iloc[event.selection.rows[0]]
        with st.container(border=True):
            header = st.container(horizontal=True, vertical_alignment="center")
            with header:
                st.markdown(f"#### Ticket #{int(selected['id'])}")
                status.ticket_type_badge(selected["ticket_type"])
                status.priority_badge(selected["priority"])
                status.status_badge(selected["status"])

            st.write(selected["description"])

            detail_cols = st.columns(3)
            detail_cols[0].metric("Maschine", selected["machine_name"])
            detail_cols[1].metric("Techniker", selected["technician"])
            detail_cols[2].metric("L\u00f6sungszeit", format_hours(selected["resolution_hours"]))

            if selected["error_code"]:
                st.caption(f"Fehlercode **{selected['error_code']}** \u2013 {selected['error_description']}")

            timeline_cols = st.columns(4)
            timeline_cols[0].markdown(f"**Erstellt**\n\n{format_datetime(selected['created_at'])}")
            timeline_cols[1].markdown(f"**Zugewiesen**\n\n{format_datetime(selected['assigned_at'])}")
            timeline_cols[2].markdown(f"**Gel\u00f6st**\n\n{format_datetime(selected['resolved_at'])}")
            timeline_cols[3].markdown(f"**Geschlossen**\n\n{format_datetime(selected['closed_at'])}")
