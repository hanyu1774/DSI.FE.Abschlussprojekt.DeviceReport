from flows.fetch_measures import FetchMeasures
from flows.insert_measure import InsertMeasure
from models.database_tables import Machine


def test_insert_returns_new_id(seeded_session):
    machine_id = seeded_session.query(Machine).filter_by(machine_name="Trockner-02").one().machine_id

    new_id = InsertMeasure().run(seeded_session, machine_id, "Riemenwechsel", "2026-06-15")

    assert isinstance(new_id, int)


def test_inserted_row_is_persisted_and_fetchable(seeded_session):
    machine_id = seeded_session.query(Machine).filter_by(machine_name="Trockner-02").one().machine_id

    new_id = InsertMeasure().run(seeded_session, machine_id, "Riemenwechsel", "2026-06-15")

    rows = FetchMeasures().run(seeded_session, measure_id=new_id)
    assert len(rows) == 1
    assert rows[0]["description"] == "Riemenwechsel"
    assert rows[0]["machine_name"] == "Trockner-02"
    assert rows[0]["start_date"] == "2026-06-15"
