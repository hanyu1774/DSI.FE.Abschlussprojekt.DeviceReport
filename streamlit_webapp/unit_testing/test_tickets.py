def test_list_tickets_endpoint(client):
    r = client.get("/tickets")
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_list_tickets_endpoint_with_priority_filter(client):
    r = client.get("/tickets?priority=critical")
    assert r.status_code == 200
    assert len(r.json()) == 1


def test_summary_endpoint(client):
    r = client.get("/tickets/summary")
    assert r.status_code == 200
    assert r.json()["total"] == 3


def test_trend_endpoint(client):
    r = client.get("/tickets/trend?interval=day")
    assert r.status_code == 200


def test_response_times_endpoint(client):
    r = client.get("/tickets/response-times")
    assert r.status_code == 200


def test_clusters_endpoint_invalid_query_param_rejected(client):
    r = client.get("/tickets/clusters?n_clusters=1")  # below ge=2
    assert r.status_code == 422
