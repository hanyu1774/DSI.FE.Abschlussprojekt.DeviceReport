"""Wartungsma\u00dfnahmen: erfassen und einsehen."""

from __future__ import annotations

import pandas
import streamlit

from components import api_client

streamlit.title(":material/handyman: Wartungsma\u00dfnahmen")
streamlit.caption("Durchgef\u00fchrte oder geplante Wartungsma\u00dfnahmen je Maschine erfassen und einsehen.")

machines = api_client.load_machines()

if not machines:
    streamlit.info("Keine Maschinen verf\u00fcgbar.", icon=":material/search_off:")
else:
    machine_options = {machine["name"]: machine["id"] for machine in machines}

    with streamlit.form("measure_form"):
        streamlit.markdown("**Neue Ma\u00dfnahme erfassen**")
        selected_machine = streamlit.selectbox("Maschine", options=sorted(machine_options))
        description = streamlit.text_area(
            "Beschreibung der Ma\u00dfnahme",
            placeholder="Zum Beispiel: Sensorik gereinigt und neu kalibriert",
        )
        start_date = streamlit.date_input("Startdatum")
        submitted = streamlit.form_submit_button(
            "Ma\u00dfnahme speichern", icon=":material/save:", type="primary"
        )

    if submitted:
        if not description.strip():
            streamlit.warning("Bitte eine Beschreibung eingeben.", icon=":material/edit_note:")
        else:
            with streamlit.spinner("Speichere\u2026"):
                result = api_client.create_measure(
                    machine_id=machine_options[selected_machine],
                    description=description.strip(),
                    start_date=start_date.isoformat(),
                )
            if result is not None:
                streamlit.toast("Ma\u00dfnahme gespeichert.", icon=":material/check_circle:")
                streamlit.rerun()

    streamlit.space("small")
    streamlit.subheader("Vorhandene Ma\u00dfnahmen")

    measures = api_client.load_measures()
    if not measures:
        streamlit.info("Keine Ma\u00dfnahmen gefunden.", icon=":material/search_off:")
    else:
        measures_df = pandas.DataFrame(measures).sort_values("start_date", ascending=False)
        streamlit.dataframe(
            measures_df,
            column_config={
                "id": streamlit.column_config.NumberColumn("ID", width="small"),
                "machine_id": None,
                "machine_name": streamlit.column_config.TextColumn("Maschine"),
                "description": streamlit.column_config.TextColumn("Beschreibung", width="large"),
                "start_date": streamlit.column_config.DateColumn("Startdatum", format="DD.MM.YYYY"),
            },
            hide_index=True,
        )
