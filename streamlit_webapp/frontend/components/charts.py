"""
Wiederverwendbare Altair-Diagramm-Bausteine (Kreis-/Donut-, Balken- und
Verlaufsdiagramme).

Altair statt Plotly/matplotlib, siehe Streamlit-Empfehlung: Vega-basierte
Diagramme sind in Streamlit nativ eingebettet, uebernehmen automatisch das
Theme aus `.streamlit/config.toml` und sind ohne Zusatzinstallation dabei.
Fuer Prioritaet/Status/Typ wird zusaetzlich die feste Farbsemantik aus
`components/status.py` als explizite Altair-Farbskala uebergeben, damit
z. B. "kritisch" im Diagramm immer densel­ben Ton hat wie im Badge -
unabhaengig davon, welche anderen Kategorien noch vorkommen.
"""

from __future__ import annotations

import altair as alt
import pandas as pd


def donut_chart(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    *,
    color_domain: list[str] | None = None,
    color_range: list[str] | None = None,
    height: int = 300,
) -> alt.Chart:
    """Donut-/Kreisdiagramm fuer eine kategoriale Verteilung."""
    if color_domain and color_range:
        color = alt.Color(
            f"{category_col}:N",
            title=None,
            scale=alt.Scale(domain=color_domain, range=color_range),
            legend=alt.Legend(orient="bottom", columns=2),
        )
    else:
        color = alt.Color(f"{category_col}:N", title=None, legend=alt.Legend(orient="bottom", columns=2))

    return (
        alt.Chart(df)
        .mark_arc(innerRadius=height * 0.22, stroke="#F5F7FA", strokeWidth=2)
        .encode(
            theta=alt.Theta(f"{value_col}:Q", stack=True),
            color=color,
            order=alt.Order(f"{value_col}:Q", sort="descending"),
            tooltip=[
                alt.Tooltip(f"{category_col}:N", title="Kategorie"),
                alt.Tooltip(f"{value_col}:Q", title="Anzahl"),
            ],
        )
        .properties(height=height)
    )


def ranked_bar_chart(
    df: pd.DataFrame,
    category_col: str,
    value_col: str,
    *,
    color_domain: list[str] | None = None,
    color_range: list[str] | None = None,
    single_color: str | None = None,
    value_title: str | None = None,
    bar_height: int = 28,
    min_height: int = 200,
    show_values: bool = True,
    category_order: list[str] | None = None,
) -> alt.Chart:
    """Horizontal sortiertes Balkendiagramm (z. B. Fehler je Maschine).

    Ohne `category_order` wird nach `value_col` aufsteigend sortiert (gut
    fuer Rankings ohne inhaerente Reihenfolge). Mit `category_order` (z. B.
    die feste Prioritaets-Reihenfolge kritisch->niedrig) wird stattdessen
    diese Reihenfolge beibehalten, damit z. B. "Kritisch" immer oben steht,
    unabhaengig von der Anzahl.
    """
    if category_order:
        ordered = df.set_index(category_col).loc[[c for c in reversed(category_order) if c in df[category_col].values]].reset_index()
    else:
        ordered = df.sort_values(value_col, ascending=True)

    if single_color:
        color = alt.value(single_color)
    elif color_domain and color_range:
        color = alt.Color(
            f"{category_col}:N",
            scale=alt.Scale(domain=color_domain, range=color_range),
            legend=None,
        )
    else:
        color = alt.value("#0E6E7C")

    # Etwas Luft rechts vom groessten Balken, damit die Werte-Beschriftung
    # (mark_text) nicht am Diagrammrand abgeschnitten wird.
    max_value = float(ordered[value_col].max()) if len(ordered) else 1.0
    x_scale = alt.Scale(domain=[0, max_value * 1.16])

    bars = (
        alt.Chart(ordered)
        .mark_bar()
        .encode(
            x=alt.X(f"{value_col}:Q", title=value_title or value_col, scale=x_scale),
            y=alt.Y(f"{category_col}:N", sort=None, title=None),
            color=color,
            tooltip=[
                alt.Tooltip(f"{category_col}:N", title="Kategorie"),
                alt.Tooltip(f"{value_col}:Q", title=value_title or value_col),
            ],
        )
    )

    height = max(min_height, bar_height * len(ordered))
    chart = bars.properties(height=height)

    if show_values:
        text = (
            alt.Chart(ordered)
            .mark_text(align="left", baseline="middle", dx=5)
            .encode(
                x=alt.X(f"{value_col}:Q", scale=x_scale),
                y=alt.Y(f"{category_col}:N", sort=None),
                text=f"{value_col}:Q",
            )
        )
        chart = (bars + text).properties(height=height)

    return chart


def trend_area_chart(
    df: pd.DataFrame,
    x_col: str,
    y_cols: list[str],
    *,
    labels: dict[str, str] | None = None,
    colors: dict[str, str] | None = None,
    height: int = 280,
) -> alt.Chart:
    """Gestapeltes Flaechendiagramm fuer einen Zeitverlauf (z. B. Tickets/Woche)."""
    labels = labels or {col: col for col in y_cols}
    long_df = df.melt(id_vars=[x_col], value_vars=y_cols, var_name="serie", value_name="anzahl")
    long_df["serie"] = long_df["serie"].map(labels).fillna(long_df["serie"])

    domain = list(labels.values())
    if colors:
        color = alt.Color(
            "serie:N",
            title=None,
            scale=alt.Scale(domain=domain, range=[colors.get(name, "#0E6E7C") for name in domain]),
            legend=alt.Legend(orient="bottom"),
        )
    else:
        color = alt.Color("serie:N", title=None, legend=alt.Legend(orient="bottom"))

    return (
        alt.Chart(long_df)
        .mark_area(opacity=0.75, interpolate="monotone", line=True)
        .encode(
            x=alt.X(f"{x_col}:T", title=None),
            y=alt.Y("anzahl:Q", title="Anzahl Tickets", stack=None),
            color=color,
            tooltip=[
                alt.Tooltip(f"{x_col}:T", title="Zeitraum"),
                alt.Tooltip("serie:N", title="Typ"),
                alt.Tooltip("anzahl:Q", title="Anzahl"),
            ],
        )
        .properties(height=height)
    )
