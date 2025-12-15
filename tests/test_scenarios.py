def test_create_and_read_scenario(client, test_db):
    # Create a scenario
    scenario_res = client.post(
        "/api/scenarios/",
        json={
            "name": "Baseline", 
            "description": "My current financial situation",
            "start_date": "2024-01-01"
        },
    )
    assert scenario_res.status_code == 200, scenario_res.text
    scenario_data = scenario_res.json()
    assert scenario_data["name"] == "Baseline"
    scenario_id = scenario_data["id"]

    # Create an owner linked to the scenario
    owner_res = client.post(
        "/api/owners/", json={"name": "Test Owner", "scenario_id": scenario_id}
    )
    assert owner_res.status_code == 200
    owner_id = owner_res.json()["id"]

    # Create an account linked to the owner
    account_data = {
        "name": "Primary Checking",
        "account_type": "Cash",
        "starting_balance": 150075, # 1500.75 in pence
        "interest_rate": 0.0,
        "scenario_id": scenario_id,
        "owner_ids": [owner_id],
    }
    account_res = client.post("/api/accounts/", json=account_data)
    assert account_res.status_code == 200
    account_id = account_res.json()["id"]

    # Create an income source
    income_data = {
        "name": "Consulting Gig",
        "net_value": 120000,
        "cadence": "monthly",
        "start_date": "2024-06-01",
        "owner_id": owner_id,
        "account_id": account_id,
    }
    income_res = client.post("/api/income_sources/", json=income_data)
    assert income_res.status_code == 200

    # Create a cost
    cost_data = {
        "name": "Groceries",
        "value": 50000,
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "is_recurring": True,
        "scenario_id": scenario_id,
        "account_id": account_id,
    }
    cost_res = client.post("/api/costs/", json=cost_data)
    assert cost_res.status_code == 200
    
    # Read the scenario back
    response = client.get(f"/api/scenarios/{scenario_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Baseline"
    assert len(data["owners"]) == 1
    assert len(data["accounts"]) == 1
    assert len(data["costs"]) == 1

    # Update the scenario
    update_data = {"name": "Baseline Scenario", "description": "An updated description"}
    response = client.put(f"/api/scenarios/{scenario_id}", json=update_data)
    assert response.status_code == 200
    assert response.json()["name"] == "Baseline Scenario"


def test_delete_scenario(client, test_db):
    # Create a scenario to delete (must include start_date)
    scenario_data = {"name": "To Be Deleted", "start_date": "2024-01-01"}
    response = client.post("/api/scenarios/", json=scenario_data)
    assert response.status_code == 200
    scenario_id = response.json()["id"]

    # Delete the scenario
    response = client.delete(f"/api/scenarios/{scenario_id}")
    assert response.status_code == 200

    # Verify it's gone
    response = client.get(f"/api/scenarios/{scenario_id}")
    assert response.status_code == 404
