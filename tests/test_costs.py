from datetime import date
from .utils import create_test_scenario, create_test_owner, create_test_account

def test_create_and_read_cost(client, test_db):
    scenario = create_test_scenario(client, "Cost Test Scenario")
    scenario_id = scenario["id"]
    
    cost_data = {
        "name": "Groceries",
        "value": 40000,
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "scenario_id": scenario_id,
        "inflation_rate": 0.03 # Fixed: was growth_rate
    }
    
    res = client.post("/api/costs/", json=cost_data)
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Groceries"
    assert data["value"] == 40000
