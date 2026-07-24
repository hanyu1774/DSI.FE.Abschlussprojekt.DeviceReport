from flows.fetch_machines import FetchMachines


def test_returns_all_machines_when_no_filter(seeded_session):
    rows = FetchMachines().run(seeded_session)
    assert len(rows) == 3


def test_filters_to_one_machine_by_id(seeded_session):
    from models.database_tables import Machine
    target_id = seeded_session.query(Machine).filter_by(machine_name="Trockner-01").one().machine_id

    rows = FetchMachines().run(seeded_session, machine_id=target_id)
    assert len(rows) == 1
    assert rows[0]["name"] == "Trockner-01"


def test_join_resolves_hall_and_type(seeded_session):
    rows = FetchMachines().run(seeded_session)
    by_name = {row["name"]: row for row in rows}
    assert by_name["Trockner-01"]["hall"] == "Halle A"
    assert by_name["Trockner-01"]["machine_type"] == "Trockner"
    assert by_name["Kuehltunnel-01"]["hall"] == "Halle B"


def test_unknown_machine_id_returns_empty(seeded_session):
    rows = FetchMachines().run(seeded_session, machine_id=999999)
    assert rows == []
