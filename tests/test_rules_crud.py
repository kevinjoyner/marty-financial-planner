import pytest
from app import schemas, models, enums, crud
from datetime import date

def test_rules_crud(client, db_session):
    # Use fixture
    db = db_session

    # Setup
    scenario = models.Scenario(name="Rule Test", start_date=date(2024, 1, 1))
    db.add(scenario)
    db.commit()

    acc1 = models.Account(scenario_id=scenario.id, name="A1", account_type=enums.AccountType.CASH, starting_balance=1000)
    acc2 = models.Account(scenario_id=scenario.id, name="A2", account_type=enums.AccountType.CASH, starting_balance=0)
    db.add(acc1)
    db.add(acc2)
    db.commit()

    # 1. Create Rule via Client (uses dependency override -> test.db)
    rule_data = {
        "scenario_id": scenario.id,
        "name": "Test Rule",
        "priority": 1,
        "rule_type": "sweep",
        "source_account_id": acc1.id,
        "target_account_id": acc2.id,
        "trigger_value": 500,
        "cadence": "monthly",
        "start_date": "2024-01-01"
    }

    res = client.post("/api/automation_rules", json=rule_data)
    assert res.status_code == 200, res.text
    rule_id = res.json()["id"]

    # 2. Get Rule
    res = client.get(f"/api/automation_rules/{rule_id}")
    assert res.status_code == 200

    # 3. Update Rule
    update_data = {"name": "Updated Rule", "trigger_value": 600}
    res = client.put(f"/api/automation_rules/{rule_id}", json=update_data)
    assert res.status_code == 200
    assert res.json()["name"] == "Updated Rule"
    assert res.json()["trigger_value"] == 600.0

    # 4. Reorder Rules
    rule2_data = rule_data.copy()
    rule2_data["name"] = "Rule 2"
    rule2_data["priority"] = 2
    res = client.post("/api/automation_rules", json=rule2_data)
    rule2_id = res.json()["id"]

    # Reorder: Rule 2 (id2) first, then Rule 1 (id1)
    res = client.put("/api/automation_rules/reorder", json=[rule2_id, rule_id])
    assert res.status_code == 200

    # Verify
    res1 = client.get(f"/api/automation_rules/{rule_id}")
    res2 = client.get(f"/api/automation_rules/{rule2_id}")

    assert res2.json()["priority"] == 1
    assert res1.json()["priority"] == 2

    # 5. Delete Rule
    res = client.delete(f"/api/automation_rules/{rule_id}")
    assert res.status_code == 200

    res = client.get(f"/api/automation_rules/{rule_id}")
    assert res.status_code == 404
