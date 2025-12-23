from app import models, enums
from app.engine.context import ProjectionContext
from dateutil.relativedelta import relativedelta
import math

def process_rsu_vesting(scenario: models.Scenario, context: ProjectionContext):
    # Iterate all accounts that are RSU type
    rsu_accounts = [a for a in context.all_accounts if a.account_type == enums.AccountType.RSU_GRANT]
    
    for rsu in rsu_accounts:
        if not rsu.vesting_schedule or not rsu.grant_date: continue
        
        # Calculate months since grant
        # diff = (context.month_start.year - rsu.grant_date.year) * 12 + (context.month_start.month - rsu.grant_date.month)
        # Better: check if current month matches a vesting milestone
        
        # We need to know which tranche vests THIS month.
        # Schedule: [{"year": 1, "percent": 25}, ...]
        # Vest Date = Grant Date + X years
        
        vest_month_matches = []
        for tranche in rsu.vesting_schedule:
            years = int(tranche.get("year", 0))
            percent = float(tranche.get("percent", 0))
            
            vest_date = rsu.grant_date + relativedelta(years=years)
            
            # If vesting cadence is monthly, we divide this tranche over 12 months *after* the cliff?
            # Or is it simple annual vesting?
            # Implemented logic: Simple Match
            if vest_date.year == context.month_start.year and vest_date.month == context.month_start.month:
                vest_month_matches.append(percent)
        
        total_percent_vesting = sum(vest_month_matches)
        
        if total_percent_vesting > 0:
            # Calculate Value
            # total_units = rsu.starting_balance (but we need initial units, balance tracks remaining?)
            # Assuming starting_balance is TOTAL units granted.
            # And we don't decrement balance in this simple engine, we just generate income.
            
            # Value = Units * Percent * Price
            # Price is in pence.
            
            units_vesting = (rsu.starting_balance * total_percent_vesting) / 100.0
            vest_value = int(units_vesting * (rsu.unit_price or 0))
            
            # Log
            # context.rule_logs.append(...) # (Simplified, context doesn't strictly have logs list in this version)
            
            # Credit Target
            if rsu.rsu_target_account_id:
                target_id = rsu.rsu_target_account_id
                if target_id in context.account_balances:
                    context.account_balances[target_id] += vest_value
                    if target_id not in context.flows: context.flows[target_id] = {}
                    if "rsu_vest" not in context.flows[target_id]: context.flows[target_id]["rsu_vest"] = 0
                    context.flows[target_id]["rsu_vest"] += vest_value / 100.0
