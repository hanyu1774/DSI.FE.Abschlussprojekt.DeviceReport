"""Production Reporting: Maschinen-KPIs auf Basis der Event-Historie."""

from __future__ import annotations

import pandas
import streamlit

from components import api_client, charts

streamlit.title(":material/monitoring: Production Reporting")
streamlit.caption("Maschinen-Kennzahlen auf Basis von Fehler-, Wartungs- und Offline-Events.")

tab_error, tab_availability, tab_mttr = streamlit.tabs(["Fehler & Stillstand", "Verf\u00fcgbarkeit", "MTTR / MTBF"])

with tab_error:
    data = api_client.load_error_rate()
    if not data:
        streamlit.info("Keine Daten verf\u00fcgbar.", icon=":material/search_off:")
    else:
        df = pandas.DataFrame(data)
        streamlit.altair_chart(
            charts.ranked_bar_chart(
                df, "machine_name", "error_count",
                single_color="#C96A1F", value_title="Anzahl Fehler-Events", bar_height=30,
            )
        )
        streamlit.dataframe(
            df,
            column_config={
                "machine_id": None,
                "machine_name": streamlit.column_config.TextColumn("Maschine"),
                "error_count": streamlit.column_config.NumberColumn("Fehler"),
                "maintenance_count": streamlit.column_config.NumberColumn("Wartungen"),
                "offline_count": streamlit.column_config.NumberColumn("Offline-Ereignisse"),
                "total_downtime_minutes": streamlit.column_config.NumberColumn(
                    "Stillstand gesamt (Min.)", format="%.0f"
                ),
            },
            hide_index=True,
        )

with tab_availability:
    data = api_client.load_availability()
    if not data:
        streamlit.info("Keine Daten verf\u00fcgbar.", icon=":material/search_off:")
    else:
        df = pandas.DataFrame(data)
        streamlit.altair_chart(
            charts.ranked_bar_chart(
                df, "machine_name", "availability_percent",
                single_color="#0E6E7C", value_title="Verf\u00fcgbarkeit (%)", bar_height=30,
            )
        )
        streamlit.caption(
            "Verf\u00fcgbarkeit = 1 \u2212 (Stillstand durch streamlit\u00f6rungen/Offline) \u00f7 beobachteter "
            "Gesamtzeitraum. Geplante Wartung z\u00e4hlt nicht als Verf\u00fcgbarkeitsverlust."
        )
        streamlit.dataframe(
            df,
            column_config={
                "machine_id": None,
                "machine_name": streamlit.column_config.TextColumn("Maschine"),
                "availability_percent": streamlit.column_config.NumberColumn("Verf\u00fcgbarkeit", format="%.2f %%"),
                "downtime_minutes": streamlit.column_config.NumberColumn("Stillstand (Min.)", format="%.0f"),
                "period_days": streamlit.column_config.NumberColumn("Betrachteter Zeitraum (Tage)", format="%.0f"),
            },
            hide_index=True,
        )

with tab_mttr:
    data = api_client.load_mttr_mtbf()
    if not data:
        streamlit.info("Keine Daten verf\u00fcgbar.", icon=":material/search_off:")
    else:
        df = pandas.DataFrame(data)
        chart_cols = streamlit.columns(2)
        with chart_cols[0]:
            streamlit.markdown("**MTTR \u2013 mittlere Reparaturzeit**")
            mttr_df = df.dropna(subset=["mttr_minutes"])
            streamlit.altair_chart(
                charts.ranked_bar_chart(
                    mttr_df, "machine_name", "mttr_minutes",
                    single_color="#B8922A", value_title="MTTR (Min.)", bar_height=26, min_height=180,
                )
            )
        with chart_cols[1]:
            streamlit.markdown("**MTBF \u2013 mittlere Zeit zwischen Ausf\u00e4llen**")
            mtbf_df = df.dropna(subset=["mtbf_hours"])
            streamlit.altair_chart(
                charts.ranked_bar_chart(
                    mtbf_df, "machine_name", "mtbf_hours",
                    single_color="#5C7F62", value_title="MTBF (Std.)", bar_height=26, min_height=180,
                )
            )

        streamlit.dataframe(
            df,
            column_config={
                "machine_id": None,
                "machine_name": streamlit.column_config.TextColumn("Maschine"),
                "failure_count": streamlit.column_config.NumberColumn("Anzahl Ausf\u00e4lle"),
                "mttr_minutes": streamlit.column_config.NumberColumn("MTTR (Min.)", format="%.1f"),
                "mtbf_hours": streamlit.column_config.NumberColumn("MTBF (Std.)", format="%.1f"),
            },
            hide_index=True,
        )
