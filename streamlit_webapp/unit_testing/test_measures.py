def test_list_measures_endpoint(client):
    r = client.get("/measures")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_create_measure_endpoint_success(client):
    machine_id = client.get("/machines").json()[1]["id"]
    r = client.post("/measures", json={
        "machine_id": machine_id, "description": "API-Test", "start_date": "2026-07-01",
    })
    assert r.status_code == 201
    assert r.json()["description"] == "API-Test"


def test_create_measure_endpoint_404_for_unknown_machine(client):
    r = client.post("/measures", json={
        "machine_id": 999999, "description": "x", "start_date": "2026-07-01",
    })
    assert r.status_code == 404


def test_create_measure_endpoint_422_for_invalid_payload(client):
    r = client.post("/measures", json={"machine_id": 1, "description": "", "start_date": "2026-07-01"})
    assert r.status_code == 422  # description has min_length=1
