from flows.fetch_machine_events import FetchMachineEvents
from models.database_tables import Machine


def _machine_id(seeded_session, name: str) -> int:
    return seeded_session.query(Machine).filter_by(machine_name=name).one().machine_id


def test_returns_events_for_one_machine_only(seeded_session):
    m1_id = _machine_id(seeded_session, "Trockner-01")
    rows = FetchMachineEvents().run(seeded_session, m1_id)
    assert len(rows) == 2  # error + maintenance events seeded for Trockner-01


def test_other_machine_not_included(seeded_session):
    m1_id = _machine_id(seeded_session, "Trockner-01")
    rows = FetchMachineEvents().run(seeded_session, m1_id)
    assert all(row["status"] in ("error", "maintenance") for row in rows)


def test_start_filter_excludes_earlier_events(seeded_session):
    m1_id = _machine_id(seeded_session, "Trockner-01")
    rows = FetchMachineEvents().run(seeded_session, m1_id, start="2026-06-02 00:00:00")
    assert len(rows) == 1
    assert rows[0]["status"] == "maintenance"


def test_error_description_joined_in(seeded_session):
    m1_id = _machine_id(seeded_session, "Trockner-01")
    rows = FetchMachineEvents().run(seeded_session, m1_id)
    error_row = next(row for row in rows if row["status"] == "error")
    assert error_row["error_description"] == "Ueberhitzung"
