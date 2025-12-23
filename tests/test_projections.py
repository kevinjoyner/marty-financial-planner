from datetime import date
from .utils import create_test_scenario, create_test_owner

def test_run_projection(client, test_db):
    scenario = create_test_scenario(client, "Projection Test Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Test Owner", scenario_id)
    owner_id = owner["id"]
    
    account_res = client.post("/api/accounts/", json={
        "name": "Checking", "account_type": "Cash", "starting_balance": 100000,
        "interest_rate": 0.0, "scenario_id": scenario_id, "owner_ids": [owner_id]
    })
    account_id = account_res.json()["id"]
    
    client.post("/api/income_sources/", json={
        "name": "Salary", "net_value": 50000, "cadence": "monthly",
        "start_date": "2024-01-01", "owner_id": owner_id, "account_id": account_id
    })
    
    res = client.post(f"/api/projections/{scenario_id}/project", json={"simulation_months": 12, "overrides": []})
    assert res.status_code == 200
    data = res.json()
    assert len(data["data_points"]) > 0

def test_run_projection_with_mortgage(client, test_db):
    scenario = create_test_scenario(client, "Mortgage Test Scenario")
    scenario_id = scenario["id"]
    owner = create_test_owner(client, "Mortgage Test Owner", scenario_id)
    owner_id = owner["id"]
    
    checking_res = client.post("/api/accounts/", json={
        "name": "Checking", "account_type": "Cash", "starting_balance": 500000,
        "interest_rate": 0.0, "scenario_id": scenario_id, "owner_ids": [owner_id]
    })
    checking_id = checking_res.json()["id"]
    
    mortgage_res = client.post("/api/accounts/", json={
        "name": "Home Loan", "account_type": "Mortgage",
        "starting_balance": -30000000, "interest_rate": 3.5,
        "original_loan_amount": 30000000, "amortisation_period_years": 30,
        "payment_from_account_id": checking_id, "scenario_id": scenario_id, "owner_ids": [owner_id]
    })
    
    client.post("/api/income_sources/", json={
        "name": "Salary", "net_value": 400000, "cadence": "monthly",
        "start_date": "2024-01-01", "owner_id": owner_id, "account_id": checking_id
    })
    
    res = client.post(f"/api/projections/{scenario_id}/project", json={"simulation_months": 12})
    assert res.status_code == 200
    data = res.json()
    assert "mortgage_stats" in data
