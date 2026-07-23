def test_error_rate_endpoint(client):
    r = client.get("/kpi/error-rate")
    assert r.status_code == 200
    assert len(r.json()) > 0


def test_availability_endpoint(client):
    r = client.get("/kpi/availability")
    assert r.status_code == 200


def test_mttr_mtbf_endpoint(client):
    r = client.get("/kpi/mttr-mtbf")
    assert r.status_code == 200
