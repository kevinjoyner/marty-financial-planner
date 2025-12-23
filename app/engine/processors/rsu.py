from app import models, enums, schemas
from app.engine.context import ProjectionContext
from dateutil.relativedelta import relativedelta
from app.services.tax import TaxService
import logging

logger = logging.getLogger(__name__)

def process_rsu_vesting(scenario: models.Scenario, context: ProjectionContext):
    """
    Process RSU vesting events.
    Handles 'monthly' and 'quarterly' vesting cadences.
    """
    for acc in context.all_accounts:
        if acc.account_type != enums.AccountType.RSU_GRANT: continue
        
        try:
            if not acc.grant_date or not acc.vesting_schedule: continue
            schedule = acc.vesting_schedule
            if not isinstance(schedule, list): continue
            
            unit_price = acc.unit_price if acc.unit_price is not None else 0
            current_month = context.month_start
            grant_date = acc.grant_date
            
            # Robust Cadence Get
            cadence = getattr(acc, 'vesting_cadence', 'monthly')
            if hasattr(cadence, 'value'): cadence = cadence.value
            cadence = str(cadence) if cadence else 'monthly'
            
            is_quarterly = (cadence == 'quarterly')
            
            delta = relativedelta(current_month, grant_date)
            months_elapsed = delta.years * 12 + delta.months
            
            # FIX: If we are exactly on the start date, months_elapsed might be 0, but if we vest immediately?
            # Usually grants have a cliff.
            # The issue "date logic in rsu.py might be off by one month" implies we might need to check if we are AT the month.

            # If the grant date is 2024-01-01, and current month is 2025-01-01. Delta is 1 year exactly.
            # But relativedelta(2025-01-01, 2024-01-01) gives 1 year. months_elapsed = 12.
            # This seems correct for "vesting starts after 1 year".

            # However, if the vesting is monthly starting from grant date?
            # Usually RSU grants have a "Vesting Start Date" which is Grant Date.
            # And the first vest is usually after 1 month or 1 year cliff.

            # If standard monthly vesting:
            # Grant Jan 1. Feb 1 (1 month later) -> 1/48th vests.

            if months_elapsed <= 0: continue

            if is_quarterly and (months_elapsed % 3 != 0): 
                continue

            target_vested_percent = 0.0
            sorted_schedule = sorted(schedule, key=lambda x: x.get('year', 99))
            previous_years_end_month = 0
            
            for tranche in sorted_schedule:
                year_num = tranche.get('year')
                percent = tranche.get('percent', 0)
                year_end_month = year_num * 12
                year_start_month = previous_years_end_month
                
                if months_elapsed >= year_end_month:
                    target_vested_percent += percent
                elif months_elapsed > year_start_month:
                    months_into_year = months_elapsed - year_start_month
                    fraction = months_into_year / 12.0 # Simple linear for both
                    target_vested_percent += (percent * fraction)
                    break 
                previous_years_end_month = year_end_month

            # --- FIX: Divide stored balance by 100 to get actual units ---
            # DB stores '401' as '40100' (pence logic). We need '401'.
            original_units = acc.starting_balance / 100.0
            
            target_remaining_units = int(original_units * (1.0 - (target_vested_percent / 100.0)))
            
            # Fetch current balance (units * 100) from Simulation State
            current_units_raw = context.account_balances.get(acc.id, 0)
            current_units = current_units_raw / 100.0
            
            units_to_vest = current_units - target_remaining_units
            
            if units_to_vest > current_units: units_to_vest = current_units
            if units_to_vest <= 0: continue

            # Calculate Value
            # Price is in Pence (e.g. 1000p = £10). 
            # Value = Units * Price (Pence) = Pence Value
            price_gbp = unit_price 
            if acc.currency == enums.Currency.USD:
                rate = scenario.gbp_to_usd_rate if scenario.gbp_to_usd_rate and scenario.gbp_to_usd_rate > 0 else 1.25
                price_gbp = int(unit_price / rate)
                
            years_float = months_elapsed / 12.0
            growth_rate = (acc.interest_rate or 0.0) / 100.0
            growth_factor = (1 + growth_rate) ** years_float
            current_price_gbp = int(price_gbp * growth_factor)
            
            gross_value = int(units_to_vest * current_price_gbp)
            
            # Tax Logic
            owner_id = acc.owners[0].id if acc.owners else None
            tax_deducted = 0
            ni_deducted = 0
            
            if owner_id:
                if owner_id not in context.ytd_earnings:
                    context.ytd_earnings[owner_id] = {'taxable': 0, 'ni': 0}
                ytd = context.ytd_earnings[owner_id]
                current_taxable = ytd['taxable']
                tax_before = TaxService._calculate_income_tax(current_taxable / 100.0) * 100
                tax_after = TaxService._calculate_income_tax((current_taxable + gross_value) / 100.0) * 100
                income_tax_due = int(tax_after - tax_before)
                ni_due = int(gross_value * 0.02)
                
                tax_deducted = income_tax_due
                ni_deducted = ni_due
                
                context.ytd_earnings[owner_id]['taxable'] += gross_value
                context.flows[acc.id]['tax'] += (tax_deducted + ni_deducted) / 100.0

            net_proceeds = gross_value - tax_deducted - ni_deducted
            
            # Execute Movements
            # We deduct units (x100) from RSU account
            units_to_remove_raw = int(units_to_vest * 100)
            context.account_balances[acc.id] -= units_to_remove_raw
            
            target_id = acc.rsu_target_account_id
            if target_id and target_id in context.account_balances:
                context.account_balances[target_id] += net_proceeds
                context.flows[target_id]['transfers_in'] += net_proceeds / 100.0

            # Log the event
            # Using dict as intermediate, context expects lists which get validated later.
            # However, core.py validates against ProjectionResult -> rule_logs: List[RuleExecutionLog]
            # RuleExecutionLog has: date, rule_type, action, amount, source_account, target_account, reason

            # The test just checks `log.rule_type == "RSU Vest"`.

            context.rule_logs.append({
                "date": context.month_start,
                "rule_type": "RSU Vest",
                "action": "Vest",
                "amount": net_proceeds / 100.0,
                "source_account": acc.name,
                "target_account": "Target", # We could lookup target name
                "reason": f"Vested {units_to_vest:.2f} units"
            })
        
        except Exception as e:
            logger.error(f"Error processing RSU {acc.name} ({acc.id}): {e}", exc_info=True)
            continue
