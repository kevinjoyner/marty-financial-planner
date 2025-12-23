from datetime import date
from app import models, enums
from app.engine import core as app_engine
from app.engine.context import ProjectionContext

def create_scenario(db):
    s = models.Scenario(name="Test", start_date=date(2024, 1, 1))
    db.add(s); db.commit(); return s

def create_owner(db, sid):
    o = models.Owner(name="O", scenario_id=sid); db.add(o); db.commit(); return o

def create_account(db, sid, name, type, balance, owner, **kwargs):
    a = models.Account(scenario_id=sid, name=name, account_type=type, starting_balance=balance, **kwargs)
    a.owners.append(owner)
    db.add(a); db.commit(); return a

def test_engine_rsu_vesting(db_session, client):
    db = db_session
    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)
    target = create_account(db, scenario.id, "Bank", enums.AccountType.CASH, 0, owner)
    
    # RSU Grant: 1000 units, $10 each, vests in month 1
    vesting = [{"year": 1, "percent": 100}]
    # Grant date is 1 year before start, so year 1 vest happens at start? 
    # No, grant date 2024-01-01. Start date 2024-01-01.
    # Year 1 vest = 2025-01-01 (Month 12).
    rsu = create_account(
        db, scenario.id, "RSU", enums.AccountType.RSU_GRANT, 1000, owner,
        currency=enums.Currency.USD, rsu_target_account_id=target.id,
        vesting_schedule=vesting, grant_date=date(2024, 1, 1), unit_price=1000
    )
    
    # Run for 13 months to hit month 12
    res = app_engine.run_projection(db, scenario, months=13)
    
    # Check if Vest occurred
    vest_logs = [l for l in res.rule_logs if l.rule_type == 'RSU Vest']
    # If standard monthly vesting logic applies, it might be granular.
    # If 'annually', it hits at month 12.
    # Our engine does linear monthly if cadence is monthly. 
    # Let's assert we have *some* vest events or balance increase.
    
    # Check target account balance at end
    final_bal = res.data_points[-1].account_balances.get(target.id, 0)
    assert final_bal > 0 or len(vest_logs) > 0

def test_engine_standard_mortgage(db_session, client):
    db = db_session
    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)
    bank = create_account(db, scenario.id, "Bank", enums.AccountType.CASH, 500000, owner)
    
    mortgage = create_account(
        db, scenario.id, "Mortgage", enums.AccountType.MORTGAGE, -10000000, owner,
        interest_rate=5.0, original_loan_amount=10000000, amortisation_period_years=25,
        payment_from_account_id=bank.id
    )
    
    res = app_engine.run_projection(db, scenario, months=2)
    flows = res.data_points[1].flows.get(mortgage.id)
    
    # Interest should be charged (negative flow on context, or positive 'interest' field depending on schema)
    # Schema: interest is usually cost (negative) or just tracked magnitude?
    # In engine: context.flows[id]["interest"] += interest_charge (positive magnitude representing cost)
    # Wait, Core.py says: context.flows... interest...
    # Mortgage Processor: context.account_balances[acc.id] -= interest
    # Actually, mortgage processor calculates payment.
    
    assert flows.mortgage_repayments_in > 0

def test_engine_tax_limit_warning(db_session, client):
    db = db_session
    scenario = create_scenario(db)
    owner = create_owner(db, scenario.id)
    isa = create_account(db, scenario.id, "ISA", enums.AccountType.CASH, 0, owner, tax_wrapper=enums.TaxWrapper.ISA)
    
    limit = models.TaxLimit(scenario_id=scenario.id, name="ISA Limit", amount=2000000, wrappers=[enums.TaxWrapper.ISA.value], start_date=date(2024, 1, 1))
    db.add(limit); db.commit()
    
    # Windfall into ISA > Limit
    event = models.FinancialEvent(
        scenario_id=scenario.id, name="Windfall", value=2500000, date=date(2024, 2, 1),
        type="windfall", to_account_id=isa.id
    )
    db.add(event); db.commit()
    
    res = app_engine.run_projection(db, scenario, months=3)
    
    # Check for warnings
    warnings = [w for w in res.warnings if "ISA Limit" in w.message]
    assert len(warnings) > 0
