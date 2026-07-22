from flows.fetch_machine_types import FetchMachineTypes


def test_returns_all_machine_types(seeded_session):
    rows = FetchMachineTypes().run(seeded_session)
    names = {row["name"] for row in rows}
    assert names == {"Trockner", "Kuehltunnel"}
