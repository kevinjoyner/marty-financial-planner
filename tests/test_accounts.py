from .utils import create_test_scenario, create_test_owner

def test_create_and_read_account(client, test_db):
    scenario = create_test_scenario(client, "Account Test Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Test Owner", scenario_id)
    owner_id = owner["id"]

    # Create an account for the owner
    account_data = {
        "name": "Primary Checking",
        "account_type": "Cash",
        "starting_balance": 150075, # Pence
        "interest_rate": 0.0,
        "is_primary_account": True,
        "scenario_id": scenario_id,
        "owner_ids": [owner_id],
    }
    response = client.post("/api/accounts", json=account_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Primary Checking"
    assert data["starting_balance"] == 150075
    assert len(data["owners"]) == 1
    assert data["owners"][0]["id"] == owner_id
    account_id = data["id"]

    # Read the account back
    response = client.get(f"/api/accounts/{account_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Primary Checking"
    assert data["id"] == account_id


def test_update_and_delete_account(client, test_db):
    scenario = create_test_scenario(client, "Account Update Test Scenario")
    scenario_id = scenario["id"]
    owner1 = create_test_owner(client, "Update Test Owner 1", scenario_id)
    owner1_id = owner1["id"]
    owner2 = create_test_owner(client, "Update Test Owner 2", scenario_id)
    owner2_id = owner2["id"]

    account_data = {
        "name": "Account to Update",
        "account_type": "Cash",
        "starting_balance": 100000,
        "interest_rate": 1.5,
        "is_primary_account": False,
        "scenario_id": scenario_id,
        "owner_ids": [owner1_id],
    }
    create_response = client.post("/api/accounts", json=account_data)
    assert create_response.status_code == 200, create_response.text
    account_id = create_response.json()["id"]

    # Update the account's name and add a joint owner
    update_data = {
        "name": "Updated Joint Savings Account",
        "owner_ids": [owner1_id, owner2_id]
    }
    response = client.put(f"/api/accounts/{account_id}", json=update_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["name"] == "Updated Joint Savings Account"
    assert len(data["owners"]) == 2
    
    # Delete
    response = client.delete(f"/api/accounts/{account_id}")
    assert response.status_code == 200
    response = client.get(f"/api/accounts/{account_id}")
    assert response.status_code == 404
