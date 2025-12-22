from sqlalchemy.orm import Session
from app import models, schemas, enums
from .context import ProjectionContext
from .processors import income, costs, transfers, mortgage, tax, rsu, growth, rules, decumulation
from dateutil.relativedelta import relativedelta
from datetime import date
import logging

logger = logging.getLogger(__name__)

def run_projection(scenario: models.Scenario, months: int, overrides: list) -> schemas.ProjectionResult:
    context = ProjectionContext(scenario, months, overrides)
    
    for _ in range(months + 1):
        month_date = context.month_start
        
        income.process_income(scenario, context)
        costs.process_costs(scenario, context)
        transfers.process_transfers(scenario, context)
        
        rsu.process_rsu_vesting(scenario, context) 
        mortgage.process_mortgages(scenario, context)
        
        rules.process_rules(scenario, context)
        decumulation.process_decumulation(scenario, context)
        growth.process_growth(scenario, context) 
        
        if month_date.month == 4: 
             tax.process_tax_year_end(scenario, context)

        total_balance = 0
        liquid_assets = 0
        
        for acc in context.all_accounts:
            raw_balance = context.account_balances.get(acc.id, 0)
            val = raw_balance
            
            # Valuate RSU
            if acc.account_type == enums.AccountType.RSU_GRANT:
                if acc.grant_date:
                    delta = relativedelta(month_date, acc.grant_date)
                    years_elapsed = delta.years + (delta.months / 12.0)
                    if years_elapsed < 0: years_elapsed = 0
                    
                    price_gbp = acc.unit_price or 0
                    if acc.currency == enums.Currency.USD:
                        rate = scenario.gbp_to_usd_rate or 1.25
                        price_gbp = int(price_gbp / rate)
                    
                    growth_rate = (acc.interest_rate or 0.0) / 100.0
                    growth_factor = (1 + growth_rate) ** years_elapsed
                    current_price = int(price_gbp * growth_factor)
                    
                    val = raw_balance * current_price 
            
            total_balance += val
            
            is_liquid = True
            if acc.account_type in [enums.AccountType.MORTGAGE, enums.AccountType.LOAN, enums.AccountType.PROPERTY, enums.AccountType.MAIN_RESIDENCE, enums.AccountType.RSU_GRANT]:
                is_liquid = False
            if acc.tax_wrapper in ["Pension", "Lifetime ISA"]: 
                is_liquid = False
            
            if is_liquid:
                liquid_assets += val

        context.data_points.append(schemas.ProjectionDataPoint(
            date=month_date,
            balance=total_balance,
            liquid_assets=liquid_assets,
        ))
        
        context.advance_month()

    return schemas.ProjectionResult(
        data_points=context.data_points,
        warnings=context.warnings,
        metadata={"currency": "GBP"}
    )
