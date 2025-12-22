import sys
import json
from sqlalchemy.orm import Session
from app.database import SessionLocal, engine
from app import models, schemas
from app.crud import scenarios
from datetime import date

# The New Demo Scenario Data (Steady State)
DEMO_SCENARIO = {
  "name": "Marty Demo: The 'Steady State'",
  "description": "A fully-featured simulation starting post-relocation. Demonstrates RSUs, Bonus structures, Smart Mortgage Overpayments, and Automated Decumulation strategies.",
  "notes": "Scenario starts April 2026. Focus on wealth accumulation and tax efficiency.",
  "start_date": "2026-04-01",
  "gbp_to_usd_rate": 1.30,
  "owners": [
    {
      "name": "Alice",
      "notes": "Tech Lead",
      "birth_date": "1988-06-15",
      "retirement_age": 60,
      "income_sources": [
        {
          "name": "Alice Base Salary",
          "net_value": 750000,
          "cadence": "monthly",
          "is_pre_tax": True,
          "salary_sacrifice_value": 40000,
          "salary_sacrifice_account_id": 15,
          "taxable_benefit_value": 15000,
          "employer_pension_contribution": 25000,
          "start_date": "2026-04-01",
          "currency": "GBP"
        },
        {
          "name": "Quarterly Performance Bonus",
          "net_value": 1200000,
          "cadence": "quarterly",
          "is_pre_tax": True,
          "start_date": "2026-06-25",
          "currency": "GBP"
        }
      ]
    },
    {
      "name": "Bob",
      "notes": "Freelance Consultant",
      "birth_date": "1990-03-20",
      "retirement_age": 65,
      "income_sources": [
        {
          "name": "Consulting Fees",
          "net_value": 450000,
          "cadence": "monthly",
          "is_pre_tax": False,
          "start_date": "2026-04-01",
          "currency": "GBP"
        }
      ]
    }
  ],
  "accounts": [
    {
      "name": "Joint Current Account",
      "notes": "Main hub",
      "account_type": "Cash",
      "tax_wrapper": "None",
      "starting_balance": 850000,
      "min_balance": 500000,
      "interest_rate": 0,
      "currency": "GBP",
      "id": 10,
      "owners": [{"name": "Alice"}, {"name": "Bob"}]
    },
    {
      "name": "High Yield Savings",
      "notes": "Emergency fund",
      "account_type": "Cash",
      "tax_wrapper": "None",
      "starting_balance": 3500000,
      "min_balance": 0,
      "interest_rate": 4.0,
      "currency": "GBP",
      "payment_from_account_id": 10,
      "id": 11,
      "owners": [{"name": "Alice"}, {"name": "Bob"}]
    },
    {
      "name": "Family Home",
      "notes": "London Zone 2",
      "account_type": "Main Residence",
      "tax_wrapper": "None",
      "starting_balance": 125000000,
      "book_cost": 125000000,
      "min_balance": 0,
      "interest_rate": 3.0,
      "currency": "GBP",
      "id": 12,
      "owners": [{"name": "Alice"}, {"name": "Bob"}]
    },
    {
      "name": "Home Mortgage",
      "notes": "Fixed rate until 2028",
      "account_type": "Mortgage",
      "tax_wrapper": "None",
      "starting_balance": -65000000,
      "min_balance": 0,
      "interest_rate": 5.5,
      "fixed_interest_rate": 3.85,
      "fixed_rate_period_years": 2,
      "amortisation_period_years": 25,
      "mortgage_start_date": "2026-03-01",
      "currency": "GBP",
      "payment_from_account_id": 10,
      "id": 13,
      "owners": [{"name": "Alice"}, {"name": "Bob"}]
    },
    {
      "name": "Tech Corp RSUs",
      "notes": "Unvested Stock Grants",
      "account_type": "RSU Grant",
      "tax_wrapper": "None",
      "starting_balance": 2500,
      "min_balance": 0,
      "interest_rate": 8.0,
      "currency": "USD",
      "unit_price": 14500,
      "grant_date": "2025-11-01",
      "rsu_target_account_id": 20,
      "vesting_schedule": [
        {"year": 1, "percent": 40},
        {"year": 2, "percent": 30},
        {"year": 3, "percent": 20},
        {"year": 4, "percent": 10}
      ],
      "id": 14,
      "owners": [{"name": "Alice"}]
    },
    {
      "name": "Alice SIPP",
      "notes": "Pension Pot",
      "account_type": "Investment",
      "tax_wrapper": "Pension",
      "starting_balance": 18500000,
      "min_balance": 0,
      "interest_rate": 7.0,
      "currency": "GBP",
      "id": 15,
      "owners": [{"name": "Alice"}]
    },
    {
      "name": "Alice ISA (Global All-Cap)",
      "account_type": "Investment",
      "tax_wrapper": "ISA",
      "starting_balance": 8500000,
      "min_balance": 0,
      "interest_rate": 6.5,
      "currency": "GBP",
      "id": 16,
      "owners": [{"name": "Alice"}]
    },
    {
      "name": "Alice Cash ISA",
      "account_type": "Cash",
      "tax_wrapper": "ISA",
      "starting_balance": 2000000,
      "min_balance": 0,
      "interest_rate": 4.2,
      "currency": "GBP",
      "id": 17,
      "owners": [{"name": "Alice"}]
    },
    {
      "name": "Bob ISA",
      "account_type": "Investment",
      "tax_wrapper": "ISA",
      "starting_balance": 4500000,
      "min_balance": 0,
      "interest_rate": 6.5,
      "currency": "GBP",
      "id": 18,
      "owners": [{"name": "Bob"}]
    },
    {
      "name": "Bob Pension",
      "account_type": "Investment",
      "tax_wrapper": "Pension",
      "starting_balance": 6200000,
      "min_balance": 0,
      "interest_rate": 7.0,
      "currency": "GBP",
      "id": 19,
      "owners": [{"name": "Bob"}]
    },
    {
      "name": "General Investment (GIA)",
      "notes": "Spillover",
      "account_type": "Investment",
      "tax_wrapper": "None",
      "starting_balance": 0,
      "min_balance": 0,
      "interest_rate": 6.0,
      "currency": "GBP",
      "id": 20,
      "owners": [{"name": "Alice"}, {"name": "Bob"}]
    }
  ],
  "costs": [
    {
      "name": "Household Bills & Groceries",
      "value": 450000,
      "cadence": "monthly",
      "start_date": "2026-04-01",
      "is_recurring": True,
      "currency": "GBP",
      "account_id": 10
    },
    {
      "name": "Annual Family Holiday",
      "value": 1500000,
      "cadence": "annually",
      "start_date": "2027-06-01",
      "is_recurring": True,
      "currency": "GBP",
      "account_id": 11
    }
  ],
  "automation_rules": [
    {
      "name": "Sweep Excess to Savings",
      "priority": 10,
      "rule_type": "sweep",
      "source_account_id": 10,
      "target_account_id": 11,
      "trigger_value": 800000,
      "cadence": "monthly",
      "start_date": "2026-04-01"
    },
    {
      "name": "Top-up Current Account",
      "priority": 1,
      "rule_type": "top_up",
      "source_account_id": 11,
      "target_account_id": 10,
      "trigger_value": 200000,
      "transfer_value": 0,
      "cadence": "monthly",
      "start_date": "2026-04-01"
    },
    {
      "name": "Fill Alice ISA",
      "priority": 5,
      "rule_type": "transfer",
      "source_account_id": 10,
      "target_account_id": 16,
      "trigger_value": 0,
      "transfer_value": 100000,
      "cadence": "monthly",
      "start_date": "2026-04-06"
    },
    {
      "name": "Smart Mortgage Overpayment",
      "priority": 8,
      "rule_type": "mortgage_smart",
      "source_account_id": 10,
      "target_account_id": 13,
      "trigger_value": 500000,
      "transfer_value": 10,
      "cadence": "monthly",
      "start_date": "2026-05-01"
    }
  ],
  "financial_events": [
    {
      "name": "Future Car Upgrade",
      "value": -4500000,
      "event_date": "2029-01-01",
      "event_type": "income_expense",
      "currency": "GBP",
      "from_account_id": 11,
      "show_on_chart": True
    }
  ],
  "tax_limits": [
    {
      "name": "ISA Allowance",
      "amount": 2000000,
      "wrappers": ["ISA", "Lifetime ISA"],
      "start_date": "2026-04-06",
      "frequency": "Annually"
    },
    {
      "name": "Pension Annual Allowance",
      "amount": 6000000,
      "wrappers": ["Pension"],
      "start_date": "2026-04-06",
      "frequency": "Annually"
    }
  ],
  "decumulation_strategies": [
    {
      "name": "Retirement Drawdown",
      "strategy_type": "Standard",
      "enabled": True,
      "start_date": "2026-04-01"
    }
  ]
}

