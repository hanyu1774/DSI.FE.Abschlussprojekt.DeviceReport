"""Ticket lifecycle vocabulary — status labels and priority ordering.

Pure data shared across multiple ticket Flows/Workflows, so per Plan #1
this lives here as a Model rather than as a module-level constant.
"""
from __future__ import annotations


class TicketStatus:
    OPEN = "Offen"
    IN_PROGRESS = "In Bearbeitung"
    RESOLVED = "Gel\u00f6st"
    CLOSED = "Geschlossen"

    PRIORITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
