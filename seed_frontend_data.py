from app.database import SessionLocal, engine
from app import models, enums, crud
from datetime import date

def seed():
    db = SessionLocal()
    
    # Clean slate for ID 1
    existing = crud.get_scenario(db, 1)
    if existing:
        print("Deleting existing Scenario 1...")
        crud.delete_scenario(db, 1)
    
    print("Creating Demo Scenario...")
    scenario = models.Scenario(id=1, name="Cockpit Demo", start_date=date(2024, 1, 1))
    db.add(scenario)
    db.commit()
    
    owner = models.Owner(scenario_id=1, name="User")
    db.add(owner)
    db.commit()
    
    # 1. Main Bank Account
    bank = models.Account(scenario_id=1, name="Main Bank", account_type=enums.AccountType.CASH, starting_balance=5000)
    bank.owners.append(owner)
    db.add(bank)
    db.commit()
    
    # 2. Mortgage
    mortgage = models.Account(
        scenario_id=1, name="Home Loan", account_type=enums.AccountType.MORTGAGE, 
        starting_balance=-350000, 
        interest_rate=4.5,
        payment_from_account_id=bank.id,
        original_loan_amount=350000,
        amortisation_period_years=25
    )
    mortgage.owners.append(owner)
    db.add(mortgage)
    
    # 3. Income
    inc = models.IncomeSource(
        owner_id=owner.id, account_id=bank.id, name="Tech Salary", 
        net_value=450000, # £4,500
        cadence=enums.Cadence.MONTHLY, 
        start_date=date(2024, 1, 1)
    )
    db.add(inc)
    
    # 4. Living Cost
    cost = models.Cost(
        scenario_id=1, account_id=bank.id, name="Living Expenses",
        value=200000, # £2,000
        cadence=enums.Cadence.MONTHLY,
        start_date=date(2024, 1, 1),
        is_recurring=True
    )
    db.add(cost)
    
    db.commit()
    print("✅ Seed Complete! Scenario ID 1 is ready.")
    db.close()

if __name__ == "__main__":
    seed()
