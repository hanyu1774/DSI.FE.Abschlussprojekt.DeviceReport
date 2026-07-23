from workflows.kpi_workflows import AvailabilityWorkflow, ErrorRateWorkflow, MttrMtbfWorkflow


def test_error_rate_workflow_returns_kpi_models(seeded_engine):
    result = ErrorRateWorkflow().run(seeded_engine)
    assert len(result) > 0
    assert result[0].machine_name is not None


def test_availability_workflow_returns_kpi_models(seeded_engine):
    result = AvailabilityWorkflow().run(seeded_engine)
    assert all(0 <= kpi.availability_percent <= 100 for kpi in result)


def test_mttr_mtbf_workflow_returns_kpi_models(seeded_engine):
    result = MttrMtbfWorkflow().run(seeded_engine)
    assert len(result) > 0
