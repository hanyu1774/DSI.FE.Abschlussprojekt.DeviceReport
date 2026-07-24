from flows.fetch_measures import FetchMeasures


def test_returns_all_measures(seeded_session):
    rows = FetchMeasures().run(seeded_session)
    assert len(rows) == 1
    assert rows[0]["machine_name"] == "Trockner-01"
    assert rows[0]["description"] == "Filterwechsel"


def test_filters_by_measure_id(seeded_session):
    all_rows = FetchMeasures().run(seeded_session)
    measure_id = all_rows[0]["id"]

    rows = FetchMeasures().run(seeded_session, measure_id=measure_id)
    assert len(rows) == 1
    assert rows[0]["id"] == measure_id
