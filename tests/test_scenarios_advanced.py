import pytest
from app import schemas, models, enums, crud
from datetime import date

def test_duplicate_scenario_comprehensive(client, db_session):
    # Use the fixture 'db_session' instead of manual get_db()
    db = db_session

    # 1. Setup Complex Scenario
    scenario = models.Scenario(name="Original", start_date=date(2024, 1, 1))
    db.add(scenario)
    db.commit()

    owner = models.Owner(name="O1", scenario_id=scenario.id)
    db.add(owner)
    db.commit()

    acc1 = models.Account(scenario_id=scenario.id, name="A1", account_type=enums.AccountType.CASH, starting_balance=1000)
    acc1.owners.append(owner)
    db.add(acc1)
    db.commit() # Get IDs

    acc2 = models.Account(scenario_id=scenario.id, name="A2", account_type=enums.AccountType.CASH, starting_balance=0, payment_from_account_id=acc1.id)
    db.add(acc2)
    db.commit()

    inc = models.IncomeSource(
        owner_id=owner.id, account_id=acc1.id, name="Job", net_value=100,
        cadence=enums.Cadence.MONTHLY, start_date=date(2024,1,1)
    )
    db.add(inc)

    cost = models.Cost(
        scenario_id=scenario.id, account_id=acc1.id, name="Food", value=10,
        cadence=enums.Cadence.MONTHLY, start_date=date(2024,1,1), is_recurring=True
    )
    db.add(cost)

    rule = models.AutomationRule(
        scenario_id=scenario.id, name="Rule", rule_type=enums.RuleType.SWEEP,
        source_account_id=acc1.id, target_account_id=acc2.id, trigger_value=500
    )
    db.add(rule)

    limit = models.TaxLimit(
        scenario_id=scenario.id, name="Limit", amount=1000, wrappers=[], start_date=date(2024,1,1)
    )
    db.add(limit)

    db.commit()

    # 2. Duplicate
    dup_scenario = crud.duplicate_scenario(db, scenario.id)
    assert dup_scenario is not None
    assert dup_scenario.id != scenario.id
    assert dup_scenario.name == "Copy of Original"

    # 3. Verify Links
    # Accounts
    assert len(dup_scenario.accounts) == 2
    dup_a1 = next(a for a in dup_scenario.accounts if a.name == "A1")
    dup_a2 = next(a for a in dup_scenario.accounts if a.name == "A2")

    assert dup_a1.id != acc1.id
    assert dup_a2.id != acc2.id

    # Check self-referencing foreign keys (payment_from_account_id)
    assert dup_a2.payment_from_account_id == dup_a1.id

    # Owners
    assert len(dup_scenario.owners) == 1
    dup_o1 = dup_scenario.owners[0]
    assert dup_o1.id != owner.id

    # Income
    assert len(dup_o1.income_sources) == 1
    dup_inc = dup_o1.income_sources[0]
    assert dup_inc.account_id == dup_a1.id

    # Rules
    assert len(dup_scenario.automation_rules) == 1
    dup_rule = dup_scenario.automation_rules[0]
    assert dup_rule.source_account_id == dup_a1.id
    assert dup_rule.target_account_id == dup_a2.id

    # Costs
    assert len(dup_scenario.costs) == 1
    dup_cost = dup_scenario.costs[0]
    assert dup_cost.account_id == dup_a1.id

    # Limits
    assert len(dup_scenario.tax_limits) == 1

def test_import_scenario_data(client, db_session):
    db = db_session

    # 1. Create Target Scenario
    scenario = models.Scenario(name="Target", start_date=date(2024, 1, 1))
    db.add(scenario)
    db.commit()

    # 2. Prepare Data
    import_data = {
        "name": "Imported Scenario",
        "description": "New Desc",
        "start_date": "2025-01-01",
        "owners": [
            {"id": 101, "name": "New Owner"}
        ],
        "accounts": [
            {"id": 201, "name": "New Acc", "account_type": "Cash", "starting_balance": 5000, "owners": [{"id": 101}]}
        ],
        "income_sources": [],
    }

    # Update data structure to match crud expectation
    import_data["owners"][0]["income_sources"] = [
        {
            "name": "Salary", "net_value": 3000, "cadence": "monthly",
            "start_date": "2025-01-01", "account_id": 201
        }
    ]

    # 3. Import
    updated_scenario = crud.import_scenario_data(db, scenario.id, import_data)

    assert updated_scenario.name == "Imported Scenario"
    assert updated_scenario.start_date == date(2025, 1, 1)

    assert len(updated_scenario.owners) == 1
    assert updated_scenario.owners[0].name == "New Owner"

    assert len(updated_scenario.accounts) == 1
    assert updated_scenario.accounts[0].name == "New Acc"

    # Check Income
    assert len(updated_scenario.owners[0].income_sources) == 1
    inc = updated_scenario.owners[0].income_sources[0]
    assert inc.name == "Salary"
    assert inc.account_id == updated_scenario.accounts[0].id
