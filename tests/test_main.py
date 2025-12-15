from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root(client):
    response = client.get("/")
    assert response.status_code == 200
    # The root path now serves the Vue 3 index.html
    assert "text/html" in response.headers["content-type"]
    # Check for the app mount point, which is standard in Vue
    assert b'<div id="app"' in response.content or b'<title>Aura' in response.content
