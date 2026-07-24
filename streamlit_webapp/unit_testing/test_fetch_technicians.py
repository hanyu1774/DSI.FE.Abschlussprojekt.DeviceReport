from flows.fetch_technicians import FetchTechnicians


def test_returns_all_technicians_ordered_by_last_name(seeded_session):
    rows = FetchTechnicians().run(seeded_session)
    last_names = [row["last_name"] for row in rows]
    assert last_names == ["Hopper", "Lovelace"]


def test_includes_shift(seeded_session):
    rows = FetchTechnicians().run(seeded_session)
    shifts = {row["last_name"]: row["shift"] for row in rows}
    assert shifts["Lovelace"] == "Frueh"
    assert shifts["Hopper"] == "Spaet"
