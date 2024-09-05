def test_healthcheck(client):
    resp = client.get("/healthcheck")
    assert resp.status_code == 200
