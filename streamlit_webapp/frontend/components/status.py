"""
Einheitliche Zuordnung von Prioritaet/Status/Ticket-Typ zu Farbe, Icon und
deutschem Label - fuer konsistente `streamlit.badge`-Anzeigen im ganzen Frontend.

Nutzt bewusst natives `streamlit.badge` mit den ueber `.streamlit/config.toml`
gesetzten Semantikfarben (redColor/orangeColor/... in "Leitstand"-Toenen)
statt eigenem CSS - das haelt Farbe & Theme an einer Stelle synchron.
"""

from __future__ import annotations

import streamlit

PRIORITY_LABELS = {"critical": "Kritisch", "high": "Hoch", "medium": "Mittel", "low": "Niedrig"}
PRIORITY_COLORS = {"critical": "red", "high": "orange", "medium": "yellow", "low": "gray"}
PRIORITY_ICONS = {
    "critical": ":material/emergency:",
    "high": ":material/warning:",
    "medium": ":material/info:",
    "low": ":material/check_circle:",
}
PRIORITY_ORDER = ["critical", "high", "medium", "low"]

STATUS_COLORS = {
    "Offen": "gray",
    "In Bearbeitung": "blue",
    "Gel\u00f6st": "green",
    "Geschlossen": "violet",
}
STATUS_ICONS = {
    "Offen": ":material/radio_button_unchecked:",
    "In Bearbeitung": ":material/schedule:",
    "Gel\u00f6st": ":material/task_alt:",
    "Geschlossen": ":material/done_all:",
}
STATUS_ORDER = ["Offen", "In Bearbeitung", "Gel\u00f6st", "Geschlossen"]

TICKET_TYPE_COLORS = {"Incident": "primary", "Service Request": "violet"}
TICKET_TYPE_ICONS = {
    "Incident": ":material/emergency:",
    "Service Request": ":material/handyman:",
}

SEVERITY_COLORS = {"critical": "red", "high": "orange", "medium": "yellow", "low": "gray"}

# Hex-Entsprechungen der Named Colors aus .streamlit/config.toml. Streamlit-
# Badges kennen nur die Namen ("red", "orange", ...); Altair-Diagramme
# brauchen konkrete Hex-Werte, um dieselbe Farbsemantik durchzuziehen (z. B.
# "kritisch" ist ueberall derselbe Ziegelrot-Ton - im Badge wie im Diagramm).
HEX = {
    "red": "#A63B32",
    "orange": "#C96A1F",
    "yellow": "#B8922A",
    "green": "#5C7F62",
    "blue": "#2B6CA3",
    "violet": "#7A5C8E",
    "gray": "#6B7280",
    "primary": "#0E6E7C",
}

PRIORITY_HEX = {key: HEX[value] for key, value in PRIORITY_COLORS.items()}
STATUS_HEX = {key: HEX[value] for key, value in STATUS_COLORS.items()}
TICKET_TYPE_HEX = {key: HEX[value] for key, value in TICKET_TYPE_COLORS.items()}


def priority_badge(priority: str) -> None:
    streamlit.badge(
        PRIORITY_LABELS.get(priority, priority),
        icon=PRIORITY_ICONS.get(priority),
        color=PRIORITY_COLORS.get(priority, "gray"),
    )


def status_badge(status: str) -> None:
    streamlit.badge(status, icon=STATUS_ICONS.get(status), color=STATUS_COLORS.get(status, "gray"))


def ticket_type_badge(ticket_type: str) -> None:
    streamlit.badge(
        ticket_type,
        icon=TICKET_TYPE_ICONS.get(ticket_type),
        color=TICKET_TYPE_COLORS.get(ticket_type, "gray"),
    )


def severity_badge(severity: str) -> None:
    streamlit.badge(
        severity.capitalize(),
        icon=PRIORITY_ICONS.get(severity),
        color=SEVERITY_COLORS.get(severity, "gray"),
    )
