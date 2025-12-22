from .utils import create_test_scenario

# Note: 'client' is a pytest fixture automatically provided by conftest.py
# We do NOT instantiate TestClient(app) here.

def test_strategy_crud(client):
    # 1. Create Scenario
    scen_data = create_test_scenario(client, "Strategy Test Scenario")
    scen_id = scen_data["id"]
    
    # 2. Create Strategy
    payload = {
        "name": "Retirement Plan A",
        "strategy_type": "Standard",
        "enabled": True,
        "start_date": "2030-01-01"
    }
    response = client.post(f"/api/scenarios/{scen_id}/strategies/", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Retirement Plan A"
    strat_id = data["id"]
    
    # 3. Read
    response = client.get(f"/api/scenarios/{scen_id}/strategies/")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
    # 4. Update
    payload["name"] = "Plan B"
    response = client.put(f"/api/scenarios/{scen_id}/strategies/{strat_id}", json=payload)
    assert response.status_code == 200
    assert response.json()["name"] == "Plan B"
    
    # 5. Delete
    response = client.delete(f"/api/scenarios/{scen_id}/strategies/{strat_id}")
    assert response.status_code == 200
    
    # Verify Empty
    response = client.get(f"/api/scenarios/{scen_id}/strategies/")
    assert len(response.json()) == 0