def seed():
    db = SessionLocal()
    try:
        # Idempotency Check: Does this scenario already exist?
        existing = db.query(models.Scenario).filter(models.Scenario.name == DEMO_SCENARIO["name"]).first()
        if existing:
            print(f"Skipping seed: Scenario '{DEMO_SCENARIO['name']}' already exists.")
            return

        print(f"Seeding '{DEMO_SCENARIO['name']}'...")
        
        # 1. Create Core Scenario
        scenario = models.Scenario(
            name=DEMO_SCENARIO["name"],
            description=DEMO_SCENARIO["description"],
            notes=DEMO_SCENARIO["notes"],
            start_date=date.fromisoformat(DEMO_SCENARIO["start_date"]),
            gbp_to_usd_rate=DEMO_SCENARIO["gbp_to_usd_rate"]
        )
        db.add(scenario)
        db.flush() # Generate ID

        # 2. Owners
        owner_objs = {} # Name -> DB Object
        for o_data in DEMO_SCENARIO["owners"]:
            owner = models.Owner(
                scenario_id=scenario.id,
                name=o_data["name"],
                notes=o_data.get("notes"),
                birth_date=date.fromisoformat(o_data["birth_date"]),
                retirement_age=o_data["retirement_age"]
            )
            scenario.owners.append(owner)
            db.flush()
            owner_objs[owner.name] = owner

        # 3. Accounts
        account_objs = {} # ID (in json) -> DB Object
        
        # Pass 1: Create Accounts (without links)
        for acc_data in DEMO_SCENARIO["accounts"]:
            acc = models.Account(
                scenario_id=scenario.id,
                name=acc_data["name"],
                notes=acc_data.get("notes"),
                account_type=acc_data["account_type"],
                tax_wrapper=acc_data["tax_wrapper"],
                starting_balance=acc_data["starting_balance"],
                min_balance=acc_data.get("min_balance", 0),
                interest_rate=acc_data.get("interest_rate", 0),
                currency=acc_data.get("currency", "GBP"),
                book_cost=acc_data.get("book_cost", acc_data["starting_balance"]),
                # Mortgage/RSU fields
                original_loan_amount=acc_data.get("original_loan_amount"),
                amortisation_period_years=acc_data.get("amortisation_period_years"),
                fixed_interest_rate=acc_data.get("fixed_interest_rate"),
                fixed_rate_period_years=acc_data.get("fixed_rate_period_years"),
                mortgage_start_date=date.fromisoformat(acc_data["mortgage_start_date"]) if acc_data.get("mortgage_start_date") else None,
                grant_date=date.fromisoformat(acc_data["grant_date"]) if acc_data.get("grant_date") else None,
                unit_price=acc_data.get("unit_price"),
                vesting_schedule=acc_data.get("vesting_schedule")
            )
            
            # Link Owners
            for o_ref in acc_data.get("owners", []):
                if o_ref["name"] in owner_objs:
                    acc.owners.append(owner_objs[o_ref["name"]])
            
            scenario.accounts.append(acc)
            db.flush()
            account_objs[acc_data["id"]] = acc

        # Pass 2: Link Accounts (Payment From / Target)
        for acc_data in DEMO_SCENARIO["accounts"]:
            db_acc = account_objs[acc_data["id"]]
            if acc_data.get("payment_from_account_id"):
                db_acc.payment_from_account_id = account_objs[acc_data["payment_from_account_id"]].id
            if acc_data.get("rsu_target_account_id"):
                db_acc.rsu_target_account_id = account_objs[acc_data["rsu_target_account_id"]].id
            db.add(db_acc)

        # 4. Incomes (Link to Owners & Accounts)
        for o_data in DEMO_SCENARIO["owners"]:
            db_owner = owner_objs[o_data["name"]]
            for inc_data in o_data["income_sources"]:
                inc = models.IncomeSource(
                    owner_id=db_owner.id,
                    name=inc_data["name"],
                    net_value=inc_data["net_value"],
                    cadence=inc_data["cadence"],
                    is_pre_tax=inc_data.get("is_pre_tax", False),
                    salary_sacrifice_value=inc_data.get("salary_sacrifice_value", 0),
                    taxable_benefit_value=inc_data.get("taxable_benefit_value", 0),
                    employer_pension_contribution=inc_data.get("employer_pension_contribution", 0),
                    start_date=date.fromisoformat(inc_data["start_date"]),
                    currency=inc_data.get("currency", "GBP")
                )
                
                # Link to Account?
                # In JSON structure, incomes are nested in owners, but we need to find which account ID they map to
                # The corrected JSON I gave you earlier didn't explicitly have account_id inside income_sources, 
                # but the *original* faulty one did. 
                # Let's assume for the seed we want to map to "Joint Current Account" (ID 10) by default 
                # unless specified otherwise.
                # EDIT: I see I added account_id to the JSON in my last turn. Good.
                # However, the seed script needs to map that "10" to the *actual* DB ID of account 10.
                
                # Find matching income in the DEMO_SCENARIO structure to get its intended account_id
                # (Since we are iterating the dict)
                target_acc_id = inc_data.get("account_id", 10) # Default to 10
                if target_acc_id in account_objs:
                    inc.account_id = account_objs[target_acc_id].id
                
                if inc_data.get("salary_sacrifice_account_id") and inc_data["salary_sacrifice_account_id"] in account_objs:
                    inc.salary_sacrifice_account_id = account_objs[inc_data["salary_sacrifice_account_id"]].id

                db.add(inc)

        # 5. Costs
        for c_data in DEMO_SCENARIO["costs"]:
            if c_data["account_id"] in account_objs:
                cost = models.Cost(
                    scenario_id=scenario.id,
                    account_id=account_objs[c_data["account_id"]].id,
                    name=c_data["name"],
                    value=c_data["value"],
                    cadence=c_data["cadence"],
                    start_date=date.fromisoformat(c_data["start_date"]),
                    is_recurring=c_data["is_recurring"]
                )
                scenario.costs.append(cost)

        # 6. Rules
        for r_data in DEMO_SCENARIO["automation_rules"]:
            if r_data["source_account_id"] in account_objs and r_data["target_account_id"] in account_objs:
                rule = models.AutomationRule(
                    scenario_id=scenario.id,
                    name=r_data["name"],
                    rule_type=r_data["rule_type"],
                    source_account_id=account_objs[r_data["source_account_id"]].id,
                    target_account_id=account_objs[r_data["target_account_id"]].id,
                    trigger_value=r_data["trigger_value"],
                    transfer_value=r_data.get("transfer_value"),
                    cadence=r_data["cadence"],
                    priority=r_data.get("priority", 0),
                    start_date=date.fromisoformat(r_data["start_date"])
                )
                scenario.automation_rules.append(rule)

        # 7. Financial Events
        for e_data in DEMO_SCENARIO["financial_events"]:
            from_acc = account_objs.get(e_data.get("from_account_id"))
            evt = models.FinancialEvent(
                scenario_id=scenario.id,
                name=e_data["name"],
                value=e_data["value"],
                event_date=date.fromisoformat(e_data["event_date"]),
                event_type=e_data["event_type"],
                show_on_chart=e_data.get("show_on_chart", False)
            )
            if from_acc: evt.from_account_id = from_acc.id
            scenario.financial_events.append(evt)

        # 8. Tax Limits
        for t_data in DEMO_SCENARIO["tax_limits"]:
            scenario.tax_limits.append(models.TaxLimit(
                name=t_data["name"],
                amount=t_data["amount"],
                wrappers=t_data["wrappers"],
                start_date=date.fromisoformat(t_data["start_date"]),
                frequency=t_data["frequency"]
            ))

        # 9. Decumulation
        for s_data in DEMO_SCENARIO["decumulation_strategies"]:
            scenario.decumulation_strategies.append(models.DecumulationStrategy(
                name=s_data["name"],
                strategy_type=s_data["strategy_type"],
                enabled=s_data["enabled"],
                start_date=date.fromisoformat(s_data["start_date"])
            ))

        db.commit()
        print("Seed complete.")

    except Exception as e:
        print(f"Seed failed: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    seed()
