import pytest

from flows.check_machine_exists import MachineNotFound
from models.database_tables import Machine
from workflows.reference_workflows import (
    GetMachineWorkflow,
    ListErrorCodesWorkflow,
    ListHallsWorkflow,
    ListMachineEventsWorkflow,
    ListMachinesWorkflow,
    ListMachineTypesWorkflow,
    ListTechniciansWorkflow,
)


def test_list_halls_workflow_maps_to_schema(seeded_session):
    result = ListHallsWorkflow().run(seeded_session)
    assert {h.name for h in result} == {"Halle A", "Halle B"}


def test_list_machine_types_workflow(seeded_session):
    result = ListMachineTypesWorkflow().run(seeded_session)
    assert len(result) == 2


def test_list_technicians_workflow(seeded_session):
    result = ListTechniciansWorkflow().run(seeded_session)
    assert len(result) == 2


def test_list_error_codes_workflow(seeded_session):
    result = ListErrorCodesWorkflow().run(seeded_session)
    assert any(e.error_code == "E101" for e in result)


def test_list_machines_workflow(seeded_session):
    result = ListMachinesWorkflow().run(seeded_session)
    assert len(result) == 3


def test_get_machine_workflow_returns_the_machine(seeded_session):
    machine_id = seeded_session.query(Machine).filter_by(machine_name="Trockner-01").one().machine_id
    result = GetMachineWorkflow().run(seeded_session, machine_id)
    assert result.name == "Trockner-01"


def test_get_machine_workflow_raises_domain_exception_for_unknown_id(seeded_session):
    with pytest.raises(MachineNotFound):
        GetMachineWorkflow().run(seeded_session, 999999)


def test_list_machine_events_workflow(seeded_session):
    machine_id = seeded_session.query(Machine).filter_by(machine_name="Trockner-01").one().machine_id
    result = ListMachineEventsWorkflow().run(seeded_session, machine_id)
    assert len(result) == 2
