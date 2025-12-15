from .utils import create_test_scenario, create_test_owner, create_test_account

def test_financial_event_crud(client, test_db):
    scenario = create_test_scenario(client, "Financial Event Test Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Event Test Owner", scenario_id)
    owner_id = owner["id"]
    account = create_test_account(client, scenario_id, [owner_id])
    account_id = account["id"]

    event_data = {
        "name": "Annual Bonus",
        "value": 500000,
        "event_date": "2025-03-15",
        "scenario_id": scenario_id,
        "from_account_id": account_id, 
        "event_type": "income_expense"
    }
    create_res = client.post("/api/financial_events/", json=event_data)
    assert create_res.status_code == 200, create_res.text
    created_event = create_res.json()
    event_id = created_event["id"]

    assert created_event["value"] == 500000

    delete_res = client.delete(f"/api/financial_events/{event_id}")
    assert delete_res.status_code == 200
