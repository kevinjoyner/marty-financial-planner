import asyncio
from app.database import SessionLocal, engine
from app import models, enums
from sqlalchemy import text
from datetime import date

# Define the Rich Demo Scenario directly in Python
DEMO_SCENARIO = {
    "name": "The 'Marty' Tech Demo",
    "description": "Interactive demo for Alice (Tech Lead) & Bob (Freelancer).",
    "start_date": date(2024, 1, 1),
    "gbp_to_usd_rate": 1.28
}

async def seed():
    print("🌱 Seeding Rich Demo Data...")
    db = SessionLocal()
    try:
        # Check if scenario exists
        existing = db.query(models.Scenario).filter(models.Scenario.name == DEMO_SCENARIO["name"]).first()
        if existing:
            print("✅ Demo scenario already exists. Skipping seed.")
            return

        # 1. Create Scenario
        scenario = models.Scenario(**DEMO_SCENARIO)
        db.add(scenario)
        db.commit()
        db.refresh(scenario)

        # 2. Create Owners
        alice = models.Owner(scenario_id=scenario.id, name="Alice", birth_date=date(1990, 6, 15), retirement_age=60)
        bob = models.Owner(scenario_id=scenario.id, name="Bob", birth_date=date(1992, 3, 10), retirement_age=65)
        db.add_all([alice, bob])
        db.commit()
        
        # 3. Create Accounts
        # Current Account
        joint_acc = models.Account(scenario_id=scenario.id, name="Joint Current Account", account_type="Cash", starting_balance=5400, currency="GBP")
        # Emergency Fund
        marcus = models.Account(scenario_id=scenario.id, name="Emergency Fund (Marcus)", account_type="Cash", starting_balance=25000, interest_rate=4.5, min_balance=10000, currency="GBP")
        
        # ISA - FIX: Added book_cost=40000 to prevent NaN calculation ((45k-40k)/40k = 12.5% return)
        isa = models.Account(scenario_id=scenario.id, name="Alice S&S ISA", account_type="Investment", tax_wrapper="ISA", starting_balance=45000, book_cost=40000, interest_rate=7.0, currency="GBP")
        
        # Mortgage
        mortgage = models.Account(scenario_id=scenario.id, name="Home Mortgage", account_type="Mortgage", starting_balance=-340000, original_loan_amount=380000, mortgage_start_date=date(2020,1,1), amortisation_period_years=25, interest_rate=5.5, fixed_interest_rate=2.1, fixed_rate_period_years=5, currency="GBP")
        
        db.add_all([joint_acc, marcus, isa, mortgage])
        db.commit()
        
        # 4. Income & Costs
        salary = models.IncomeSource(scenario_id=scenario.id, account_id=joint_acc.id, owner_id=alice.id, name="Alice Salary", net_value=8500000, cadence="monthly", is_pre_tax=True, start_date=date(2024,1,1))
        freelance = models.IncomeSource(scenario_id=scenario.id, account_id=joint_acc.id, owner_id=bob.id, name="Bob Freelance", net_value=320000, cadence="monthly", start_date=date(2024,1,1))
        
        expenses = models.Cost(scenario_id=scenario.id, account_id=joint_acc.id, name="Living Expenses", value=180000, cadence="monthly", start_date=date(2024,1,1))
        
        db.add_all([salary, freelance, expenses])
        db.commit()

        # 5. Financial Events
        kitchen = models.FinancialEvent(scenario_id=scenario.id, name="New Kitchen", value=1500000, event_date=date(2025, 6, 1), event_type="income_expense", from_account_id=marcus.id, show_on_chart=True)
        car = models.FinancialEvent(scenario_id=scenario.id, name="Car Purchase", value=800000, event_date=date(2026, 3, 1), event_type="income_expense", from_account_id=marcus.id, show_on_chart=True)

        db.add_all([kitchen, car])
        db.commit()

        # 6. Automation Rules
        sweep = models.AutomationRule(scenario_id=scenario.id, name="Sweep to Savings", rule_type="sweep", source_account_id=joint_acc.id, target_account_id=marcus.id, trigger_value=300000, priority=1, cadence="monthly")
        
        db.add(sweep)
        db.commit()

        print("✅ Rich Demo Data Seeded Successfully!")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed())
