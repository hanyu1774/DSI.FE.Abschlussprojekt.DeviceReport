"""Dashboard: Schnell\u00fcbersicht \u00fcber Maschinen, Incidents und Service Requests."""

from __future__ import annotations

import pandas
import streamlit

from components import api_client, charts, status
from components.formatting import format_hours

streamlit.title(":material/dashboard: Dashboard")
streamlit.caption("Schnell\u00fcbersicht \u00fcber Maschinenstatus, Incidents und Service Requests.")


@streamlit.fragment(parallel=True)
def kpi_overview() -> None:
    with streamlit.container(horizontal=True):
        with streamlit.container(border=True):
            with streamlit.skeleton(height=88):
                machines = api_client.load_machines()
                streamlit.metric("Maschinen", len(machines))

        with streamlit.container(border=True):
            with streamlit.skeleton(height=88):
                summary = api_client.load_ticket_summary()
                streamlit.metric("Offene Tickets", summary.get("open_count", 0))

        with streamlit.container(border=True):
            with streamlit.skeleton(height=88):
                summary = api_client.load_ticket_summary()
                streamlit.metric("Kritische Tickets", summary.get("critical_count", 0))

        with streamlit.container(border=True):
            with streamlit.skeleton(height=88):
                response_times = api_client.load_response_times()
                overall = response_times.get("overall", {})
                streamlit.metric(
                    "\u00d8 L\u00f6sungszeit",
                    format_hours(overall.get("avg_time_to_resolve_hours")),
                    help="Durchschnittliche Zeit von Ticket-Erstellung bis L\u00f6sung, \u00fcber Incidents und Service Requests hinweg.",
                )


@streamlit.fragment(parallel=True)
def ticket_breakdown_charts() -> None:
    with streamlit.skeleton(height=420):
        summary = api_client.load_ticket_summary()
        if not summary:
            streamlit.info("Keine Ticket-Daten verf\u00fcgbar.")
            return

        type_df = pandas.DataFrame(summary["by_type"])
        priority_df = pandas.DataFrame(summary["by_priority"])
        status_df = pandas.DataFrame(summary["by_status"])
        category_df = pandas.DataFrame(summary["by_category"])

        row1 = streamlit.columns(2)
        with row1[0]:
            with streamlit.container(border=True):
                streamlit.markdown("**Tickets nach Typ**")
                streamlit.altair_chart(
                    charts.donut_chart(
                        type_df,
                        "name",
                        "count",
                        color_domain=list(status.TICKET_TYPE_HEX.keys()),
                        color_range=list(status.TICKET_TYPE_HEX.values()),
                    )
                )
        with row1[1]:
            with streamlit.container(border=True):
                streamlit.markdown("**Tickets nach Priorit\u00e4t**")
                priority_df["label"] = priority_df["name"].map(status.PRIORITY_LABELS).fillna(priority_df["name"])
                priority_label_order = [status.PRIORITY_LABELS[p] for p in status.PRIORITY_ORDER]
                streamlit.altair_chart(
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

        row2 = streamlit.columns(2)
        with row2[0]:
            with streamlit.container(border=True):
                streamlit.markdown("**Tickets nach Status**")
                streamlit.altair_chart(
                    charts.donut_chart(
                        status_df,
                        "name",
                        "count",
                        color_domain=status.STATUS_ORDER,
                        color_range=[status.STATUS_HEX[s] for s in status.STATUS_ORDER],
                    )
                )
        with row2[1]:
            with streamlit.container(border=True):
                streamlit.markdown("**Tickets nach Fehlerkategorie**")
                streamlit.altair_chart(
                    charts.ranked_bar_chart(
                        category_df,
                        "name",
                        "count",
                        single_color="#0E6E7C",
                        value_title="Anzahl Tickets",
                        min_height=180,
                    )
                )


@streamlit.fragment(parallel=True)
def ticket_trend_section() -> None:
    with streamlit.container(border=True):
        header_cols = streamlit.container(horizontal=True, horizontal_alignment="distribute", vertical_alignment="center")
        with header_cols:
            streamlit.markdown("**Tickets im Zeitverlauf**")
            interval_label = streamlit.segmented_control(
                "Intervall",
                options=["Tag", "Woche", "Monat"],
                default="Woche",
                key="dashboard_trend_interval",
                label_visibility="collapsed",
            )
        interval_map = {"Tag": "day", "Woche": "week", "Monat": "month"}
        interval = interval_map.get(interval_label or "Woche", "week")

        with streamlit.skeleton(height=280):
            trend = api_client.load_ticket_trend(interval=interval)
            if not trend:
                streamlit.info("Keine Verlaufsdaten verf\u00fcgbar.")
                return
            trend_df = pandas.DataFrame(trend)
            streamlit.altair_chart(
                charts.trend_area_chart(
                    trend_df,
                    "period",
                    ["incident_count", "service_request_count"],
                    labels={"incident_count": "Incident", "service_request_count": "Service Request"},
                    colors=status.TICKET_TYPE_HEX,
                )
            )


@streamlit.fragment(parallel=True)
def top_machines_section() -> None:
    with streamlit.container(border=True):
        streamlit.markdown("**Maschinen mit den meisten Fehlern** (Top 5)")
        streamlit.caption("Vollst\u00e4ndige Aufschl\u00fcsselung inkl. Verf\u00fcgbarkeit und MTTR/MTBF unter *Production Reporting*.")
        with streamlit.skeleton(height=200):
            error_rate = api_client.load_error_rate()
            if not error_rate:
                streamlit.info("Keine KPI-Daten verf\u00fcgbar.")
                return
            top5 = pandas.DataFrame(error_rate).sort_values("error_count", ascending=False).head(5)
            streamlit.altair_chart(
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
streamlit.space("small")
ticket_breakdown_charts()
streamlit.space("small")
ticket_trend_section()
streamlit.space("small")
top_machines_section()
