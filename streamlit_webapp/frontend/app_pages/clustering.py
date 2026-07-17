"""Ticket-Clustering: thematische Gruppierung \u00e4hnlicher Ticket-Beschreibungen."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components import api_client, charts

st.title(":material/hub: Ticket-Clustering")
st.caption(
    "Gruppiert \u00e4hnliche Ticket-Beschreibungen automatisch per Text-Mining (TF-IDF + KMeans) - "
    "n\u00fctzlich, um wiederkehrende Themen zu erkennen, auch bei Service Requests ohne Fehlercode."
)

n_clusters = st.slider("Anzahl Cluster", min_value=2, max_value=12, value=6, key="cluster_count")

with st.spinner("Berechne Cluster\u2026"):
    clusters = api_client.load_clusters(n_clusters)

if not clusters:
    st.info("Keine Cluster-Daten verf\u00fcgbar.", icon=":material/search_off:")
else:
    sizes_df = pd.DataFrame(
        [{"cluster": f"Cluster {c['cluster_id']}", "tickets": c["size"]} for c in clusters]
    )
    st.altair_chart(
        charts.ranked_bar_chart(
            sizes_df, "cluster", "tickets",
            single_color="#0E6E7C", value_title="Anzahl Tickets", bar_height=32, min_height=160,
        )
    )

    st.space("small")

    for cluster in clusters:
        with st.container(border=True):
            header = st.container(
                horizontal=True, horizontal_alignment="distribute", vertical_alignment="center"
            )
            with header:
                st.markdown(f"**Cluster {cluster['cluster_id']}** \u2014 {cluster['size']} Tickets")
                if cluster["dominant_category"]:
                    st.badge(cluster["dominant_category"], icon=":material/category:", color="primary")

            if cluster["top_keywords"]:
                st.caption("Schl\u00fcsselbegriffe: " + " \u00b7 ".join(f"`{kw}`" for kw in cluster["top_keywords"]))

            with st.expander(f"{len(cluster['example_descriptions'])} Beispiel-Tickets ansehen", icon=":material/description:"):
                for example in cluster["example_descriptions"]:
                    st.markdown(f"- {example}")
