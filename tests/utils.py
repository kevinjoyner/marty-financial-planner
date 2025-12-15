from fastapi.testclient import TestClient
from typing import Optional

def create_test_scenario(client: TestClient, name: str, description: str = "") -> dict:
    response = client.post("/api/scenarios/", json={
        "name": name, 
        "description": description,
        "start_date": "2024-01-01" 
    })
    assert response.status_code == 200, response.text
    return response.json()

def create_test_owner(client: TestClient, name: str, scenario_id: Optional[int] = None) -> dict:
    assert scenario_id is not None
    response = client.post("/api/owners/", json={"name": name, "scenario_id": scenario_id})
    assert response.status_code == 200
    return response.json()

def create_test_account(client: TestClient, scenario_id: int, owner_ids: list[int], name: str = "Test Account") -> dict:
    account_data = {
        "name": name,
        "account_type": "Cash",
        "starting_balance": 100000, 
        "interest_rate": 0.0,
        "scenario_id": scenario_id,
        "owner_ids": owner_ids,
        "currency": "GBP"
    }
    response = client.post("/api/accounts/", json=account_data)
    assert response.status_code == 200, response.text
    return response.json()

def create_test_income_source(client: TestClient, owner_id: int, account_id: int) -> dict:
    income_data = {
        "name": "Test Income",
        "net_value": 50000, 
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "owner_id": owner_id,
        "account_id": account_id,
        "currency": "GBP"
    }
    response = client.post("/api/income_sources/", json=income_data)
    assert response.status_code == 200
    return response.json()

def create_test_cost(client: TestClient, scenario_id: int, account_id: int) -> dict:
    cost_data = {
        "name": "Test Cost",
        "value": 20000, 
        "cadence": "monthly",
        "start_date": "2024-01-01",
        "is_recurring": True,
        "scenario_id": scenario_id,
        "account_id": account_id,
        "currency": "GBP"
    }
    response = client.post("/api/costs/", json=cost_data)
    assert response.status_code == 200
    return response.json()
