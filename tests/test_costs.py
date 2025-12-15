from .utils import create_test_scenario, create_test_owner, create_test_account

def test_create_and_read_cost(client, test_db):
    scenario = create_test_scenario(client, "Cost Test Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Cost Test Owner", scenario_id)
    owner_id = owner["id"]
    account = create_test_account(client, scenario_id, [owner_id])
    account_id = account["id"]

    cost_data = {
        "name": "Monthly Rent",
        "value": 120000,
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "is_recurring": True,
        "scenario_id": scenario_id,
        "account_id": account_id,
    }
    response = client.post("/api/costs/", json=cost_data)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Monthly Rent"
    cost_id = data["id"]

    response = client.get(f"/api/costs/{cost_id}")
    assert response.status_code == 200
    
    response = client.delete(f"/api/costs/{cost_id}")
    assert response.status_code == 200
