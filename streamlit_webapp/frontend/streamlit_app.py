"""
Production Hall Reporting - Streamlit-Frontend (Einstiegspunkt).

Datenfluss: Streamlit (dieses Frontend) -> FastAPI -> SQLite.

Start (aus dem Ordner `frontend/`, bei laufendem Backend):
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Production Hall Reporting",
    page_icon=":material/factory:",
    layout="wide",
)

with st.sidebar:
    st.markdown("## :material/factory: Production Hall")
    st.caption("Reporting f\u00fcr Maschinen, Incidents & Service Requests")

page = st.navigation(
    [
        st.Page("app_pages/dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
        st.Page("app_pages/tickets.py", title="Tickets", icon=":material/confirmation_number:"),
        st.Page("app_pages/machines.py", title="Maschinen", icon=":material/precision_manufacturing:"),
        st.Page("app_pages/kpis.py", title="Production Reporting", icon=":material/monitoring:"),
        st.Page("app_pages/measures.py", title="Ma\u00dfnahmen", icon=":material/handyman:"),
        st.Page("app_pages/clustering.py", title="Ticket-Clustering", icon=":material/hub:"),
    ],
    position="sidebar",
)

with st.sidebar:
    st.space("small")
    if st.button("Daten aktualisieren", icon=":material/refresh:", width="stretch"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Production Hall Reporting v2.0 \u00b7 FastAPI + Streamlit")

page.run()
