import pytest
from datetime import date
from app import models, enums, engine

def create_basic_scenario(session, owner_age=40):
    """Helper to set up a scenario with one person and various accounts"""
    scenario = models.Scenario(
        name="Decumulation Test",
        start_date=date(2025, 1, 1),
        gbp_to_usd_rate=1.25
    )
    session.add(scenario)
    session.flush()

    # Create Owner
    dob = date(2025 - owner_age, 1, 1)
    owner = models.Owner(name="Test User", birth_date=dob, retirement_age=65, scenario_id=scenario.id)
    session.add(owner)
    session.flush()

    # Create Accounts (Balances in Pence)
    # 1. Current Account (The one that will go into deficit)
    acc_current = models.Account(
        name="Current", 
        account_type=enums.AccountType.CASH, 
        starting_balance=0, # Empty
        min_balance=0,
        scenario_id=scenario.id
    )
    # 2. Savings (Cash Priority 1)
    acc_savings = models.Account(
        name="Savings", 
        account_type=enums.AccountType.CASH, 
        starting_balance=500000, # £5k
        scenario_id=scenario.id
    )
    # 3. GIA (Priority 2)
    acc_gia = models.Account(
        name="GIA", 
        account_type=enums.AccountType.INVESTMENT, 
        tax_wrapper=enums.TaxWrapper.GIA,
        starting_balance=500000, 
        scenario_id=scenario.id
    )
    # 4. ISA (Priority 3)
    acc_isa = models.Account(
        name="ISA", 
        account_type=enums.AccountType.INVESTMENT, 
        tax_wrapper=enums.TaxWrapper.ISA,
        starting_balance=500000, 
        scenario_id=scenario.id
    )
    # 5. Pension (Priority 4 - Locked/Unlocked)
    acc_pension = models.Account(
        name="Pension", 
        account_type=enums.AccountType.INVESTMENT, 
        tax_wrapper=enums.TaxWrapper.PENSION,
        starting_balance=500000, 
        scenario_id=scenario.id
    )
    
    session.add_all([acc_current, acc_savings, acc_gia, acc_isa, acc_pension])
    session.flush()
    
    # Link Owner to Pension (Critical for age check)
    acc_pension.owners.append(owner)
    session.flush()

    return scenario, owner, acc_current, acc_savings, acc_gia, acc_isa, acc_pension

def test_decumulation_inactive_without_strategy(db_session):
    """Ensure decumulation does NOT run if no strategy is defined"""
    scenario, owner, current, savings, _, _, _ = create_basic_scenario(db_session)
    
    # Add a massive cost to cause deficit
    cost = models.Cost(
        name="Living", 
        value=200000, # £2k
        cadence=enums.Cadence.MONTHLY, 
        start_date=scenario.start_date, 
        account_id=current.id, 
        scenario_id=scenario.id
    )
    db_session.add(cost)
    db_session.commit() # Commit to ensure ID availability for engine

    # Run for 1 month
    proj = engine.run_projection(db_session, scenario, 1)
    
    # Check Result: Current account should be negative (£2000)
    # Savings should be untouched (£5000)
    current_end = proj.data_points[1].account_balances[current.id]
    savings_end = proj.data_points[1].account_balances[savings.id]
    
    assert current_end == -2000.0
    assert savings_end == 5000.0

def test_decumulation_priority_waterfall(db_session):
    """Ensure assets are drained in order: Cash -> GIA -> ISA"""
    scenario, _, current, savings, gia, isa, _ = create_basic_scenario(db_session)
    
    # Enable Strategy
    strategy = models.DecumulationStrategy(
        name="Auto", 
        strategy_type="automated", 
        scenario_id=scenario.id
    )
    db_session.add(strategy)
    
    # Cost: £12k (Consumes all £5k Savings + £5k GIA + £2k ISA)
    cost = models.Cost(
        name="Heavy Living", 
        value=1200000, 
        cadence=enums.Cadence.MONTHLY, 
        start_date=scenario.start_date, 
        account_id=current.id, 
        scenario_id=scenario.id
    )
    db_session.add(cost)
    db_session.commit()

    # Run 1 month
    proj = engine.run_projection(db_session, scenario, 1)
    
    # Balances at end of month 1 (in Pounds)
    # Current: Should be 0 (Filled by transfers)
    # Savings: 0 (Drained first)
    # GIA: 0 (Drained second)
    # ISA: 3000 (Started 5000, took 2000)
    
    dp = proj.data_points[1]
    assert dp.account_balances[current.id] == 0
    assert dp.account_balances[savings.id] == 0
    assert dp.account_balances[gia.id] == 0
    assert dp.account_balances[isa.id] == 3000.0

def test_pension_lock_age_40(db_session):
    """Ensure Pension is NOT touched if owner is 40"""
    scenario, owner, current, savings, gia, isa, pension = create_basic_scenario(db_session, owner_age=40)
    
    # Enable Strategy
    db_session.add(models.DecumulationStrategy(name="Auto", scenario_id=scenario.id))
    
    # Cost: £20k (Exhausts all liquid £15k, needs £5k more)
    # Should drain Savings(5k), GIA(5k), ISA(5k) -> Deficit remains 5k
    cost = models.Cost(name="Huge Cost", value=2000000, cadence=enums.Cadence.MONTHLY, start_date=scenario.start_date, account_id=current.id, scenario_id=scenario.id)
    db_session.add(cost)
    db_session.commit()

    proj = engine.run_projection(db_session, scenario, 1)
    dp = proj.data_points[1]
    
    # Pension should be untouched (5000)
    assert dp.account_balances[pension.id] == 5000.0
    # Current should be -5000 (Deficit remained)
    assert dp.account_balances[current.id] == -5000.0

def test_pension_access_age_60(db_session):
    """Ensure Pension IS touched if owner is 60"""
    scenario, owner, current, savings, gia, isa, pension = create_basic_scenario(db_session, owner_age=60)
    
    # Enable Strategy
    db_session.add(models.DecumulationStrategy(name="Auto", scenario_id=scenario.id))
    
    # Cost: £20k (Exhausts all liquid £15k, needs £5k from Pension)
    cost = models.Cost(name="Huge Cost", value=2000000, cadence=enums.Cadence.MONTHLY, start_date=scenario.start_date, account_id=current.id, scenario_id=scenario.id)
    db_session.add(cost)
    db_session.commit()

    proj = engine.run_projection(db_session, scenario, 1)
    dp = proj.data_points[1]
    
    # Pension should be drained (Started 5000, took 5000 -> 0)
    assert dp.account_balances[pension.id] == 0
    # Current should be 0 (Fully covered)
    assert dp.account_balances[current.id] == 0
