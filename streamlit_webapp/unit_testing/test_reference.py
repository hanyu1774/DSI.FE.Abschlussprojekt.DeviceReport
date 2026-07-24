def test_list_halls_endpoint(client):
    r = client.get("/halls")
    assert r.status_code == 200
    assert {h["name"] for h in r.json()} == {"Halle A", "Halle B"}


def test_list_machines_endpoint(client):
    r = client.get("/machines")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_get_machine_endpoint_success(client):
    machine_id = client.get("/machines").json()[0]["id"]
    r = client.get(f"/machines/{machine_id}")
    assert r.status_code == 200


def test_get_machine_endpoint_404_for_unknown_id(client):
    r = client.get("/machines/999999")
    assert r.status_code == 404
    assert "detail" in r.json()


def test_machine_events_endpoint(client):
    machine_id = client.get("/machines").json()[0]["id"]
    r = client.get(f"/machines/{machine_id}/events")
    assert r.status_code == 200


def test_error_codes_endpoint(client):
    r = client.get("/error-codes")
    assert r.status_code == 200
    codes = {e["error_code"] for e in r.json()}
    assert "E101" in codes


def test_technicians_endpoint(client):
    r = client.get("/technicians")
    assert r.status_code == 200
    assert len(r.json()) == 2
