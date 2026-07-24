from flows.check_machine_exists import CheckMachineExists
from models.database_tables import Machine


def test_existing_machine_returns_true(seeded_session):
    machine_id = seeded_session.query(Machine).filter_by(machine_name="Trockner-01").one().machine_id
    assert CheckMachineExists().run(seeded_session, machine_id) is True


def test_unknown_machine_returns_false(seeded_session):
    assert CheckMachineExists().run(seeded_session, 999999) is False
