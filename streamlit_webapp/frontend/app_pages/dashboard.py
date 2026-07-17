"""Dashboard: Schnell\u00fcbersicht \u00fcber Maschinen, Incidents und Service Requests."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import api_client, charts, status
from components.formatting import format_hours

st.title(":material/dashboard: Dashboard")
st.caption("Schnell\u00fcbersicht \u00fcber Maschinenstatus, Incidents und Service Requests.")


@st.fragment(parallel=True)
def kpi_overview() -> None:
    with st.container(horizontal=True):
        with st.container(border=True):
            with st.skeleton(height=88):
                machines = api_client.load_machines()
                st.metric("Maschinen", len(machines))

        with st.container(border=True):
            with st.skeleton(height=88):
                summary = api_client.load_ticket_summary()
                st.metric("Offene Tickets", summary.get("open_count", 0))

        with st.container(border=True):
            with st.skeleton(height=88):
                summary = api_client.load_ticket_summary()
                st.metric("Kritische Tickets", summary.get("critical_count", 0))

        with st.container(border=True):
            with st.skeleton(height=88):
                response_times = api_client.load_response_times()
                overall = response_times.get("overall", {})
                st.metric(
                    "\u00d8 L\u00f6sungszeit",
                    format_hours(overall.get("avg_time_to_resolve_hours")),
                    help="Durchschnittliche Zeit von Ticket-Erstellung bis L\u00f6sung, \u00fcber Incidents und Service Requests hinweg.",
                )


@st.fragment(parallel=True)
def ticket_breakdown_charts() -> None:
    with st.skeleton(height=420):
        summary = api_client.load_ticket_summary()
        if not summary:
            st.info("Keine Ticket-Daten verf\u00fcgbar.")
            return

        type_df = pd.DataFrame(summary["by_type"])
        priority_df = pd.DataFrame(summary["by_priority"])
        status_df = pd.DataFrame(summary["by_status"])
        category_df = pd.DataFrame(summary["by_category"])

        row1 = st.columns(2)
        with row1[0]:
            with st.container(border=True):
                st.markdown("**Tickets nach Typ**")
                st.altair_chart(
                    charts.donut_chart(
                        type_df,
                        "name",
                        "count",
                        color_domain=list(status.TICKET_TYPE_HEX.keys()),
                        color_range=list(status.TICKET_TYPE_HEX.values()),
                    )
                )
        with row1[1]:
            with st.container(border=True):
                st.markdown("**Tickets nach Priorit\u00e4t**")
                priority_df["label"] = priority_df["name"].map(status.PRIORITY_LABELS).fillna(priority_df["name"])
                priority_label_order = [status.PRIORITY_LABELS[p] for p in status.PRIORITY_ORDER]
                st.altair_chart(
                    charts.ranked_bar_chart(
                        priority_df,
                        "label",
                        "count",
                        color_domain=priority_label_order,
                        color_range=[status.PRIORITY_HEX[p] for p in status.PRIORITY_ORDER],
                        value_title="Anzahl Tickets",
                        min_height=180,
                        category_order=priority_label_order,
                    )
                )

        row2 = st.columns(2)
        with row2[0]:
            with st.container(border=True):
                st.markdown("**Tickets nach Status**")
                st.altair_chart(
                    charts.donut_chart(
                        status_df,
                        "name",
                        "count",
                        color_domain=status.STATUS_ORDER,
                        color_range=[status.STATUS_HEX[s] for s in status.STATUS_ORDER],
                    )
                )
        with row2[1]:
            with st.container(border=True):
                st.markdown("**Tickets nach Fehlerkategorie**")
                st.altair_chart(
                    charts.ranked_bar_chart(
                        category_df,
                        "name",
                        "count",
                        single_color="#0E6E7C",
                        value_title="Anzahl Tickets",
                        min_height=180,
                    )
                )


@st.fragment(parallel=True)
def ticket_trend_section() -> None:
    with st.container(border=True):
        header_cols = st.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
        with header_cols:
            st.markdown("**Tickets im Zeitverlauf**")
            interval_label = st.segmented_control(
                "Intervall",
                options=["Tag", "Woche", "Monat"],
                default="Woche",
                key="dashboard_trend_interval",
                label_visibility="collapsed",
            )
        interval_map = {"Tag": "day", "Woche": "week", "Monat": "month"}
        interval = interval_map.get(interval_label or "Woche", "week")

        with st.skeleton(height=280):
            trend = api_client.load_ticket_trend(interval=interval)
            if not trend:
                st.info("Keine Verlaufsdaten verf\u00fcgbar.")
                return
            trend_df = pd.DataFrame(trend)
            st.altair_chart(
                charts.trend_area_chart(
                    trend_df,
                    "period",
                    ["incident_count", "service_request_count"],
                    labels={"incident_count": "Incident", "service_request_count": "Service Request"},
                    colors=status.TICKET_TYPE_HEX,
                )
            )


@st.fragment(parallel=True)
def top_machines_section() -> None:
    with st.container(border=True):
        st.markdown("**Maschinen mit den meisten Fehlern** (Top 5)")
        st.caption("Vollst\u00e4ndige Aufschl\u00fcsselung inkl. Verf\u00fcgbarkeit und MTTR/MTBF unter *Production Reporting*.")
        with st.skeleton(height=200):
            error_rate = api_client.load_error_rate()
            if not error_rate:
                st.info("Keine KPI-Daten verf\u00fcgbar.")
                return
            top5 = pd.DataFrame(error_rate).sort_values("error_count", ascending=False).head(5)
            st.altair_chart(
                charts.ranked_bar_chart(
                    top5,
                    "machine_name",
                    "error_count",
                    single_color="#C96A1F",
                    value_title="Fehleranzahl",
                    min_height=180,
                    bar_height=32,
                )
            )


kpi_overview()
st.space("small")
ticket_breakdown_charts()
st.space("small")
ticket_trend_section()
st.space("small")
top_machines_section()
