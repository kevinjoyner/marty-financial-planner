import pytest
from datetime import date
from app import schemas, models, enums, engine as app_engine

def create_scenario(db):
    scenario = models.Scenario(
        name="Engine Test Scenario",
        description="Complex scenario for engine testing",
        start_date=date(2024, 1, 1),
        gbp_to_usd_rate=1.25
    )
    db.add(scenario)
    db.commit()
    db.refresh(scenario)
    return scenario

def create_owner(db, scenario_id, name="Test Owner"):
    owner = models.Owner(name=name, scenario_id=scenario_id)
    db.add(owner)
    db.commit()
    db.refresh(owner)
    return owner

def create_account(db, scenario_id, name, account_type, balance, owner, currency=enums.Currency.GBP, **kwargs):
    account = models.Account(
        scenario_id=scenario_id,
        name=name,
        account_type=account_type,
        starting_balance=balance,
        currency=currency,
        interest_rate=kwargs.get("interest_rate", 0.0),
        tax_wrapper=kwargs.get("tax_wrapper", enums.TaxWrapper.NONE),
        rsu_target_account_id=kwargs.get("rsu_target_account_id"),
        vesting_schedule=kwargs.get("vesting_schedule"),
        grant_date=kwargs.get("grant_date"),
        unit_price=kwargs.get("unit_price"),
        original_loan_amount=kwargs.get("original_loan_amount"),
        amortisation_period_years=kwargs.get("amortisation_period_years"),
        mortgage_start_date=kwargs.get("mortgage_start_date"),
        payment_from_account_id=kwargs.get("payment_from_account_id"),
        fixed_rate_period_years=kwargs.get("fixed_rate_period_years"),
        fixed_interest_rate=kwargs.get("fixed_interest_rate"),
        book_cost=kwargs.get("book_cost", balance)
    )
    account.owners.append(owner)
    db.add(account)
    db.commit()
    db.refresh(account)
    return account

def test_engine_rsu_vesting(db_session, client):
    # Use fixture
    db = db_session

    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)

    # Target account for vesting
    target_acc = create_account(db, scenario.id, "Main Bank", enums.AccountType.CASH, 0, owner)

    # RSU Grant Account
    vesting_schedule = [{"year": 1, "percent": 100}]
    rsu_acc = create_account(
        db, scenario.id, "RSU Grant", enums.AccountType.RSU_GRANT,
        balance=1000, # 1000 units
        owner=owner,
        currency=enums.Currency.USD,
        rsu_target_account_id=target_acc.id,
        vesting_schedule=vesting_schedule,
        grant_date=date(2024, 1, 1),
        unit_price=1000, # $10.00
        interest_rate=0.0
    )

    # Run projection
    projection = app_engine.run_projection(db, scenario, months=13)

    # Check rule logs
    vest_logs = [log for log in projection.rule_logs if log.rule_type == "RSU Vest"]
    assert len(vest_logs) > 0

    total_vested = sum(log.amount for log in vest_logs)
    assert total_vested > 0

    final_point = projection.data_points[-1]
    target_balance = final_point.account_balances[target_acc.id]
    assert target_balance > 0

def test_engine_mortgage_smart_payment(db_session, client):
    db = db_session

    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)

    source_acc = create_account(db, scenario.id, "Savings", enums.AccountType.CASH, 1000000, owner)
    mortgage_acc = create_account(db, scenario.id, "Mortgage", enums.AccountType.MORTGAGE, -500000, owner)

    rule = models.AutomationRule(
        scenario_id=scenario.id,
        name="Mortgage Overpay",
        priority=1,
        rule_type=enums.RuleType.MORTGAGE_SMART,
        source_account_id=source_acc.id,
        target_account_id=mortgage_acc.id,
        # Updated to Pence: 100,000 = £1,000 buffer
        trigger_value=100000.0,
        transfer_value=10.0,
        cadence=enums.Cadence.ANNUALLY,
        start_date=date(2024, 1, 1)
    )
    db.add(rule)
    db.commit()

    projection = app_engine.run_projection(db, scenario, months=13)

    final_point = projection.data_points[-1]
    mortgage_balance = final_point.account_balances[mortgage_acc.id]

    assert mortgage_balance > -5000.0
    assert mortgage_balance < 0

    smart_logs = [log for log in projection.rule_logs if "Smart Smooth" in log.reason]
    assert len(smart_logs) > 0

