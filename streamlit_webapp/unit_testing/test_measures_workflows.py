import pytest

from flows.check_machine_exists import MachineNotFound
from models.database_tables import Machine
from models.schema_models import MeasureCreate
from workflows.measures_workflows import CreateMeasureWorkflow, ListMeasuresWorkflow


def test_list_measures_workflow(seeded_session):
    result = ListMeasuresWorkflow().run(seeded_session)
    assert len(result) == 1
    assert result[0].description == "Filterwechsel"


def test_create_measure_workflow_persists_and_returns_it(seeded_session):
    machine_id = seeded_session.query(Machine).filter_by(machine_name="Trockner-02").one().machine_id
    payload = MeasureCreate(machine_id=machine_id, description="Neue Wartung", start_date="2026-07-01")

    result = CreateMeasureWorkflow().run(seeded_session, payload)

    assert result.description == "Neue Wartung"
    assert result.machine_name == "Trockner-02"
    all_measures = ListMeasuresWorkflow().run(seeded_session)
    assert len(all_measures) == 2


def test_create_measure_workflow_raises_for_unknown_machine(seeded_session):
    payload = MeasureCreate(machine_id=999999, description="x", start_date="2026-07-01")
    with pytest.raises(MachineNotFound):
        CreateMeasureWorkflow().run(seeded_session, payload)
