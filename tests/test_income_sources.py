from datetime import date
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
        "net_value": 500000, # Fixed
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "owner_id": owner_id,
        "account_id": account_id
    }
    
    res = client.post("/api/income_sources/", json=income_data)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Salary"
    assert data["net_value"] == 500000
