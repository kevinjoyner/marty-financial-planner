from datetime import date
from .utils import create_test_scenario

def test_financial_event_crud(client, test_db):
    scenario = create_test_scenario(client, "Event Scenario")
    scenario_id = scenario["id"]
    
    event_data = {
        "name": "Bonus",
        "value": 100000,
        "date": "2024-12-25", # Fixed: was event_date
        "type": "windfall",
        "scenario_id": scenario_id
    }
    
    res = client.post("/api/financial_events/", json=event_data)
    assert res.status_code == 200
    assert res.json()["name"] == "Bonus"
