"""
Production Hall Reporting - Streamlit-Frontend (Einstiegspunkt).

Datenfluss: Streamlit (dieses Frontend) -> FastAPI -> SQLite.

Start (aus dem Ordner `frontend/`, bei laufendem Backend):
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import streamlit

streamlit.set_page_config(
    page_title="Production Hall Reporting",
    page_icon=":material/factory:",
    layout="wide",
)

with streamlit.sidebar:
    streamlit.markdown("## :material/factory: Production Hall")
    streamlit.caption("Reporting f\u00fcr Maschinen, Incidents & Service Requests")

page = streamlit.navigation(
    [
        streamlit.Page("app_pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
        streamlit.Page("app_pages/tickets.py", title="Tickets", icon=":material/confirmation_number:"),
        streamlit.Page("app_pages/machines.py", title="Maschinen", icon=":material/precision_manufacturing:"),
        streamlit.Page("app_pages/kpis.py", title="Production Reporting", icon=":material/monitoring:"),
        streamlit.Page("app_pages/measures.py", title="Ma\u00dfnahmen", icon=":material/handyman:"),
        streamlit.Page("app_pages/clustering.py", title="Ticket-Clustering", icon=":material/hub:"),
    ],
    position="sidebar",
)

with streamlit.sidebar:
    streamlit.space("small")
    if streamlit.button("Daten aktualisieren", icon=":material/refresh:", width="stretch"):
        streamlit.cache_data.clear()
        streamlit.rerun()
    streamlit.caption("Production Hall Reporting v2.0 \u00b7 FastAPI + Streamlit")

page.run()
