"""
Zentrale "Leitstand"-Farbpalette fuer das gesamte Frontend.

`ColorToken` traegt die Bedeutung (WAS die Farbe ausdrueckt), `PALETTE`
ordnet jedem Token den tatsaechlichen Hex-Wert zu (WIE sie aussieht). Diese
Trennung ist der Grund, warum Streamlit-Diagramme (components/charts.py,
status.py) und der PDF-Export (pdf_export.py) hier ausschliesslich
importieren, statt eigene Hex-Werte zu pflegen. Beide Ausgaben koennen so
nie wieder auseinanderdriften. Soll sich mal ein Ton aendern, wird er genau
einmal hier angepasst.
"""

from __future__ import annotations

from enum import Enum, auto


class ColorToken(Enum):
    PRIMARY = auto()    # Hauptfarbe: Kopfzeilen, primaere Kategorie ohne eigene Semantik
    SECONDARY = auto()  # neutrale Kategorie ("Offen")
    ACTIVE = auto()      # "aktiv / in Bearbeitung"
    DARK_LAVENDER_BLUE = auto()
    GREEN = auto()       # positiv / geloest / niedrige Prioritaet
    OLIVE = auto()       # zweite neutrale Kategorie (Service Request, Geschlossen, MTBF)
    ORANGE = auto()       # hohe Prioritaet / auffaellige Fehlerzahlen
    YELLOW = auto()      # mittlere Prioritaet
    RED = auto()          # kritische Prioritaet / Incident
    RUBY_RED = auto()
    PURPLE = auto()
    TEXT = auto()         # Fliesstext (PDF)
    WHITE = auto()
    GREY = auto()
    GRID = auto()         # rein strukturell (Tabellenlinien/Rahmen), keine Bedeutungsfarbe
    ZEBRA = auto()


PALETTE: dict[ColorToken, str] = {
    ColorToken.PRIMARY: "#2A8DE5",
    ColorToken.SECONDARY: "#8de52a",
    ColorToken.ACTIVE: "#3434ff",
    ColorToken.DARK_LAVENDER_BLUE: "#2A58E5",
    ColorToken.GREEN: "#288c36",
    ColorToken.OLIVE: "#647e35",
    ColorToken.ORANGE: "#D64E3A",
    ColorToken.YELLOW: "#F8CB20",
    ColorToken.RED: "#e52a2f",
    ColorToken.RUBY_RED: "#9B111E",
    ColorToken.PURPLE: "#822ae5",
    ColorToken.TEXT: "#1B1F24",
    ColorToken.WHITE: "#FFFFFF",
    ColorToken.GREY: "#808080",
    ColorToken.GRID: "#D3D9E0",
    ColorToken.ZEBRA: "#F5F7FA",
}
