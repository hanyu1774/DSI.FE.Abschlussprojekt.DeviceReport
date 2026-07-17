"""Production Reporting: Maschinen-KPIs auf Basis der Event-Historie."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import api_client, charts

st.title(":material/monitoring: Production Reporting")
st.caption("Maschinen-Kennzahlen auf Basis von Fehler-, Wartungs- und Offline-Events.")

tab_error, tab_availability, tab_mttr = st.tabs(["Fehler & Stillstand", "Verf\u00fcgbarkeit", "MTTR / MTBF"])

with tab_error:
    data = api_client.load_error_rate()
    if not data:
        st.info("Keine Daten verf\u00fcgbar.", icon=":material/search_off:")
    else:
        df = pd.DataFrame(data)
        st.altair_chart(
            charts.ranked_bar_chart(
                df, "machine_name", "error_count",
                single_color="#C96A1F", value_title="Anzahl Fehler-Events", bar_height=30,
            )
        )
        st.dataframe(
            df,
            column_config={
                "machine_id": None,
                "machine_name": st.column_config.TextColumn("Maschine"),
                "error_count": st.column_config.NumberColumn("Fehler"),
                "maintenance_count": st.column_config.NumberColumn("Wartungen"),
                "offline_count": st.column_config.NumberColumn("Offline-Ereignisse"),
                "total_downtime_minutes": st.column_config.NumberColumn(
                    "Stillstand gesamt (Min.)", format="%.0f"
                ),
            },
            hide_index=True,
        )

with tab_availability:
    data = api_client.load_availability()
    if not data:
        st.info("Keine Daten verf\u00fcgbar.", icon=":material/search_off:")
    else:
        df = pd.DataFrame(data)
        st.altair_chart(
            charts.ranked_bar_chart(
                df, "machine_name", "availability_percent",
                single_color="#0E6E7C", value_title="Verf\u00fcgbarkeit (%)", bar_height=30,
            )
        )
        st.caption(
            "Verf\u00fcgbarkeit = 1 \u2212 (Stillstand durch St\u00f6rungen/Offline) \u00f7 beobachteter "
            "Gesamtzeitraum. Geplante Wartung z\u00e4hlt nicht als Verf\u00fcgbarkeitsverlust."
        )
        st.dataframe(
            df,
            column_config={
                "machine_id": None,
                "machine_name": st.column_config.TextColumn("Maschine"),
                "availability_percent": st.column_config.NumberColumn("Verf\u00fcgbarkeit", format="%.2f %%"),
                "downtime_minutes": st.column_config.NumberColumn("Stillstand (Min.)", format="%.0f"),
                "period_days": st.column_config.NumberColumn("Betrachteter Zeitraum (Tage)", format="%.0f"),
            },
            hide_index=True,
        )

with tab_mttr:
    data = api_client.load_mttr_mtbf()
    if not data:
        st.info("Keine Daten verf\u00fcgbar.", icon=":material/search_off:")
    else:
        df = pd.DataFrame(data)
        chart_cols = st.columns(2)
        with chart_cols[0]:
            st.markdown("**MTTR \u2013 mittlere Reparaturzeit**")
            mttr_df = df.dropna(subset=["mttr_minutes"])
            st.altair_chart(
                charts.ranked_bar_chart(
                    mttr_df, "machine_name", "mttr_minutes",
                    single_color="#B8922A", value_title="MTTR (Min.)", bar_height=26, min_height=180,
                )
            )
        with chart_cols[1]:
            st.markdown("**MTBF \u2013 mittlere Zeit zwischen Ausf\u00e4llen**")
            mtbf_df = df.dropna(subset=["mtbf_hours"])
            st.altair_chart(
                charts.ranked_bar_chart(
                    mtbf_df, "machine_name", "mtbf_hours",
                    single_color="#5C7F62", value_title="MTBF (Std.)", bar_height=26, min_height=180,
                )
            )

        st.dataframe(
            df,
            column_config={
                "machine_id": None,
                "machine_name": st.column_config.TextColumn("Maschine"),
                "failure_count": st.column_config.NumberColumn("Anzahl Ausf\u00e4lle"),
                "mttr_minutes": st.column_config.NumberColumn("MTTR (Min.)", format="%.1f"),
                "mtbf_hours": st.column_config.NumberColumn("MTBF (Std.)", format="%.1f"),
            },
            hide_index=True,
        )
