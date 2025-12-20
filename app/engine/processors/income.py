from app import models, enums, schemas
from app.services.tax import TaxService
from app.engine.context import ProjectionContext
from app.engine.tax_logic import track_contribution, get_contribution_headroom

def process_income(scenario: models.Scenario, context: ProjectionContext):
    seen_ids = set(); all_income_sources = []
    for owner in scenario.owners:
        for inc in owner.income_sources:
            if inc.id not in seen_ids: all_income_sources.append(inc); seen_ids.add(inc.id)
    for inc in all_income_sources:
        if inc.account_id not in context.account_balances: continue
        if not (inc.start_date.replace(day=1) <= context.month_start and (inc.end_date is None or inc.end_date >= context.month_start)): continue
        should = False
        if inc.cadence.value == 'once':
            if context.month_start.year == inc.start_date.year and context.month_start.month == inc.start_date.month: should = True
        elif inc.cadence.value == 'monthly': should = True
        elif inc.cadence.value == 'quarterly' and context.month_start.month in [1, 4, 7, 10]: should = True
        elif inc.cadence.value == 'annually' and context.month_start.month == inc.start_date.month: should = True
        if should:
            if inc.owner_id not in context.ytd_earnings: context.ytd_earnings[inc.owner_id] = {'taxable': 0, 'ni': 0}
            gross_input = inc.net_value 
            net_to_pay = gross_input
            tax_deducted = 0
            emp_contrib = inc.employer_pension_contribution or 0
            if emp_contrib > 0 and inc.salary_sacrifice_account_id:
                sac_target = inc.salary_sacrifice_account_id
                if sac_target in context.account_balances:
                    context.account_balances[sac_target] += emp_contrib
                    context.account_book_costs[sac_target] += emp_contrib
                    context.flows[sac_target]["employer_contribution"] += emp_contrib / 100.0
                    context.flows[sac_target]["transfers_in"] += emp_contrib / 100.0
                    track_contribution(context, sac_target, emp_contrib)
            if inc.is_pre_tax:
                sac_amount = inc.salary_sacrifice_value or 0
                sac_target = inc.salary_sacrifice_account_id
                adjusted_gross = max(0, gross_input - sac_amount)
                if sac_amount > 0 and sac_target and sac_target in context.account_balances:
                    context.account_balances[sac_target] += sac_amount
                    context.account_book_costs[sac_target] += sac_amount 
                    context.flows[sac_target]["transfers_in"] += sac_amount / 100.0
                    track_contribution(context, sac_target, sac_amount)
                bik_amount = inc.taxable_benefit_value or 0
                amount_for_tax = adjusted_gross + bik_amount
                amount_for_ni = adjusted_gross 
                current_ytd_tax = context.ytd_earnings[inc.owner_id]['taxable']
                current_ytd_ni = context.ytd_earnings[inc.owner_id]['ni']
                tax_deducted = TaxService.calculate_payroll_deductions(amount_for_tax, amount_for_ni, current_ytd_tax, current_ytd_ni)
                context.ytd_earnings[inc.owner_id]['taxable'] += amount_for_tax
                context.ytd_earnings[inc.owner_id]['ni'] += amount_for_ni
                net_to_pay = adjusted_gross - tax_deducted
            else:
                context.ytd_earnings[inc.owner_id]['taxable'] += gross_input
                context.ytd_earnings[inc.owner_id]['ni'] += gross_input
                net_to_pay = gross_input
            target_account = next((acc for acc in context.all_accounts if acc.id == inc.account_id), None)
            final_credit = net_to_pay
            if target_account and inc.currency != target_account.currency:
                if inc.currency == enums.Currency.USD and target_account.currency == enums.Currency.GBP: final_credit = round(net_to_pay / scenario.gbp_to_usd_rate)
                elif inc.currency == enums.Currency.GBP and target_account.currency == enums.Currency.USD: final_credit = round(net_to_pay * scenario.gbp_to_usd_rate)
            headroom = get_contribution_headroom(context, inc.account_id, scenario.tax_limits)
            if headroom < final_credit:
                context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=inc.account_id, message=f"Tax Limit: Income '{inc.name}' exceeds allowance.", source_type="income", source_id=inc.id))
            context.account_balances[inc.account_id] += final_credit
            context.account_book_costs[inc.account_id] += final_credit 
            context.flows[inc.account_id]["income"] += gross_input / 100.0
            context.flows[inc.account_id]["tax"] += tax_deducted / 100.0
            track_contribution(context, inc.account_id, final_credit)