def test_engine_sweep_rule(db_session, client):
    db = db_session

    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)

    # 200,000 Pence = £2,000
    source_acc = create_account(db, scenario.id, "Checking", enums.AccountType.CASH, 200000, owner)
    target_acc = create_account(db, scenario.id, "Savings", enums.AccountType.CASH, 0, owner)

    rule = models.AutomationRule(
        scenario_id=scenario.id,
        name="Sweep Excess",
        priority=1,
        rule_type=enums.RuleType.SWEEP,
        source_account_id=source_acc.id,
        target_account_id=target_acc.id,
        # Updated to Pence: 100,000 = £1,000 trigger
        trigger_value=100000.0,
        cadence=enums.Cadence.MONTHLY,
        start_date=date(2024, 1, 1)
    )
    db.add(rule)
    db.commit()

    projection = app_engine.run_projection(db, scenario, months=2)

    final_point = projection.data_points[-1]
    source_balance = final_point.account_balances[source_acc.id]
    target_balance = final_point.account_balances[target_acc.id]

    # Expect balances in Pounds (Float)
    assert source_balance == 1000.0
    assert target_balance == 1000.0

def test_engine_cgt_on_transfer(db_session, client):
    db = db_session

    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)

    gia_acc = create_account(
        db, scenario.id, "GIA", enums.AccountType.INVESTMENT,
        balance=200000,
        owner=owner,
        book_cost=100000
    )

    bank_acc = create_account(db, scenario.id, "Bank", enums.AccountType.CASH, 0, owner)

    # Increase Value to trigger Gain
    gia_acc.starting_balance = 20000000
    gia_acc.book_cost = 1000000
    db.commit()

    transfer = models.Transfer(
        scenario_id=scenario.id,
        from_account_id=gia_acc.id,
        to_account_id=bank_acc.id,
        value=5000000,
        cadence=enums.Cadence.ONCE,
        start_date=date(2024, 2, 1),
        name="Big Withdrawal"
    )
    db.add(transfer)
    db.commit()

    projection = app_engine.run_projection(db, scenario, months=3)
    flows_feb = projection.data_points[2].flows[gia_acc.id]
    assert flows_feb.cgt > 0

def test_engine_tax_limit_warning(db_session, client):
    db = db_session

    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)

    isa_acc = create_account(
        db, scenario.id, "ISA", enums.AccountType.CASH, 0, owner,
        tax_wrapper=enums.TaxWrapper.ISA
    )

    limit = models.TaxLimit(
        scenario_id=scenario.id,
        name="ISA Limit",
        amount=2000000,
        wrappers=[enums.TaxWrapper.ISA.value],
        start_date=date(2024, 1, 1),
        end_date=date(2025, 4, 5)
    )
    db.add(limit)
    db.commit()

    income = models.FinancialEvent(
        scenario_id=scenario.id,
        name="Windfall",
        value=2500000,
        event_date=date(2024, 2, 1),
        event_type=enums.FinancialEventType.INCOME_EXPENSE,
        from_account_id=isa_acc.id
    )
    db.add(income)
    db.commit()

    projection = app_engine.run_projection(db, scenario, months=3)
    warnings = [w for w in projection.warnings if "exceeds allowance" in w.message]
    assert len(warnings) > 0

def test_engine_standard_mortgage(db_session, client):
    db = db_session

    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)

    bank_acc = create_account(db, scenario.id, "Bank", enums.AccountType.CASH, 500000, owner)

    mortgage_acc = create_account(
        db, scenario.id, "Mortgage", enums.AccountType.MORTGAGE, -10000000, owner,
        interest_rate=5.0,
        original_loan_amount=10000000,
        amortisation_period_years=25,
        payment_from_account_id=bank_acc.id
    )

    projection = app_engine.run_projection(db, scenario, months=2)

    flows = projection.data_points[1].flows[mortgage_acc.id]
    repayment = flows.mortgage_repayments_in
    interest = flows.interest

    assert repayment > 0
    assert interest < 0
    assert 580 < repayment < 590
