from app import models, enums, schemas
from app.engine.context import ProjectionContext
from dateutil.relativedelta import relativedelta
from app.services.tax import TaxService
import logging

logger = logging.getLogger(__name__)

def process_rsu_vesting(scenario: models.Scenario, context: ProjectionContext):
    for acc in context.all_accounts:
        if acc.account_type != enums.AccountType.RSU_GRANT: continue
        
        try:
            if not acc.grant_date or not acc.vesting_schedule: continue
            schedule = acc.vesting_schedule
            if not isinstance(schedule, list): continue
            
            unit_price = acc.unit_price if acc.unit_price is not None else 0
            current_month = context.month_start
            grant_date = acc.grant_date
            
            cadence = getattr(acc, 'vesting_cadence', 'monthly') or 'monthly'
            is_quarterly = (cadence == 'quarterly')
            
            delta = relativedelta(current_month, grant_date)
            months_elapsed = delta.years * 12 + delta.months
            
            if months_elapsed <= 0: continue
            if is_quarterly and (months_elapsed % 3 != 0): continue

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
                    fraction = months_into_year / 12.0
                    target_vested_percent += (percent * fraction)
                    break 
                previous_years_end_month = year_end_month

            original_units = acc.starting_balance 
            target_remaining_units = int(original_units * (1.0 - (target_vested_percent / 100.0)))
            current_units = context.account_balances.get(acc.id, 0)
            units_to_vest = current_units - target_remaining_units
            
            if units_to_vest > current_units: units_to_vest = current_units
            if units_to_vest <= 0: continue

            price_gbp = unit_price 
            if acc.currency == enums.Currency.USD:
                rate = scenario.gbp_to_usd_rate if scenario.gbp_to_usd_rate and scenario.gbp_to_usd_rate > 0 else 1.25
                price_gbp = int(unit_price / rate)
                
            years_float = months_elapsed / 12.0
            growth_rate = (acc.interest_rate or 0.0) / 100.0
            growth_factor = (1 + growth_rate) ** years_float
            current_price_gbp = int(price_gbp * growth_factor)
            
            gross_value = units_to_vest * current_price_gbp 
            
            owner_id = acc.owners[0].id if acc.owners else None
            tax_deducted = 0
            ni_deducted = 0
            
            if owner_id:
                ytd = context.ytd_earnings.get(owner_id, {'taxable': 0, 'ni': 0})
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
            
            context.account_balances[acc.id] -= units_to_vest
            target_id = acc.rsu_target_account_id
            if target_id and target_id in context.account_balances:
                context.account_balances[target_id] += net_proceeds
                context.flows[target_id]['transfers_in'] += net_proceeds / 100.0
        
        except Exception as e:
            logger.error(f"Error processing RSU {acc.name} ({acc.id}): {e}")
            continue
