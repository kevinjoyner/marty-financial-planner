import asyncio
from app.database import SessionLocal
from app import models, enums
from datetime import date
from sqlalchemy import text

# --- CONFIGURATION ---
# VALUES IN PENCE (x100)
ISA_BALANCE = 45000 * 100
ISA_COST = 40000 * 100  # 12.5% Growth

RSU_BALANCE = 4000 * 100
RSU_COST = 3000 * 100   # 33% Growth

DEMO_SCENARIO = {
    "name": "The 'Marty' Tech Demo",
    "description": "Interactive demo for Alice (Tech Lead) & Bob (Freelancer).",
    "start_date": date(2024, 1, 1),
    "gbp_to_usd_rate": 1.28
}

async def seed():
    print("🌱 Seeding Rich Demo Data (Values in Pence)...")
    db = SessionLocal()
    try:
        # 1. CLEANUP: Robustly delete existing demo
        existing = db.query(models.Scenario).filter(models.Scenario.name == DEMO_SCENARIO["name"]).first()
        if existing:
            print(f"♻️  Found existing demo scenario (ID: {existing.id}). Performing surgical cleanup...")
            
            # A. Break Self-Referential Account Links (Mortgages/RSUs)
            # This prevents "Foreign Key" errors when deleting accounts that point to each other
            db.execute(text(f"UPDATE accounts SET payment_from_account_id = NULL, rsu_target_account_id = NULL WHERE scenario_id = {existing.id}"))
            
            # B. Delete Dependents Explicitly (Order Matters)
            db.query(models.AutomationRule).filter(models.AutomationRule.scenario_id == existing.id).delete()
            db.query(models.TaxLimit).filter(models.TaxLimit.scenario_id == existing.id).delete()
            db.query(models.FinancialEvent).filter(models.FinancialEvent.scenario_id == existing.id).delete()
            db.query(models.Cost).filter(models.Cost.scenario_id == existing.id).delete()
            db.query(models.Transfer).filter(models.Transfer.scenario_id == existing.id).delete()
            
            # Delete Income Sources (Need to find them via Owners)
            owners = db.query(models.Owner).filter(models.Owner.scenario_id == existing.id).all()
            for o in owners:
                db.query(models.IncomeSource).filter(models.IncomeSource.owner_id == o.id).delete()
            
            db.commit() # Commit intermediate cleanups

            # C. Delete Core Entities
            db.query(models.Account).filter(models.Account.scenario_id == existing.id).delete()
            db.query(models.Owner).filter(models.Owner.scenario_id == existing.id).delete()
            
            # D. Finally, Delete Scenario
            db.delete(existing)
            db.commit()
            print("   ...Cleanup complete.")

        # 2. Create Scenario
        scenario = models.Scenario(**DEMO_SCENARIO)
        db.add(scenario)
        db.commit()
        db.refresh(scenario)

        # 3. Create Owners
        alice = models.Owner(scenario_id=scenario.id, name="Alice", birth_date=date(1990, 6, 15), retirement_age=60)
        bob = models.Owner(scenario_id=scenario.id, name="Bob", birth_date=date(1992, 3, 10), retirement_age=65)
        db.add_all([alice, bob])
        db.commit() 
        
        # 4. Create Accounts (Values x100)
        # Joint Account (Cash)
        joint_acc = models.Account(
            scenario_id=scenario.id, 
            name="Joint Current Account", 
            account_type=enums.AccountType.CASH, 
            starting_balance=5400 * 100, 
            currency=enums.Currency.GBP,
            interest_rate=0.0
        )
        
        # Emergency Fund (Cash)
        marcus = models.Account(
            scenario_id=scenario.id, 
            name="Emergency Fund (Marcus)", 
            account_type=enums.AccountType.CASH, 
            starting_balance=25000 * 100, 
            interest_rate=4.5, 
            min_balance=10000 * 100, 
            currency=enums.Currency.GBP
        )
        
        # ISA (Investment)
        isa = models.Account(
            scenario_id=scenario.id, 
            name="Alice S&S ISA", 
            account_type=enums.AccountType.INVESTMENT, 
            tax_wrapper=enums.TaxWrapper.ISA, 
            starting_balance=ISA_BALANCE, 
            book_cost=ISA_COST, 
            interest_rate=7.0, 
            currency=enums.Currency.GBP
        )

        # Mortgage (Liability)
        mortgage = models.Account(
            scenario_id=scenario.id, 
            name="Home Mortgage", 
            account_type=enums.AccountType.MORTGAGE, 
            starting_balance=-340000 * 100, 
            original_loan_amount=380000 * 100, 
            mortgage_start_date=date(2020,1,1), 
            amortisation_period_years=25, 
            interest_rate=5.5, 
            fixed_interest_rate=2.1, 
            fixed_rate_period_years=5, 
            currency=enums.Currency.GBP
        )

        # RSU Grant (Special)
        rsu = models.Account(
            scenario_id=scenario.id,
            name="Tech Corp RSU Grant (2023)",
            account_type=enums.AccountType.RSU_GRANT,
            starting_balance=RSU_BALANCE, 
            book_cost=RSU_COST,
            currency=enums.Currency.USD,
            unit_price=145.0, 
            grant_date=date(2023, 1, 1),
            vesting_schedule=[
                {"year": 1, "percent": 25},
                {"year": 2, "percent": 25},
                {"year": 3, "percent": 25},
                {"year": 4, "percent": 25}
            ]
        )
        
        # Main Residence
        home = models.Account(
            scenario_id=scenario.id,
            name="Family Home (Shakespeare Rd)",
            account_type=enums.AccountType.MAIN_RESIDENCE,
            starting_balance=650000 * 100,
            interest_rate=3.0, # Capital Appreciation
            currency=enums.Currency.GBP
        )
        
        db.add_all([joint_acc, marcus, isa, mortgage, rsu, home])
        db.commit()

        # 5. LINK OWNERS TO ACCOUNTS
        joint_acc.owners.append(alice)
        joint_acc.owners.append(bob)
        marcus.owners.append(alice)
        marcus.owners.append(bob)
        isa.owners.append(alice)
        rsu.owners.append(alice)
        mortgage.owners.append(alice)
        mortgage.owners.append(bob)
        home.owners.append(alice)
        home.owners.append(bob)

        # Link Mortgage Payment & RSU Target
        mortgage.payment_from_account_id = joint_acc.id
        rsu.rsu_target_account_id = marcus.id

        db.commit()
        
        # 6. Income Sources (Values x100)
        salary = models.IncomeSource(
            owner_id=alice.id,
            account_id=joint_acc.id,
            name="Alice Salary (Tech Lead)", 
            net_value=5500 * 100, 
            cadence=enums.Cadence.MONTHLY, 
            is_pre_tax=False, 
            start_date=date(2024,1,1)
        )
        
        freelance = models.IncomeSource(
            owner_id=bob.id,
            account_id=joint_acc.id,
            name="Bob Freelance", 
            net_value=3200 * 100, 
            cadence=enums.Cadence.MONTHLY, 
            start_date=date(2024,1,1)
        )
        
        db.add_all([salary, freelance])
        
        # 7. Costs (Values x100)
        living = models.Cost(
            scenario_id=scenario.id,
            account_id=joint_acc.id,
            name="Living Expenses", 
            value=1800 * 100, 
            cadence=enums.Cadence.MONTHLY, 
            start_date=date(2024,1,1)
        )

        netflix = models.Cost(
            scenario_id=scenario.id,
            account_id=joint_acc.id,
            name="Netflix & Subs", 
            value=45 * 100, 
            cadence=enums.Cadence.MONTHLY, 
            start_date=date(2024,1,1)
        )
        
        db.add_all([living, netflix])
        db.commit()

        # 8. Financial Events
        kitchen = models.FinancialEvent(
            scenario_id=scenario.id, 
            name="New Kitchen", 
            value=15000 * 100, 
            event_date=date(2025, 6, 1), 
            event_type=enums.FinancialEventType.INCOME_EXPENSE, 
            from_account_id=marcus.id, 
            show_on_chart=True
        )
        
        db.add(kitchen)
        
        # 9. Tax Limits
        isa_limit = models.TaxLimit(
            scenario_id=scenario.id,
            name="ISA Allowance",
            amount=20000 * 100,
            wrappers=["ISA", "Lifetime ISA"],
            start_date=date(2024, 4, 6),
            frequency="Annually"
        )
        
        pension_limit = models.TaxLimit(
            scenario_id=scenario.id,
            name="Pension Annual Allowance",
            amount=60000 * 100,
            wrappers=["Pension"],
            start_date=date(2024, 4, 6),
            frequency="Annually"
        )
        
        db.add_all([isa_limit, pension_limit])

        # 10. Automation Rules
        sweep_rule = models.AutomationRule(
            scenario_id=scenario.id,
            name="Sweep to Savings",
            rule_type=enums.RuleType.SWEEP,
            source_account_id=joint_acc.id,
            target_account_id=marcus.id,
            trigger_value=6000 * 100,
            priority=10,
            cadence=enums.Cadence.MONTHLY,
            start_date=date(2024, 1, 1)
        )
        
        db.add(sweep_rule)
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
