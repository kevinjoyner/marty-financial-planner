from .utils import create_test_scenario, create_test_owner, create_test_account

def test_create_and_read_income_source(client, test_db):
    scenario = create_test_scenario(client, "Income Test Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Income Test Owner", scenario_id)
    owner_id = owner["id"]
    account = create_test_account(client, scenario_id, [owner_id])
    account_id = account["id"]

    income_data = {
        "name": "Salary",
        "net_value": 400000,
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "owner_id": owner_id,
        "account_id": account_id,
    }
    response = client.post("/api/income_sources", json=income_data)
    assert response.status_code == 200
    data = response.json()
    assert data["net_value"] == 400000
    id = data["id"]

    response = client.get(f"/api/income_sources/{id}")
    assert response.status_code == 200
    
    response = client.delete(f"/api/income_sources/{id}")
    assert response.status_code == 200
