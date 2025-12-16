import asyncio
from app.database import SessionLocal
from app import models
from datetime import date

# --- CONFIGURATION ---
# We set book_cost LOWER than balance to ensure the dashboard shows green growth numbers.
ISA_BALANCE = 45000
ISA_COST = 40000  # 12.5% Growth

RSU_BALANCE = 4000
RSU_COST = 3000   # 33% Growth

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
        # 1. CLEANUP: Delete existing demo if present (prevents "Zombie" partial states)
        existing = db.query(models.Scenario).filter(models.Scenario.name == DEMO_SCENARIO["name"]).first()
        if existing:
            print("♻️  Found existing demo scenario. Deleting to ensure clean seed...")
            db.delete(existing)
            db.commit()

        # 2. Create Scenario
        scenario = models.Scenario(**DEMO_SCENARIO)
        db.add(scenario)
        db.commit()
        db.refresh(scenario)

        # 3. Create Owners
        alice = models.Owner(scenario_id=scenario.id, name="Alice", birth_date=date(1990, 6, 15), retirement_age=60)
        bob = models.Owner(scenario_id=scenario.id, name="Bob", birth_date=date(1992, 3, 10), retirement_age=65)
        db.add_all([alice, bob])
        db.commit() # Commit to get IDs
        
        # 4. Create Accounts
        # Joint Account (Cash)
        joint_acc = models.Account(
            scenario_id=scenario.id, 
            name="Joint Current Account", 
            account_type="Cash", 
            starting_balance=5400, 
            currency="GBP",
            interest_rate=0.0
        )
        
        # Emergency Fund (Cash)
        marcus = models.Account(
            scenario_id=scenario.id, 
            name="Emergency Fund (Marcus)", 
            account_type="Cash", 
            starting_balance=25000, 
            interest_rate=4.5, 
            min_balance=10000, 
            currency="GBP"
        )
        
        # ISA (Investment)
        isa = models.Account(
            scenario_id=scenario.id, 
            name="Alice S&S ISA", 
            account_type="Investment", 
            tax_wrapper="ISA", 
            starting_balance=ISA_BALANCE, 
            book_cost=ISA_COST, 
            interest_rate=7.0, 
            currency="GBP"
        )

        # Mortgage (Liability)
        mortgage = models.Account(
            scenario_id=scenario.id, 
            name="Home Mortgage", 
            account_type="Mortgage", 
            starting_balance=-340000, 
            original_loan_amount=380000, 
            mortgage_start_date=date(2020,1,1), 
            amortisation_period_years=25, 
            interest_rate=5.5, 
            fixed_interest_rate=2.1, 
            fixed_rate_period_years=5, 
            currency="GBP"
        )

        # RSU Grant (Special)
        rsu = models.Account(
            scenario_id=scenario.id,
            name="Tech Corp RSU Grant (2023)",
            account_type="RSU Grant",
            starting_balance=RSU_BALANCE,
            book_cost=RSU_COST,
            currency="USD",
            unit_price=145.0,
            grant_date=date(2023, 1, 1),
            vesting_schedule=[
                {"year": 1, "percent": 25},
                {"year": 2, "percent": 25},
                {"year": 3, "percent": 25},
                {"year": 4, "percent": 25}
            ]
        )
        
        db.add_all([joint_acc, marcus, isa, mortgage, rsu])
        db.commit()

        # 5. LINK OWNERS TO ACCOUNTS (Critical for UI visibility)
        # Joint Account -> Alice & Bob
        joint_acc.owners.append(alice)
        joint_acc.owners.append(bob)
        
        # Others -> Alice
        marcus.owners.append(alice)
        marcus.owners.append(bob) # Assuming shared
        isa.owners.append(alice)
        rsu.owners.append(alice)
        mortgage.owners.append(alice)
        mortgage.owners.append(bob)

        # Link Mortgage Payment
        mortgage.payment_from_account_id = joint_acc.id
        rsu.rsu_target_account_id = marcus.id

        db.commit()
        
        # 6. Income Sources
        salary = models.IncomeSource(
            owner_id=alice.id,
            account_id=joint_acc.id,
            name="Alice Salary (Tech Lead)", 
            net_value=5500,  # Monthly Net (approx for 85k gross)
            cadence="monthly", 
            is_pre_tax=False, 
            start_date=date(2024,1,1)
        )
        
        freelance = models.IncomeSource(
            owner_id=bob.id,
            account_id=joint_acc.id,
            name="Bob Freelance", 
            net_value=3200, 
            cadence="monthly", 
            start_date=date(2024,1,1)
        )
        
        db.add_all([salary, freelance])
        
        # 7. Costs
        living = models.Cost(
            scenario_id=scenario.id,
            account_id=joint_acc.id,
            name="Living Expenses", 
            value=1800, 
            cadence="monthly", 
            start_date=date(2024,1,1)
        )

        netflix = models.Cost(
            scenario_id=scenario.id,
            account_id=joint_acc.id,
            name="Netflix & Subs", 
            value=45, 
            cadence="monthly", 
            start_date=date(2024,1,1)
        )
        
        db.add_all([living, netflix])
        db.commit()

        # 8. Financial Events (The jagged lines)
        kitchen = models.FinancialEvent(
            scenario_id=scenario.id, 
            name="New Kitchen", 
            value=15000, 
            event_date=date(2025, 6, 1), 
            event_type="income_expense", 
            from_account_id=marcus.id, 
            show_on_chart=True
        )
        
        db.add(kitchen)
        db.commit()

        print("✅ Rich Demo Data Seeded Successfully!")

    except Exception as e:
        print(f"❌ Error seeding data: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(seed())
