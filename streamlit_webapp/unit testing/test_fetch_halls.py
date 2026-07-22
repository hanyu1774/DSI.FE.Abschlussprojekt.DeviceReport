from flows.fetch_halls import FetchHalls


def test_returns_all_halls(seeded_session):
    rows = FetchHalls().run(seeded_session)
    names = [row["name"] for row in rows]
    assert names == ["Halle A", "Halle B"]


def test_ordered_by_name(seeded_session):
    rows = FetchHalls().run(seeded_session)
    names = [row["name"] for row in rows]
    assert names == sorted(names)
