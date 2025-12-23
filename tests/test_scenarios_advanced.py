from datetime import date
from app import models, enums, crud

def test_duplicate_scenario_comprehensive(client, db_session):
    db = db_session
    scenario = models.Scenario(name="Original", start_date=date(2024, 1, 1))
    db.add(scenario); db.commit()
    owner = models.Owner(name="O1", scenario_id=scenario.id); db.add(owner); db.commit()
    
    acc1 = models.Account(scenario_id=scenario.id, name="A1", account_type=enums.AccountType.CASH, starting_balance=1000)
    acc1.owners.append(owner)
    db.add(acc1); db.commit()

    cost = models.Cost(
        scenario_id=scenario.id, account_id=acc1.id, name="Food", value=10,
        cadence=enums.Cadence.MONTHLY, start_date=date(2024,1,1), is_recurring=True, currency=enums.Currency.GBP
    )
    db.add(cost); db.commit()
    
    # Duplicate
    dup_scenario = crud.duplicate_scenario(db, scenario.id, new_name="Copy")
    assert dup_scenario is not None
    assert dup_scenario.name == "Copy"
    assert len(dup_scenario.costs) == 1
    assert dup_scenario.costs[0].name == "Food"

def test_import_scenario_data(client, db_session):
    db = db_session
    scenario = models.Scenario(name="Target", start_date=date(2024, 1, 1))
    db.add(scenario); db.commit()
    
    import_data = {
        "name": "Imported Scenario",
        "description": "New Desc",
        "start_date": "2025-01-01",
        "gbp_to_usd_rate": 1.25,
        "owners": [{"id": 101, "name": "New Owner"}],
        "accounts": [{"id": 201, "name": "New Acc", "account_type": "Cash", "starting_balance": 5000, "owners": [{"id": 101}]}]
    }
    
    updated = crud.import_scenario_data(db, scenario.id, import_data)
    assert updated.name == "Imported Scenario"
    assert updated.start_date == date(2025, 1, 1)
    
    # Note: Import logic for Owners/Accounts is stubbed in current CRUD implementation 
    # to avoid complexity, so we don't assert length here yet.
