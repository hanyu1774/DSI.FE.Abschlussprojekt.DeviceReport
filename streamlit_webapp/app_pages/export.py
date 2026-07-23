"""PDF-Export: Analysebericht mit frei w\u00e4hlbaren Abschnitten als PDF herunterladen."""

from __future__ import annotations

from datetime import datetime

import streamlit

from components import pdf_export

streamlit.title(":material/picture_as_pdf: PDF-Export")
streamlit.caption("Analysebericht zusammenstellen und als PDF herunterladen. Du entscheidest, was rein soll.")

SECTION_OPTIONS = {key: label for key, (label, _builder) in pdf_export.SECTION_BUILDERS.items()}
DEFAULT_SELECTION = ["kpi_overview", "ticket_breakdown", "ticket_trend", "top_machines", "production_kpis"]

with streamlit.container(border=True):
    streamlit.markdown("**Abschnitte ausw\u00e4hlen**")
    selected_labels = streamlit.multiselect(
        "Was soll im Bericht enthalten sein?",
        options=list(SECTION_OPTIONS.values()),
        default=[SECTION_OPTIONS[k] for k in DEFAULT_SELECTION],
        label_visibility="collapsed",
    )
    label_to_key = {label: key for key, label in SECTION_OPTIONS.items()}
    selected_keys = [label_to_key[label] for label in selected_labels]
    # Reihenfolge im PDF folgt der festen, sinnvollen Abfolge aus SECTION_BUILDERS,
    # nicht der Klick-Reihenfolge im Multiselect.
    selected_keys = [key for key in pdf_export.SECTION_BUILDERS if key in selected_keys]

options: dict = {}

if "ticket_trend" in selected_keys:
    with streamlit.container(border=True):
        streamlit.markdown("**Ticket-Verlauf**")
        interval_label = streamlit.segmented_control(
            "Intervall", options=["Tag", "Woche", "Monat"], default="Woche", key="export_trend_interval",
        )
        options["trend_interval"] = {"Tag": "day", "Woche": "week", "Monat": "month"}.get(interval_label or "Woche", "week")

if "top_machines" in selected_keys:
    with streamlit.container(border=True):
        streamlit.markdown("**Top-Maschinen nach Fehlern**")
        options["top_machines_n"] = streamlit.slider("Anzahl Maschinen", 3, 15, 5, key="export_top_n")

if "ticket_list" in selected_keys:
    with streamlit.container(border=True):
        streamlit.markdown("**Ticket-Liste**")
        options["ticket_list_limit"] = streamlit.slider("Max. Anzahl Tickets (neueste zuerst)", 10, 300, 50, step=10, key="export_ticket_limit")

if "ticket_clusters" in selected_keys:
    with streamlit.container(border=True):
        streamlit.markdown("**Ticket-Clustering**")
        options["n_clusters"] = streamlit.slider("Anzahl Cluster", 2, 12, 6, key="export_n_clusters")

streamlit.space("small")

if not selected_keys:
    streamlit.info("Bitte mindestens einen Abschnitt ausw\u00e4hlen.", icon=":material/info:")
else:
    generate_clicked = streamlit.button(
        "PDF erstellen", icon=":material/picture_as_pdf:", type="primary", key="export_generate"
    )

    if generate_clicked:
        with streamlit.spinner("Erstelle Bericht\u2026"):
            try:
                pdf_bytes = pdf_export.generate_pdf(selected_keys, options)
            except Exception as error:
                streamlit.error(f"Der Bericht konnte nicht erstellt werden: {error}", icon=":material/error:")
            else:
                streamlit.session_state["export_pdf_bytes"] = pdf_bytes
                streamlit.toast("Bericht erstellt.", icon=":material/check_circle:")

    if "export_pdf_bytes" in streamlit.session_state:
        filename = f"analysebericht_{datetime.now().strftime('%Y-%m-%d_%H%M')}.pdf"
        streamlit.download_button(
            "PDF herunterladen",
            data=streamlit.session_state["export_pdf_bytes"],
            file_name=filename,
            mime="application/pdf",
            icon=":material/download:",
            type="primary",
        )
