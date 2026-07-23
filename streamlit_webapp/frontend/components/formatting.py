"""Kleine Formatierungs-Helfer fuer konsistente Anzeige von Zahlen/Dauern."""

from __future__ import annotations

from datetime import datetime


def format_hours(hours: float | None) -> str:
    """Formatiert eine Stundenangabe menschenlesbar (z. B. '2,3 Std.' oder '1 Tag 4 Std.')."""
    if hours is None:
        return "\u2013"
    if hours < 48:
        return f"{hours:.1f}".replace(".", ",") + " Std."
    days = int(hours // 24)
    rest_hours = round(hours - days * 24)
    return f"{days} Tage {rest_hours} Std."


def format_minutes(minutes: float | None) -> str:
    if minutes is None:
        return "\u2013"
    if minutes < 90:
        return f"{minutes:.0f} Min."
    return format_hours(minutes / 60)


def format_datetime(value: str | None) -> str:
    if not value:
        return "\u2013"
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return value
    return parsed.strftime("%d.%m.%Y %H:%M")


def format_date(value: str | None) -> str:
    if not value:
        return "\u2013"
    try:
        parsed = datetime.fromisoformat(value[:10])
    except ValueError:
        return value
    return parsed.strftime("%d.%m.%Y")


def format_percent(value: float | None, decimals: int = 1) -> str:
    if value is None:
        return "\u2013"
    return f"{value:.{decimals}f}\u00a0%".replace(".", ",")
