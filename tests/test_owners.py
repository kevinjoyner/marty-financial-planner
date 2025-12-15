from fastapi.testclient import TestClient


def create_scenario_helper(client: TestClient) -> int:
    """Helper function to create a scenario and return its ID."""
    response = client.post(
        "/api/scenarios",
        json={
            "name": "Test Scenario for Owners", 
            "description": "A test scenario",
            "start_date": "2024-01-01"
        },
    )
    assert response.status_code == 200
    return response.json()["id"]


def test_create_owner(client: TestClient, test_db):
    scenario_id = create_scenario_helper(client)
    response = client.post(
        "/api/owners",
        json={"name": "John Doe", "scenario_id": scenario_id},
    )
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "John Doe"
    assert "id" in data


def test_read_owner(client: TestClient, test_db):
    scenario_id = create_scenario_helper(client)
    create_response = client.post(
        "/api/owners",
        json={"name": "Jane Doe", "scenario_id": scenario_id},
    )
    owner_id = create_response.json()["id"]

    response = client.get(f"/api/owners/{owner_id}")
    data = response.json()
    assert response.status_code == 200
    assert data["name"] == "Jane Doe"
    assert data["id"] == owner_id


def test_delete_owner(client: TestClient, test_db):
    scenario_id = create_scenario_helper(client)
    create_response = client.post(
        "/api/owners",
        json={"name": "Delete Me", "scenario_id": scenario_id},
    )
    owner_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/owners/{owner_id}")
    assert delete_response.status_code == 200

    # Verify the owner is gone
    get_response = client.get(f"/api/owners/{owner_id}")
    assert get_response.status_code == 404
