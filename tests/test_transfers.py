from datetime import date
from .utils import create_test_scenario, create_test_owner, create_test_account

def test_transfer_crud(client, test_db):
    scenario = create_test_scenario(client, "Transfer Test Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Transfer Test Owner", scenario_id)
    owner_id = owner["id"]
    
    from_account = create_test_account(client, scenario_id, [owner_id], name="From Account")
    from_account_id = from_account["id"]
    to_account = create_test_account(client, scenario_id, [owner_id], name="To Account")
    to_account_id = to_account["id"]
    
    transfer_data = {
        "name": "Monthly Savings",
        "value": 50000,
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "scenario_id": scenario_id,
        "from_account_id": from_account_id,
        "to_account_id": to_account_id,
        # Removed 'notes'
    }
    create_res = client.post("/api/transfers/", json=transfer_data)
    assert create_res.status_code == 200
    transfer_id = create_res.json()["id"]
    
    # Read
    get_res = client.get(f"/api/transfers/{transfer_id}")
    assert get_res.status_code == 200
    assert get_res.json()["name"] == "Monthly Savings"
    
    # Update
    update_data = {"name": "Updated Savings", "value": 60000}
    put_res = client.put(f"/api/transfers/{transfer_id}", json=update_data)
    assert put_res.status_code == 200
    assert put_res.json()["value"] == 60000
    
    # Delete
    del_res = client.delete(f"/api/transfers/{transfer_id}")
    assert del_res.status_code == 200
