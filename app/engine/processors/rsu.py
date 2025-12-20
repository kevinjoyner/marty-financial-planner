import math
from dateutil.relativedelta import relativedelta
from app import models, enums, schemas, utils
from app.services.tax import TaxService
from app.engine.context import ProjectionContext
from app.engine.tax_logic import track_contribution, get_contribution_headroom

def process_rsu_vesting(scenario: models.Scenario, context: ProjectionContext):
    for acc in context.all_accounts:
        if acc.account_type != enums.AccountType.RSU_GRANT: continue
        if not acc.rsu_target_account_id or not acc.vesting_schedule: continue
        if acc.id not in context.account_balances: continue
        start_anchor = acc.grant_date or scenario.start_date
        if context.month_start < start_anchor.replace(day=1): continue
        diff = relativedelta(context.month_start, start_anchor.replace(day=1))
        months_elapsed = diff.years * 12 + diff.months + 1 
        current_year = math.ceil(months_elapsed / 12)
        month_in_year = (months_elapsed - 1) % 12 + 1
        tranche = next((t for t in acc.vesting_schedule if t.get("year") == current_year), None)
        if not tranche: continue
        percent = float(tranche.get("percent", 0)); 
        if percent <= 0: continue
        original_units = acc.starting_balance; 
        if original_units <= 0: continue
        total_units_this_year = int((original_units * (percent / 100.0)))
        monthly_units = math.floor(total_units_this_year / 12)
        if month_in_year == 12: vested_so_far = monthly_units * 11; monthly_units = total_units_this_year - vested_so_far
        current_units = context.account_balances[acc.id]
        if monthly_units > current_units: monthly_units = current_units
        if monthly_units <= 0: continue
        unit_price_at_grant = acc.unit_price or 0
        safe_rate = acc.interest_rate or 0.0
        monthly_rate = safe_rate / 100 / 12
        current_unit_price = unit_price_at_grant * ((1 + monthly_rate) ** months_elapsed)
        vest_value_gross = int((monthly_units / 100.0) * current_unit_price)
        vest_value_gbp = vest_value_gross
        if acc.currency == enums.Currency.USD: vest_value_gbp = int(vest_value_gross / scenario.gbp_to_usd_rate)
        owner_id = acc.owners[0].id if acc.owners else 0
        if owner_id not in context.ytd_earnings: context.ytd_earnings[owner_id] = {'taxable': 0, 'ni': 0}
        current_ytd_tax = context.ytd_earnings[owner_id]['taxable']
        current_ytd_ni = context.ytd_earnings[owner_id]['ni']
        tax = TaxService.calculate_payroll_deductions(vest_value_gbp, vest_value_gbp, current_ytd_tax, current_ytd_ni)
        context.ytd_earnings[owner_id]['taxable'] += vest_value_gbp
        context.ytd_earnings[owner_id]['ni'] += vest_value_gbp
        net_gbp = vest_value_gbp - tax
        target_id = acc.rsu_target_account_id
        context.account_balances[acc.id] -= monthly_units
        if target_id in context.account_balances:
            headroom = get_contribution_headroom(context, target_id, scenario.tax_limits)
            if headroom < net_gbp:
                context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=target_id, message=f"Tax Limit: RSU Vest exceeds allowance.", source_type="rsu_vest", source_id=acc.id))
            context.account_balances[target_id] += net_gbp
            context.account_book_costs[target_id] += net_gbp 
            context.flows[target_id]["transfers_in"] += net_gbp / 100.0
            context.flows[target_id]["tax"] += tax / 100.0 
            track_contribution(context, target_id, net_gbp)
            src_name = acc.name
            tgt_name = next((a.name for a in context.all_accounts if a.id == target_id), "Target")
            context.rule_logs.append(schemas.RuleExecutionLog(date=context.month_start, rule_type="RSU Vest", action=f"Vested {monthly_units/100} units", amount=net_gbp / 100.0, source_account=src_name, target_account=tgt_name, reason=f"Tax: {utils.format_currency(tax)}"))
