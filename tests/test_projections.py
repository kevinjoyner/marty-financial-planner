from app.utils import calculate_mortgage_payment
from .utils import create_test_scenario, create_test_owner

def test_run_projection(client, test_db):
    # Basic Projection
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
    client.post("/api/costs/", json={
        "name": "Rent", "value": 20000, "cadence": "monthly", 
        "start_date": "2024-01-01", "is_recurring": True, "scenario_id": scenario_id, "account_id": account_id
    })

    # FIX: Send empty dict as body to satisfy Pydantic
    response = client.post(f"/api/projections/{scenario_id}/project?months=3", json={})
    assert response.status_code == 200, response.text
    data = response.json()
    # 1000 + 500 - 200 = 1300 GBP -> 130000 Pence
    assert data["data_points"][0]["balance"] == 100000 
    assert data["data_points"][1]["balance"] == 130000

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

    # Capture the Mortgage Response to get the ID
    mortgage_res = client.post("/api/accounts/", json={
        "name": "Home Loan", "account_type": "Mortgage",
        "starting_balance": -30000000, "interest_rate": 3.5,
        "original_loan_amount": 30000000, "amortisation_period_years": 30,
        "payment_from_account_id": checking_id, "scenario_id": scenario_id, "owner_ids": [owner_id]
    })
    mortgage_id = mortgage_res.json()["id"]

    client.post("/api/income_sources/", json={
        "name": "Salary", "net_value": 400000, "cadence": "monthly", 
        "start_date": "2024-01-01", "owner_id": owner_id, "account_id": checking_id
    })

    response = client.post(f"/api/projections/{scenario_id}/project?months=2", json={})
    assert response.status_code == 200, response.text
    data = response.json()

    # Calculation verification
    principal_pence = 30000000 
    annual_rate = 3.5
    years = 30
    monthly_payment_pence = calculate_mortgage_payment(principal_pence, annual_rate, years)
    
    post_payment_principal = principal_pence - monthly_payment_pence
    interest_pence = post_payment_principal * (annual_rate / 100 / 12)
    
    expected_mortgage_balance_pence = -30000000 + monthly_payment_pence - interest_pence
    
    actual_mortgage_balance = data["data_points"][1]["account_balances"][str(mortgage_id)]
    
    assert abs(actual_mortgage_balance - expected_mortgage_balance_pence) < 10
