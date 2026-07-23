"""
PDF-Export fuer den Analysebericht.

Warum kein React-PDF-Feature (@react-pdf/renderer & Co.)? Diese Bibliotheken
bauen PDFs aus React-Komponenten und laufen im Browser/Node. Das Frontend
hier ist aber eine reine Python/Streamlit-App ohne eigenes React-Build (kein
package.json, kein Node im Projekt). Ein React-PDF-Feature einzubauen wuerde
bedeuten, eine komplette Streamlit-"Custom Component" (eigenes React+
TypeScript-Projekt, Bundler, JS-Build-Pipeline) nur fuer diesen einen Button
aufzuziehen. Der pythonische, deutlich schlankere Weg fuer Streamlit ist ein
serverseitig (in Python) gebautes PDF, das per `st.download_button`
ausgeliefert wird. Dafuer sorgt dieses Modul mit `reportlab` (PDF-Layout)
und `vl-convert-python` (rendert die vorhandenen Altair-Diagramme aus
`components/charts.py` verlustfrei als PNG, ganz ohne Browser/Selenium).

Farbkonzept: siehe Kommentar bei PDF_COLORS weiter unten.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any

import altair
import pandas
import vl_convert as vlc
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from components import api_client, charts, status
from components.colors import ColorToken, PALETTE
from components.formatting import format_date, format_datetime, format_hours


PRIMARY = PALETTE[ColorToken.PRIMARY]
SECONDARY = PALETTE[ColorToken.SECONDARY]
ACTIVE = PALETTE[ColorToken.ACTIVE]
GREEN = PALETTE[ColorToken.GREEN]
OLIVE = PALETTE[ColorToken.OLIVE]
ORANGE = PALETTE[ColorToken.ORANGE]
YELLOW = PALETTE[ColorToken.YELLOW]
RED = PALETTE[ColorToken.RED]

TEXT = PALETTE[ColorToken.TEXT]
WHITE = PALETTE[ColorToken.WHITE]
GRID = PALETTE[ColorToken.GRID]         # rein strukturell (Tabellenlinien/Rahmen), keine Bedeutungsfarbe
ZEBRA = PALETTE[ColorToken.ZEBRA]

PRIORITY_DOMAIN = status.PRIORITY_ORDER
PRIORITY_RANGE = [status.PRIORITY_HEX[p] for p in status.PRIORITY_ORDER]
PRIORITY_LABELS = status.PRIORITY_LABELS

STATUS_DOMAIN = status.STATUS_ORDER
STATUS_RANGE = [status.STATUS_HEX[s] for s in status.STATUS_ORDER]

TICKET_TYPE_DOMAIN = list(status.TICKET_TYPE_HEX.keys())
TICKET_TYPE_RANGE = list(status.TICKET_TYPE_HEX.values())

PAGE_WIDTH_MM = 170  # A4 minus Raender (20mm links/rechts)


# ---------------------------------------------------------------------------
# Low-Level Helfer
# ---------------------------------------------------------------------------

def _hx(hex_code: str) -> colors.Color:
    return colors.HexColor(hex_code)


def _chart_to_image(chart: altair.Chart, *, width_mm: float, chart_px_width: int = 700) -> Image:
    """Rendert ein bestehendes Altair-Diagramm (aus components/charts.py)
    verlustfrei als PNG, ohne Browser/Selenium - siehe Moduldocstring.

    `components/charts.py` setzt bewusst keine feste `width` (die App laesst
    Streamlit/Vega die Breite an den Container anpassen). Fuer das PDF
    brauchen wir aber eine deterministische Pixelbreite, damit das
    Seitenverhaeltnis beim Einbetten stimmt - die wird hier nachtraeglich
    per `.properties(width=...)` ergaenzt (Altair mergt das verlustfrei mit
    der von charts.py bereits gesetzten `height`).
    """
    chart = chart.properties(width=chart_px_width)
    png_bytes = vlc.vegalite_to_png(chart.to_json(), scale=2)
    pil_img = PILImage.open(io.BytesIO(png_bytes))
    ratio = pil_img.height / pil_img.width
    width = width_mm * mm
    return Image(io.BytesIO(png_bytes), width=width, height=width * ratio)


def _styles() -> dict[str, ParagraphStyle]:
    return {
        "title": ParagraphStyle("title", fontName="Helvetica-Bold", fontSize=22, textColor=_hx(WHITE), leading=26),
        "subtitle": ParagraphStyle("subtitle", fontName="Helvetica", fontSize=11, textColor=_hx(WHITE), leading=15),
        "h1": ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=14, textColor=_hx(WHITE), leading=17),
        "h2": ParagraphStyle("h2", fontName="Helvetica-Bold", fontSize=10.5, textColor=_hx(PRIMARY), leading=13, spaceBefore=6, spaceAfter=3),
        "body": ParagraphStyle("body", fontName="Helvetica", fontSize=9.5, textColor=_hx(TEXT), leading=13),
        "caption": ParagraphStyle("caption", fontName="Helvetica-Oblique", fontSize=8, textColor=_hx(TEXT), leading=11),
        "cell": ParagraphStyle("cell", fontName="Helvetica", fontSize=8, textColor=_hx(TEXT), leading=10),
        "cell_head": ParagraphStyle("cell_head", fontName="Helvetica-Bold", fontSize=8, textColor=_hx(WHITE), leading=10),
        "metric_value": ParagraphStyle("metric_value", fontName="Helvetica-Bold", fontSize=19, textColor=_hx(PRIMARY), leading=23, alignment=TA_CENTER),
        "metric_label": ParagraphStyle("metric_label", fontName="Helvetica", fontSize=8.5, textColor=_hx(TEXT), leading=11, alignment=TA_CENTER),
    }


def _section_header(text: str, styles: dict[str, ParagraphStyle]) -> Table:
    t = Table([[Paragraph(text, styles["h1"])]], colWidths=[PAGE_WIDTH_MM * mm])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hx(PRIMARY)),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def _empty_note(styles: dict[str, ParagraphStyle]) -> Paragraph:
    return Paragraph("Keine Daten verf\u00fcgbar.", styles["caption"])


def _metric_row(metrics: list[tuple[str, str]], styles: dict[str, ParagraphStyle]) -> Table:
    header = [Paragraph(value, styles["metric_value"]) for _, value in metrics]
    footer = [Paragraph(label, styles["metric_label"]) for label, _ in metrics]
    col_width = PAGE_WIDTH_MM * mm / len(metrics)
    t = Table([header, footer], colWidths=[col_width] * len(metrics))
    t.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, _hx(GRID)),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, _hx(GRID)),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _data_table(headers: list[str], rows: list[list[Any]], col_widths_mm: list[float], styles: dict[str, ParagraphStyle]) -> Table:
    head = [Paragraph(h, styles["cell_head"]) for h in headers]
    body = [[Paragraph("\u2013" if cell in (None, "") else str(cell), styles["cell"]) for cell in row] for row in rows]
    data = [head] + body
    t = Table(data, colWidths=[w * mm for w in col_widths_mm], repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), _hx(PRIMARY)),
        ("GRID", (0, 0), (-1, -1), 0.4, _hx(GRID)),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for i in range(2, len(data), 2):
        style.append(("BACKGROUND", (0, i), (-1, i), _hx(ZEBRA)))
    t.setStyle(TableStyle(style))
    return t


def _two_up(img_left, img_right) -> Table:
    t = Table([[img_left, img_right]], colWidths=[(PAGE_WIDTH_MM / 2) * mm] * 2)
    t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (1, 0), (1, 0), 6)]))
    return t


# ---------------------------------------------------------------------------
# Section-Builder - jede Funktion liefert eine Liste von Flowables und wird
# nur aufgerufen, wenn der Nutzer den jeweiligen Abschnitt ausgewaehlt hat.
# ---------------------------------------------------------------------------

def section_kpi_overview() -> list:
    styles = _styles()
    block = [_section_header("KPI-\u00dcbersicht", styles), Spacer(1, 3 * mm)]

    machines = api_client.load_machines()
    summary = api_client.load_ticket_summary()
    response_times = api_client.load_response_times()
    overall = response_times.get("overall", {})

    metrics = [
        ("Maschinen", str(len(machines))),
        ("Offene Tickets", str(summary.get("open_count", 0))),
        ("Kritische Tickets", str(summary.get("critical_count", 0))),
        ("\u00d8 L\u00f6sungszeit", format_hours(overall.get("avg_time_to_resolve_hours")))
    ]
    block.append(_metric_row(metrics, styles))
    return block


def section_ticket_breakdown() -> list:
    styles = _styles()
    block = [_section_header("Ticket-Verteilung", styles), Spacer(1, 3 * mm)]

    summary = api_client.load_ticket_summary()
    if not summary:
        block.append(_empty_note(styles))
        return block

    type_df = pandas.DataFrame(summary["by_type"])
    priority_df = pandas.DataFrame(summary["by_priority"])
    status_df = pandas.DataFrame(summary["by_status"])
    category_df = pandas.DataFrame(summary["by_category"])

    if not type_df.empty and not priority_df.empty:
        priority_df["label"] = priority_df["name"].map(PRIORITY_LABELS).fillna(priority_df["name"])
        priority_order = [PRIORITY_LABELS[p] for p in PRIORITY_DOMAIN]
        type_chart = charts.donut_chart(type_df, "name", "count", color_domain=TICKET_TYPE_DOMAIN, color_range=TICKET_TYPE_RANGE, height=130)
        priority_chart = charts.ranked_bar_chart(
            priority_df, "label", "count", color_domain=priority_order, color_range=PRIORITY_RANGE,
            min_height=95, bar_height=22, category_order=priority_order, value_title="Anzahl",
        )
        block.append(Paragraph("Nach Typ & Priorit\u00e4t", styles["h2"]))
        block.append(_two_up(
            _chart_to_image(type_chart, width_mm=78, chart_px_width=300),
            _chart_to_image(priority_chart, width_mm=78, chart_px_width=340),
        ))
        block.append(Spacer(1, 3 * mm))

    if not status_df.empty and not category_df.empty:
        status_chart = charts.donut_chart(status_df, "name", "count", color_domain=STATUS_DOMAIN, color_range=STATUS_RANGE, height=130)
        category_chart = charts.ranked_bar_chart(category_df, "name", "count", single_color=PRIMARY, min_height=95, bar_height=22, value_title="Anzahl")
        block.append(Paragraph("Nach Status & Fehlerkategorie", styles["h2"]))
        block.append(_two_up(
            _chart_to_image(status_chart, width_mm=78, chart_px_width=300),
            _chart_to_image(category_chart, width_mm=78, chart_px_width=340),
        ))

    return block


def section_ticket_trend(interval: str = "week") -> list:
    styles = _styles()
    block = [_section_header("Ticket-Verlauf", styles), Spacer(1, 3 * mm)]

    trend = api_client.load_ticket_trend(interval=interval)
    if not trend:
        block.append(_empty_note(styles))
        return block

    trend_df = pandas.DataFrame(trend)
    chart = charts.trend_area_chart(
        trend_df, "period", ["incident_count", "service_request_count"],
        labels={"incident_count": "Incident", "service_request_count": "Service Request"},
        colors={"Incident": RED, "Service Request": PALETTE[ColorToken.YELLOW]},
        height=170,
    )
    block.append(_chart_to_image(chart, width_mm=PAGE_WIDTH_MM, chart_px_width=760))
    return block


def section_top_machines(top_n: int = 5) -> list:
    styles = _styles()
    block = [_section_header("Maschinen mit den meisten Fehlern", styles), Spacer(1, 3 * mm)]

    error_rate = api_client.load_error_rate()
    if not error_rate:
        block.append(_empty_note(styles))
        return block

    df = pandas.DataFrame(error_rate).sort_values("error_count", ascending=False).head(top_n)
    chart = charts.ranked_bar_chart(df, "machine_name", "error_count", single_color=ORANGE, value_title="Fehleranzahl", bar_height=24, min_height=100)
    block.append(_chart_to_image(chart, width_mm=PAGE_WIDTH_MM, chart_px_width=760))
    return block


def section_production_kpis() -> list:
    styles = _styles()
    block = [_section_header("Production-KPIs", styles), Spacer(1, 3 * mm)]

    error_rate = api_client.load_error_rate()
    availability = api_client.load_availability()
    mttr_mtbf = api_client.load_mttr_mtbf()

    if error_rate:
        block.append(Paragraph("Fehler & Stillstand je Maschine", styles["h2"]))
        df = pandas.DataFrame(error_rate)
        chart = charts.ranked_bar_chart(df, "machine_name", "error_count", single_color=ORANGE, value_title="Anzahl Fehler-Events", bar_height=20, min_height=90)
        block.append(_chart_to_image(chart, width_mm=PAGE_WIDTH_MM, chart_px_width=760))
        block.append(Spacer(1, 3 * mm))

    if availability:
        block.append(Paragraph("Verf\u00fcgbarkeit je Maschine", styles["h2"]))
        df = pandas.DataFrame(availability)
        chart = charts.ranked_bar_chart(df, "machine_name", "availability_percent", single_color=GREEN, value_title="Verf\u00fcgbarkeit (%)", bar_height=20, min_height=90)
        block.append(_chart_to_image(chart, width_mm=PAGE_WIDTH_MM, chart_px_width=760))
        block.append(Spacer(1, 3 * mm))

    if mttr_mtbf:
        df = pandas.DataFrame(mttr_mtbf)
        mttr_df = df.dropna(subset=["mttr_minutes"])
        mtbf_df = df.dropna(subset=["mtbf_hours"])
        if not mttr_df.empty and not mtbf_df.empty:
            block.append(Paragraph("MTTR (Reparaturzeit) & MTBF (Zeit zw. Ausf\u00e4llen)", styles["h2"]))
            mttr_chart = charts.ranked_bar_chart(mttr_df, "machine_name", "mttr_minutes", single_color=SECONDARY, value_title="MTTR (Min.)", bar_height=20, min_height=90)
            mtbf_chart = charts.ranked_bar_chart(mtbf_df, "machine_name", "mtbf_hours", single_color=OLIVE, value_title="MTBF (Std.)", bar_height=20, min_height=90)
            block.append(_two_up(
                _chart_to_image(mttr_chart, width_mm=78, chart_px_width=340),
                _chart_to_image(mtbf_chart, width_mm=78, chart_px_width=340),
            ))

    if not (error_rate or availability or mttr_mtbf):
        block.append(_empty_note(styles))
    return block


def section_ticket_list(limit: int = 50) -> list:
    styles = _styles()
    block = [_section_header(f"Ticket-Liste (neueste {limit})", styles), Spacer(1, 3 * mm)]

    tickets = api_client.load_tickets(limit=limit)
    if not tickets:
        block.append(_empty_note(styles))
        return block

    rows = [
        [t["id"], t["ticket_type"], t["machine_name"], PRIORITY_LABELS.get(t["priority"], t["priority"]),
         t["status"], format_datetime(t["created_at"]), format_hours(t.get("resolution_hours"))]
        for t in tickets
    ]
    headers = ["ID", "Typ", "Maschine", "Priorit\u00e4t", "Status", "Erstellt", "L\u00f6sungszeit"]
    widths = [10, 24, 30, 20, 26, 32, 28]
    block.append(_data_table(headers, rows, widths, styles))
    return block


def section_ticket_clusters(n_clusters: int = 6) -> list:
    styles = _styles()
    block = [_section_header("Ticket-Clustering", styles), Spacer(1, 3 * mm)]

    clusters = api_client.load_clusters(n_clusters)
    if not clusters:
        block.append(_empty_note(styles))
        return block

    rows = []
    for c in clusters:
        keywords = " \u00b7 ".join(c["top_keywords"][:5])
        rows.append([c["cluster_id"], c["size"], c.get("dominant_category") or "\u2013", keywords])
    headers = ["Cluster", "Gr\u00f6\u00dfe", "Kategorie", "Schl\u00fcsselbegriffe"]
    widths = [18, 18, 34, 100]
    block.append(_data_table(headers, rows, widths, styles))
    return block


def section_machines() -> list:
    styles = _styles()
    block = [_section_header("Maschinen-Stammdaten", styles), Spacer(1, 3 * mm)]

    machines = api_client.load_machines()
    if not machines:
        block.append(_empty_note(styles))
        return block

    rows = [[m["id"], m["name"], m["machine_type"], m["hall"], m["manufacturer"], m["year_built"]] for m in machines]
    headers = ["ID", "Name", "Typ", "Halle", "Hersteller", "Baujahr"]
    widths = [12, 34, 32, 26, 34, 22]
    block.append(_data_table(headers, rows, widths, styles))
    return block


def section_measures() -> list:
    styles = _styles()
    block = [_section_header("Wartungsma\u00dfnahmen", styles), Spacer(1, 3 * mm)]

    measures = api_client.load_measures()
    if not measures:
        block.append(_empty_note(styles))
        return block

    rows = [[m["id"], m["machine_name"], m["description"], format_date(m["start_date"])] for m in measures]
    headers = ["ID", "Maschine", "Beschreibung", "Startdatum"]
    widths = [12, 34, 92, 32]
    block.append(_data_table(headers, rows, widths, styles))
    return block


# ---------------------------------------------------------------------------
# Oeffentliche API der Seite: Optionen -> fertiges PDF (Bytes)
# ---------------------------------------------------------------------------

SECTION_BUILDERS = {
    "kpi_overview": ("KPI-\u00dcbersicht", lambda opt: section_kpi_overview()),
    "ticket_breakdown": ("Ticket-Verteilung", lambda opt: section_ticket_breakdown()),
    "ticket_trend": ("Ticket-Verlauf", lambda opt: section_ticket_trend(opt.get("trend_interval", "week"))),
    "top_machines": ("Top-Maschinen nach Fehlern", lambda opt: section_top_machines(opt.get("top_machines_n", 5))),
    "production_kpis": ("Production-KPIs", lambda opt: section_production_kpis()),
    "ticket_list": ("Ticket-Liste", lambda opt: section_ticket_list(opt.get("ticket_list_limit", 50))),
    "ticket_clusters": ("Ticket-Clustering", lambda opt: section_ticket_clusters(opt.get("n_clusters", 6))),
    "machines": ("Maschinen-Stammdaten", lambda opt: section_machines()),
    "measures": ("Wartungsma\u00dfnahmen", lambda opt: section_measures()),
}


def generate_pdf(selected_sections: list[str], options: dict[str, Any] | None = None) -> bytes:
    """Baut den Analysebericht als PDF und gibt die Roh-Bytes zurueck.

    `selected_sections` ist eine Liste von Keys aus SECTION_BUILDERS, in der
    gewuenschten Reihenfolge - so entscheidet der Nutzer im Frontend, was
    genau im Export landet (siehe app_pages/export.py).
    """
    options = options or {}
    styles = _styles()

    cover = Table(
        [[Paragraph("Machine Report App", styles["title"])],
         [Paragraph("Analysebericht", styles["subtitle"])]],
        colWidths=[PAGE_WIDTH_MM * mm],
    )
    cover.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), _hx(PRIMARY)),
        ("TOPPADDING", (0, 0), (-1, 0), 18),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 18),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))

    story: list = [
        cover,
        Spacer(1, 4 * mm),
        Paragraph(f"Erstellt am {datetime.now().strftime('%d.%m.%Y um %H:%M')} Uhr", styles["caption"]),
        Spacer(1, 6 * mm),
    ]

    for key in selected_sections:
        if key not in SECTION_BUILDERS:
            continue
        _, builder = SECTION_BUILDERS[key]
        story.extend(builder(options))
        story.append(Spacer(1, 6 * mm))

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        topMargin=18 * mm, bottomMargin=16 * mm, leftMargin=20 * mm, rightMargin=20 * mm,
        title="Machine Report App - Analysebericht",
    )
    doc.build(story)
    return buffer.getvalue()
