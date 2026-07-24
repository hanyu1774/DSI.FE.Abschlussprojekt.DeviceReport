import pandas as pd

from flows.enrich_tickets import EnrichTickets
from models.ticket_status import TicketStatus


def _tickets_df() -> pd.DataFrame:
    return pd.DataFrame([
        {  # open: only created_at set
            "id": 1, "technician_first_name": None, "technician_last_name": None,
            "created_at": pd.Timestamp("2026-06-01"), "assigned_at": pd.NaT,
            "resolved_at": pd.NaT, "closed_at": pd.NaT,
        },
        {  # in progress: assigned but not resolved
            "id": 2, "technician_first_name": "Ada", "technician_last_name": "Lovelace",
            "created_at": pd.Timestamp("2026-06-01"), "assigned_at": pd.Timestamp("2026-06-01 12:00:00"),
            "resolved_at": pd.NaT, "closed_at": pd.NaT,
        },
        {  # closed: everything set
            "id": 3, "technician_first_name": "Grace", "technician_last_name": "Hopper",
            "created_at": pd.Timestamp("2026-06-01 00:00:00"), "assigned_at": pd.Timestamp("2026-06-01 01:00:00"),
            "resolved_at": pd.Timestamp("2026-06-01 05:00:00"), "closed_at": pd.Timestamp("2026-06-01 06:00:00"),
        },
    ])


def test_status_derived_correctly_for_each_lifecycle_stage():
    result = EnrichTickets().run(_tickets_df()).set_index("id")
    assert result.loc[1, "status"] == TicketStatus.OPEN
    assert result.loc[2, "status"] == TicketStatus.IN_PROGRESS
    assert result.loc[3, "status"] == TicketStatus.CLOSED


def test_technician_full_name_merged():
    result = EnrichTickets().run(_tickets_df()).set_index("id")
    # NaN, not None, at this stage - pandas' .replace("", None) idiom
    # produces NaN, and this Flow doesn't clean that up. That's fine: every
    # consumer routes through DataHelpers.to_json_records before building a
    # Pydantic model, and that's where NaN -> None actually happens.
    assert pd.isna(result.loc[1, "technician"])
    assert result.loc[2, "technician"] == "Ada Lovelace"


def test_resolution_hours_computed_only_when_resolved():
    result = EnrichTickets().run(_tickets_df()).set_index("id")
    assert pd.isna(result.loc[1, "resolution_hours"])
    assert result.loc[3, "resolution_hours"] == 5.0
