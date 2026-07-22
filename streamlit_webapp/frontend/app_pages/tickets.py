"""Tickets: filterbare \u00dcbersicht aller Incidents & Service Requests mit Detailansicht."""

from __future__ import annotations

import pandas
import streamlit

from components import api_client, status
from components.formatting import format_datetime, format_hours

streamlit.title(":material/confirmation_number: Tickets")
streamlit.caption("Incidents und Service Requests durchsuchen, filtern und im Detail ansehen.")

machines = api_client.load_machines()
machine_options = {machine["name"]: machine["id"] for machine in machines}

filter_row = streamlit.container(horizontal=True, vertical_alignment="center")
with filter_row:
    ticket_type_choice = streamlit.segmented_control(
        "Typ",
        options=["Alle", "Incident", "Service Request"],
        default="Alle",
        key="tickets_type_filter",
    )
    with streamlit.popover("Weitere Filter", icon=":material/filter_list:"):
        priority_choice = streamlit.selectbox(
            "Priorit\u00e4t",
            options=["Alle"] + [status.PRIORITY_LABELS[p] for p in status.PRIORITY_ORDER],
            key="tickets_priority_filter",
        )
        status_choice = streamlit.selectbox(
            "Status", options=["Alle"] + status.STATUS_ORDER, key="tickets_status_filter"
        )
        machine_choice = streamlit.selectbox(
            "Maschine", options=["Alle"] + sorted(machine_options), key="tickets_machine_filter"
        )
        limit = streamlit.slider("Max. Anzahl geladener Tickets", 20, 500, 150, step=10, key="tickets_limit_filter")

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
    streamlit.info("F\u00fcr die gew\u00e4hlten Filter wurden keine Tickets gefunden.", icon=":material/search_off:")
else:
    tickets_df = pandas.DataFrame(tickets)
    tickets_df["priority_label"] = tickets_df["priority"].map(status.PRIORITY_LABELS).fillna(tickets_df["priority"])
    tickets_df["technician"] = tickets_df["technician"].fillna("\u2013")

    open_count = int((tickets_df["status"] != "Geschlossen").sum())
    critical_count = int((tickets_df["priority"] == "critical").sum())

    with streamlit.container(horizontal=True):
        streamlit.metric("Angezeigt", f"{len(tickets_df)} / {total_tickets}", border=True)
        streamlit.metric("Davon offen", open_count, border=True)
        streamlit.metric("Davon kritisch", critical_count, border=True)

    streamlit.space("small")

    display_columns = [
        "id", "ticket_type", "machine_name", "priority_label", "status",
        "description", "technician", "created_at", "resolution_hours",
    ]
    event = streamlit.dataframe(
        tickets_df[display_columns],
        column_config={
            "id": streamlit.column_config.NumberColumn("ID", width="small"),
            "ticket_type": streamlit.column_config.TextColumn("Typ"),
            "machine_name": streamlit.column_config.TextColumn("Maschine"),
            "priority_label": streamlit.column_config.TextColumn("Priorit\u00e4t"),
            "status": streamlit.column_config.TextColumn("Status"),
            "description": streamlit.column_config.TextColumn("Beschreibung", width="large"),
            "technician": streamlit.column_config.TextColumn("Techniker"),
            "created_at": streamlit.column_config.DatetimeColumn("Erstellt", format="DD.MM.YYYY HH:mm"),
            "resolution_hours": streamlit.column_config.NumberColumn("L\u00f6sungszeit (Std.)", format="%.1f"),
        },
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="tickets_table",
    )

    streamlit.caption("Zeile anklicken f\u00fcr Details.")

    if event.selection.rows:
        selected = tickets_df.iloc[event.selection.rows[0]]
        with streamlit.container(border=True):
            header = streamlit.container(horizontal=True, vertical_alignment="center")
            with header:
                streamlit.markdown(f"#### Ticket #{int(selected['id'])}")
                status.ticket_type_badge(selected["ticket_type"])
                status.priority_badge(selected["priority"])
                status.status_badge(selected["status"])

            streamlit.write(selected["description"])

            detail_cols = streamlit.columns(3)
            detail_cols[0].metric("Maschine", selected["machine_name"])
            detail_cols[1].metric("Techniker", selected["technician"])
            detail_cols[2].metric("L\u00f6sungszeit", format_hours(selected["resolution_hours"]))

            if selected["error_code"]:
                streamlit.caption(f"Fehlercode **{selected['error_code']}** \u2013 {selected['error_description']}")

            timeline_cols = streamlit.columns(4)
            timeline_cols[0].markdown(f"**Erstellt**\n\n{format_datetime(selected['created_at'])}")
            timeline_cols[1].markdown(f"**Zugewiesen**\n\n{format_datetime(selected['assigned_at'])}")
            timeline_cols[2].markdown(f"**Gel\u00f6st**\n\n{format_datetime(selected['resolved_at'])}")
            timeline_cols[3].markdown(f"**Geschlossen**\n\n{format_datetime(selected['closed_at'])}")
