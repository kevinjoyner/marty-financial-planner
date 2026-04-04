from .utils import create_test_scenario, create_test_owner, create_test_account, create_test_cost

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


def test_delete_account_cascades_cost(client, test_db):
    """Deleting an account should cascade-delete any costs attached to it."""
    scenario = create_test_scenario(client, "Cascade Cost Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Owner", scenario_id)
    account = create_test_account(client, scenario_id, [owner["id"]], "Account With Cost")
    account_id = account["id"]

    cost = create_test_cost(client, scenario_id, account_id)
    cost_id = cost["id"]

    # Sanity-check the cost exists
    assert client.get(f"/api/costs/{cost_id}").status_code == 200

    # Delete the account
    assert client.delete(f"/api/accounts/{account_id}").status_code == 200

    # Cost must be gone too
    assert client.get(f"/api/costs/{cost_id}").status_code == 404


def test_delete_account_nullifies_payment_from(client, test_db):
    """Deleting account A should NULL out payment_from_account_id on sibling accounts."""
    scenario = create_test_scenario(client, "Nullify Payment From Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Owner", scenario_id)
    owner_id = owner["id"]

    # Create the source account (will be deleted)
    source = create_test_account(client, scenario_id, [owner_id], "Source Account")
    source_id = source["id"]

    # Create a mortgage that pays from the source account
    mortgage_data = {
        "name": "Test Mortgage",
        "account_type": "Mortgage",
        "starting_balance": -20000000,
        "interest_rate": 3.5,
        "scenario_id": scenario_id,
        "owner_ids": [owner_id],
        "currency": "GBP",
        "payment_from_account_id": source_id,
    }
    mortgage_resp = client.post("/api/accounts/", json=mortgage_data)
    assert mortgage_resp.status_code == 200, mortgage_resp.text
    mortgage_id = mortgage_resp.json()["id"]

    # Sanity-check the link is set
    detail = client.get(f"/api/accounts/{mortgage_id}").json()
    assert detail["payment_from_account_id"] == source_id

    # Delete the source account
    assert client.delete(f"/api/accounts/{source_id}").status_code == 200

    # The mortgage's payment_from_account_id must now be NULL
    detail_after = client.get(f"/api/accounts/{mortgage_id}").json()
    assert detail_after["payment_from_account_id"] is None


def test_delete_account_cascades_transfer(client, test_db):
    """Deleting one side of a transfer should cascade-delete the transfer."""
    scenario = create_test_scenario(client, "Cascade Transfer Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Owner", scenario_id)
    owner_id = owner["id"]

    acc_a = create_test_account(client, scenario_id, [owner_id], "Account A")
    acc_b = create_test_account(client, scenario_id, [owner_id], "Account B")

    transfer_data = {
        "name": "Monthly Transfer",
        "value": 50000,
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "scenario_id": scenario_id,
        "from_account_id": acc_a["id"],
        "to_account_id": acc_b["id"],
        "currency": "GBP",
    }
    transfer_resp = client.post("/api/transfers/", json=transfer_data)
    assert transfer_resp.status_code == 200, transfer_resp.text
    transfer_id = transfer_resp.json()["id"]

    assert client.get(f"/api/transfers/{transfer_id}").status_code == 200

    # Delete account A (the from-side)
    assert client.delete(f"/api/accounts/{acc_a['id']}").status_code == 200

    # Transfer must be gone
    assert client.get(f"/api/transfers/{transfer_id}").status_code == 404

