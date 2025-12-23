from starlette.testclient import TestClient

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/json"
    assert "message" in response.json()
