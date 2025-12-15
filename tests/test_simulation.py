import pytest
from app import models, enums, schemas
from datetime import date

def test_simulation_overrides(client, db_session):
    db = db_session
    scenario = models.Scenario(name="Sim Test", start_date=date(2024, 1, 1))
    db.add(scenario)
    db.commit()
    
    owner = models.Owner(name="O1", scenario_id=scenario.id)
    db.add(owner)
    
    acc = models.Account(scenario_id=scenario.id, name="Cash", account_type=enums.AccountType.CASH, starting_balance=0)
    acc.owners.append(owner)
    db.add(acc)
    db.commit()
    
    # Income
    inc = models.IncomeSource(
        owner_id=owner.id, account_id=acc.id, name="Salary", 
        net_value=500000, cadence=enums.Cadence.MONTHLY, start_date=date(2024, 1, 1)
    )
    db.add(inc)
    db.commit()
    
    # 1. Run Baseline
    payload_base = {"simulation_months": 3, "overrides": []}
    res = client.post(f"/api/projections/{scenario.id}/project", json=payload_base)
    assert res.status_code == 200, f"Error: {res.text}"
    baseline = res.json()
    
    assert len(baseline["data_points"]) == 4 
    
    final_balance_base = baseline["data_points"][-1]["balance"]
    # Ensure baseline is calculated
    assert final_balance_base > 0
    
    # 2. Run Simulation (Double Income)
    payload_sim = {
        "simulation_months": 3,
        "overrides": [
            {
                "type": "income", "id": inc.id, "field": "net_value", "value": 1000000 
            }
        ]
    }
    res = client.post(f"/api/projections/{scenario.id}/project", json=payload_sim)
    assert res.status_code == 200
    simulation = res.json()
    
    final_balance_sim = simulation["data_points"][-1]["balance"]
    
    # Logic check: More income = Higher balance
    assert final_balance_sim > final_balance_base
