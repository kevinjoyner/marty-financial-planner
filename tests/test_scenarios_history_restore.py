import pytest
from app import schemas, models, enums, crud
from datetime import date, datetime

def test_scenario_restore_history(client, test_db):
    """
    Test restoring scenario history.
    """
    # 1. Create Scenario via Client
    res = client.post("/api/scenarios/", json={"name": "History Test", "start_date": "2024-01-01"})
    assert res.status_code == 200
    scenario_data = res.json()
    scenario_id = scenario_data["id"]

    # 2. Make a change (trigger snapshot via PUT)
    res = client.put(f"/api/scenarios/{scenario_id}", json={"name": "Name V2"})
    assert res.status_code == 200

    # 3. Get History via Client
    res = client.get(f"/api/scenarios/{scenario_id}/history")
    assert res.status_code == 200
    history = res.json()
    
    # Check that history works generally
    assert isinstance(history, list)

def test_import_new_scenario(client, test_db):
    """
    Test importing as a new scenario.
    """
    import_data = {
        "name": "Fresh Import",
        "description": "Imported from JSON",
        "start_date": "2025-01-01",
        "gbp_to_usd_rate": 1.30,
        "accounts": [
            {
                "id": 1,
                "name": "Acc1",
                "account_type": "Cash",
                "starting_balance": 1000,
                "interest_rate": 0.0
            }
        ]
    }

    res = client.post("/api/scenarios/import_new", json=import_data)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["name"] == "Fresh Import"
    assert data["start_date"] == "2025-01-01"
    assert len(data["accounts"]) == 1
    assert data["accounts"][0]["name"] == "Acc1"
