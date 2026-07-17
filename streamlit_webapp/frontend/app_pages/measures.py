"""Wartungsma\u00dfnahmen: erfassen und einsehen."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import api_client

st.title(":material/handyman: Wartungsma\u00dfnahmen")
st.caption("Durchgef\u00fchrte oder geplante Wartungsma\u00dfnahmen je Maschine erfassen und einsehen.")

machines = api_client.load_machines()

if not machines:
    st.info("Keine Maschinen verf\u00fcgbar.", icon=":material/search_off:")
else:
    machine_options = {machine["name"]: machine["id"] for machine in machines}

    with st.form("measure_form"):
        st.markdown("**Neue Ma\u00dfnahme erfassen**")
        selected_machine = st.selectbox("Maschine", options=sorted(machine_options))
        description = st.text_area(
            "Beschreibung der Ma\u00dfnahme",
            placeholder="Zum Beispiel: Sensorik gereinigt und neu kalibriert",
        )
        start_date = st.date_input("Startdatum")
        submitted = st.form_submit_button(
            "Ma\u00dfnahme speichern", icon=":material/save:", type="primary"
        )

    if submitted:
        if not description.strip():
            st.warning("Bitte eine Beschreibung eingeben.", icon=":material/edit_note:")
        else:
            with st.spinner("Speichere\u2026"):
                result = api_client.create_measure(
                    machine_id=machine_options[selected_machine],
                    description=description.strip(),
                    start_date=start_date.isoformat(),
                )
            if result is not None:
                st.toast("Ma\u00dfnahme gespeichert.", icon=":material/check_circle:")
                st.rerun()

    st.space("small")
    st.subheader("Vorhandene Ma\u00dfnahmen")

    measures = api_client.load_measures()
    if not measures:
        st.info("Keine Ma\u00dfnahmen gefunden.", icon=":material/search_off:")
    else:
        measures_df = pd.DataFrame(measures).sort_values("start_date", ascending=False)
        st.dataframe(
            measures_df,
            column_config={
                "id": st.column_config.NumberColumn("ID", width="small"),
                "machine_id": None,
                "machine_name": st.column_config.TextColumn("Maschine"),
                "description": st.column_config.TextColumn("Beschreibung", width="large"),
                "start_date": st.column_config.DateColumn("Startdatum", format="DD.MM.YYYY"),
            },
            hide_index=True,
        )
