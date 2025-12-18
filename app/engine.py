from dataclasses import dataclass, field
from dateutil.relativedelta import relativedelta
from datetime import date
from . import models, schemas, utils, enums
from .services.tax import TaxService
from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import math
import sys

@dataclass
class ProjectionContext:
    month_start: date
    account_balances: Dict[int, int]
    account_book_costs: Dict[int, int]
    flows: Dict[int, Any]
    ytd_contributions: Dict = field(default_factory=dict)
    ytd_earnings: Dict = field(default_factory=dict)
    ytd_interest: Dict = field(default_factory=dict)
    ytd_gains: Dict = field(default_factory=dict)
    warnings: List = field(default_factory=list)
    rule_logs: List = field(default_factory=list)
    mortgage_state: Dict = field(default_factory=dict)
    mortgage_stats: List = field(default_factory=list)
    annotations: List = field(default_factory=list)
    all_accounts: List[models.Account] = field(default_factory=list)
    prev_balances: Dict[int, int] = field(default_factory=dict)

# ... (Standard helpers) ...
def _calculate_disposal_impact(withdrawal_amount: int, current_balance: int, current_book_cost: int, account_type: enums.AccountType, tax_wrapper: enums.TaxWrapper) -> tuple[int, int]:
    # EXEMPTIONS: 
    # 1. Tax Wrappers (ISA/Pension)
    # 2. Cash/Debt accounts
    # 3. Main Residence (Private Residence Relief)
    if tax_wrapper and tax_wrapper != enums.TaxWrapper.NONE: return 0, 0
    if account_type in [enums.AccountType.CASH, enums.AccountType.MORTGAGE, enums.AccountType.LOAN, enums.AccountType.MAIN_RESIDENCE]: return 0, 0
    
    if current_balance <= 0 or withdrawal_amount <= 0: return 0, 0
    fraction = withdrawal_amount / current_balance
    if fraction > 1.0: fraction = 1.0
    cost_portion = int(current_book_cost * fraction)
    gain = withdrawal_amount - cost_portion
    return cost_portion, gain

def _calculate_gbp_balances(current_balances, accounts, rate, month_start=None):
    gbp_balances = {}
    total = 0
    account_map = {acc.id: acc for acc in accounts}
    for acc_id, bal in current_balances.items():
        acc = account_map.get(acc_id)
        if not acc: continue
        val_gbp = bal
        if acc.account_type == enums.AccountType.RSU_GRANT:
            if not acc.grant_date or not acc.unit_price: val_gbp = 0
            else:
                months_elapsed = 0
                if month_start and month_start > acc.grant_date:
                    diff = relativedelta(month_start, acc.grant_date.replace(day=1))
                    months_elapsed = diff.years * 12 + diff.months
                safe_rate = acc.interest_rate or 0.0
                monthly_rate = safe_rate / 100 / 12
                current_price = acc.unit_price * ((1 + monthly_rate) ** months_elapsed)
                units = bal / 100.0
                val_gbp = int(units * current_price)
                if acc.currency == enums.Currency.USD: val_gbp = round(val_gbp / rate)
        elif acc.currency == enums.Currency.USD:
            val_gbp = round(bal / rate)
        gbp_balances[acc_id] = val_gbp / 100.0
        total += val_gbp
    return gbp_balances, total / 100.0

def _track_contribution(context: ProjectionContext, account_id: int, amount: int):
    if amount <= 0: return
    acc = next((a for a in context.all_accounts if a.id == account_id), None)
    if not acc or not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.NONE: return
    if acc.owners:
        owner_id = acc.owners[0].id
        wrapper_str = acc.tax_wrapper.value 
        type_str = acc.account_type.value
        if owner_id not in context.ytd_contributions: context.ytd_contributions[owner_id] = {}
        key = f"{wrapper_str}:{type_str}"
        context.ytd_contributions[owner_id][key] = context.ytd_contributions[owner_id].get(key, 0) + amount

def _get_contribution_headroom(context: ProjectionContext, account_id: int, tax_limits: List[models.TaxLimit]):
    acc = next((a for a in context.all_accounts if a.id == account_id), None)
    if not acc or not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.NONE: return 999999999999
    if not acc.owners: return 0
    owner_id = acc.owners[0].id
    wrapper_str = acc.tax_wrapper.value
    type_str = acc.account_type.value
    applicable_limits = []
    for limit in tax_limits:
        if limit.start_date <= context.month_start and (limit.end_date is None or limit.end_date >= context.month_start):
            if wrapper_str in limit.wrappers:
                if limit.account_types and len(limit.account_types) > 0:
                    if type_str not in limit.account_types: continue 
                applicable_limits.append(limit)
    if not applicable_limits: return 999999999999
    min_headroom = 999999999999
    for limit in applicable_limits:
        limit_usage = 0
        if owner_id in context.ytd_contributions:
            user_contribs = context.ytd_contributions[owner_id]
            for key, amount in user_contribs.items():
                c_wrapper, c_type = key.split(":")
                wrapper_match = c_wrapper in limit.wrappers
                type_match = True
                if limit.account_types and len(limit.account_types) > 0:
                    if c_type not in limit.account_types: type_match = False
                if wrapper_match and type_match: limit_usage += amount
        headroom = max(0, limit.amount - limit_usage)
        if headroom < min_headroom: min_headroom = headroom
    return min_headroom

def _process_income(scenario: models.Scenario, context: ProjectionContext):
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
                    _track_contribution(context, sac_target, emp_contrib)
            if inc.is_pre_tax:
                sac_amount = inc.salary_sacrifice_value or 0
                sac_target = inc.salary_sacrifice_account_id
                adjusted_gross = max(0, gross_input - sac_amount)
                if sac_amount > 0 and sac_target and sac_target in context.account_balances:
                    context.account_balances[sac_target] += sac_amount
                    context.account_book_costs[sac_target] += sac_amount 
                    context.flows[sac_target]["transfers_in"] += sac_amount / 100.0
                    _track_contribution(context, sac_target, sac_amount)
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
            headroom = _get_contribution_headroom(context, inc.account_id, scenario.tax_limits)
            if headroom < final_credit:
                context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=inc.account_id, message=f"Tax Limit: Income '{inc.name}' exceeds allowance.", source_type="income", source_id=inc.id))
            context.account_balances[inc.account_id] += final_credit
            context.account_book_costs[inc.account_id] += final_credit 
            context.flows[inc.account_id]["income"] += gross_input / 100.0
            context.flows[inc.account_id]["tax"] += tax_deducted / 100.0
            _track_contribution(context, inc.account_id, final_credit)

def _process_costs(scenario: models.Scenario, context: ProjectionContext):
    seen_ids = set(); unique_costs = []
    for c in scenario.costs:
        if c.id not in seen_ids: unique_costs.append(c); seen_ids.add(c.id)
    for cost in unique_costs:
        if cost.account_id not in context.account_balances: continue
        if not (cost.start_date.replace(day=1) <= context.month_start and (cost.end_date is None or cost.end_date >= context.month_start)): continue
        value = cost.value
        target_account = next((acc for acc in context.all_accounts if acc.id == cost.account_id), None)
        if target_account and cost.currency != target_account.currency:
            if cost.currency == enums.Currency.USD and target_account.currency == enums.Currency.GBP: value = round(value / scenario.gbp_to_usd_rate)
            elif cost.currency == enums.Currency.GBP and target_account.currency == enums.Currency.USD: value = round(value * scenario.gbp_to_usd_rate)
        should = False
        if cost.cadence.value == 'once':
             if context.month_start.year == cost.start_date.year and context.month_start.month == cost.start_date.month: should = True
        elif cost.cadence.value == 'monthly': should = True
        elif cost.cadence.value == 'quarterly' and context.month_start.month in [1, 4, 7, 10]: should = True
        elif cost.cadence.value == 'annually' and context.month_start.month == cost.start_date.month: should = True
        if should:
            context.account_balances[cost.account_id] -= value
            context.flows[cost.account_id]["costs"] += value / 100.0

def _process_transfers(scenario: models.Scenario, context: ProjectionContext):
    seen_ids = set(); unique_transfers = []
    for t in scenario.transfers:
        if t.id not in seen_ids: unique_transfers.append(t); seen_ids.add(t.id)
    for transfer in unique_transfers:
        if not (transfer.start_date.replace(day=1) <= context.month_start and (transfer.end_date is None or transfer.end_date >= context.month_start)): continue
        value = transfer.value
        from_account = next((acc for acc in context.all_accounts if acc.id == transfer.from_account_id), None)
        to_account = next((acc for acc in context.all_accounts if acc.id == transfer.to_account_id), None)
        if not from_account or not to_account: continue
        if from_account.currency != to_account.currency:
            if from_account.currency == enums.Currency.USD and to_account.currency == enums.Currency.GBP: value = round(value / scenario.gbp_to_usd_rate)
            elif from_account.currency == enums.Currency.GBP and to_account.currency == enums.Currency.USD: value = round(value * scenario.gbp_to_usd_rate)
        should = False
        if transfer.cadence.value == 'once':
             if context.month_start.year == transfer.start_date.year and context.month_start.month == transfer.start_date.month: should = True
        elif transfer.cadence.value == 'monthly': should = True
        elif transfer.cadence.value == 'quarterly' and context.month_start.month in [1, 4, 7, 10]: should = True
        elif transfer.cadence.value == 'annually' and context.month_start.month == transfer.start_date.month: should = True
        if should:
            if transfer.show_on_chart:
                context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label=transfer.name, type="transaction"))
            
            headroom = _get_contribution_headroom(context, transfer.to_account_id, scenario.tax_limits)
            if headroom < value:
                context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=transfer.to_account_id, message=f"Tax Limit: Transfer exceeds allowance.", source_type="transfer", source_id=transfer.id))
            cgt_tax = 0
            cost_portion, gain = _calculate_disposal_impact(value, context.account_balances[from_account.id], context.account_book_costs[from_account.id], from_account.account_type, from_account.tax_wrapper)
            if gain > 0:
                owner_id = from_account.owners[0].id if from_account.owners else 0
                if owner_id not in context.ytd_gains: context.ytd_gains[owner_id] = 0
                earnings = context.ytd_earnings.get(owner_id, {}).get('taxable', 0)
                cgt_tax = TaxService.calculate_capital_gains_tax(gain, context.ytd_gains[owner_id], earnings)
                context.ytd_gains[owner_id] += gain
            context.account_balances[transfer.from_account_id] -= value
            context.account_book_costs[transfer.from_account_id] -= cost_portion 
            context.flows[transfer.from_account_id]["transfers_out"] += value / 100.0
            context.flows[transfer.from_account_id]["cgt"] += cgt_tax / 100.0 
            net_received = value - cgt_tax 
            context.account_balances[transfer.to_account_id] += net_received
            context.account_book_costs[transfer.to_account_id] += net_received 
            context.flows[transfer.to_account_id]["transfers_in"] += net_received / 100.0
            _track_contribution(context, transfer.to_account_id, net_received)

def _process_events(scenario: models.Scenario, context: ProjectionContext):
    next_month_start = context.month_start + relativedelta(months=1)
    seen_ids = set(); unique_events = []
    for e in scenario.financial_events:
        if e.id not in seen_ids: unique_events.append(e); seen_ids.add(e.id)
    for event in unique_events:
        if (event.event_date >= context.month_start and event.event_date < next_month_start and event.event_date >= scenario.start_date):
            if event.show_on_chart:
                context.annotations.append(schemas.ProjectionAnnotation(date=event.event_date, label=event.name, type="transaction"))
                
            if event.event_type == enums.FinancialEventType.INCOME_EXPENSE and event.from_account_id in context.account_balances:
                if event.value > 0:
                     headroom = _get_contribution_headroom(context, event.from_account_id, scenario.tax_limits)
                     if headroom < event.value:
                         context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=event.from_account_id, message=f"Tax Limit: Event '{event.name}' exceeds allowance.", source_type="event", source_id=event.id))
                     _track_contribution(context, event.from_account_id, event.value)
                context.account_balances[event.from_account_id] += event.value
                context.account_book_costs[event.from_account_id] += event.value 
                context.flows[event.from_account_id]["events"] += event.value / 100.0
            elif event.event_type == enums.FinancialEventType.TRANSFER and event.from_account_id in context.account_balances and event.to_account_id in context.account_balances:
                headroom = _get_contribution_headroom(context, event.to_account_id, scenario.tax_limits)
                if headroom < event.value:
                     context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=event.to_account_id, message=f"Tax Limit: Transfer Event '{event.name}' exceeds allowance.", source_type="event", source_id=event.id))
                from_acc = next((a for a in context.all_accounts if a.id == event.from_account_id), None)
                cgt_tax = 0; cost_portion = event.value 
                if from_acc:
                    cost_portion, gain = _calculate_disposal_impact(event.value, context.account_balances[event.from_account_id], context.account_book_costs[event.from_account_id], from_acc.account_type, from_acc.tax_wrapper)
                    if gain > 0:
                        owner_id = from_acc.owners[0].id if from_acc.owners else 0
                        if owner_id not in context.ytd_gains: context.ytd_gains[owner_id] = 0
                        earnings = context.ytd_earnings.get(owner_id, {}).get('taxable', 0)
                        cgt_tax = TaxService.calculate_capital_gains_tax(gain, context.ytd_gains[owner_id], earnings)
                        context.ytd_gains[owner_id] += gain
                context.account_balances[event.from_account_id] -= event.value
                context.account_book_costs[event.from_account_id] -= cost_portion 
                context.flows[event.from_account_id]["transfers_out"] += event.value / 100.0
                context.flows[event.from_account_id]["cgt"] += cgt_tax / 100.0
                net_received = event.value - cgt_tax
                context.account_balances[event.to_account_id] += net_received
                context.account_book_costs[event.to_account_id] += net_received
                context.flows[event.to_account_id]["transfers_in"] += net_received / 100.0
                _track_contribution(context, event.to_account_id, net_received)

def _process_rsu_vesting(scenario: models.Scenario, context: ProjectionContext):
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
            headroom = _get_contribution_headroom(context, target_id, scenario.tax_limits)
            if headroom < net_gbp:
                context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=target_id, message=f"Tax Limit: RSU Vest exceeds allowance.", source_type="rsu_vest", source_id=acc.id))
            context.account_balances[target_id] += net_gbp
            context.account_book_costs[target_id] += net_gbp 
            context.flows[target_id]["transfers_in"] += net_gbp / 100.0
            context.flows[target_id]["tax"] += tax / 100.0 
            _track_contribution(context, target_id, net_gbp)
            src_name = acc.name
            tgt_name = next((a.name for a in context.all_accounts if a.id == target_id), "Target")
            context.rule_logs.append(schemas.RuleExecutionLog(date=context.month_start, rule_type="RSU Vest", action=f"Vested {monthly_units/100} units", amount=net_gbp / 100.0, source_account=src_name, target_account=tgt_name, reason=f"Tax: {utils.format_currency(tax)}"))

def _process_rules(scenario: models.Scenario, context: ProjectionContext):
    seen_ids = set(); unique_rules = []
    for r in scenario.automation_rules:
        if r.id not in seen_ids: unique_rules.append(r); seen_ids.add(r.id)
    sorted_rules = sorted(unique_rules, key=lambda r: r.priority)
    for rule in sorted_rules:
        if rule.start_date and context.month_start < rule.start_date.replace(day=1): continue
        if rule.end_date and context.month_start > rule.end_date: continue
        should_run = False
        if rule.cadence.value == 'once':
            if rule.start_date and context.month_start.year == rule.start_date.year and context.month_start.month == rule.start_date.month: should_run = True
        elif rule.cadence.value == 'monthly': should_run = True
        elif rule.cadence.value == 'quarterly' and context.month_start.month in [1, 4, 7, 10]: should_run = True
        elif rule.cadence.value == 'annually' and context.month_start.month == 1: should_run = True 
        if not should_run: continue
        source_id = rule.source_account_id; target_id = rule.target_account_id
        if source_id not in context.account_balances: continue
        source_bal = context.account_balances[source_id]
        target_bal = context.account_balances.get(target_id, 0)
        source_acc = next((a for a in context.all_accounts if a.id == source_id), None)
        if source_acc and source_acc.account_type == enums.AccountType.RSU_GRANT: continue
        
        trigger_pence = int(rule.trigger_value)
        
        transfer_amount = 0; reason = ""
        if rule.rule_type == enums.RuleType.SWEEP:
            if source_bal > trigger_pence: transfer_amount = source_bal - trigger_pence; reason = f"Sweep"
        elif rule.rule_type == enums.RuleType.TOP_UP and target_id:
            if target_bal < trigger_pence: deficit = trigger_pence - target_bal; transfer_amount = min(deficit, source_bal) if source_bal > 0 else 0; reason = f"Top-Up"
        elif rule.rule_type == enums.RuleType.SMART_TRANSFER:
            fixed_val = int(rule.transfer_value or 0)
            if source_bal >= (trigger_pence + fixed_val): transfer_amount = fixed_val; reason = f"Smart Transfer"
            else: reason = "Skipped: Low Funds"
        elif rule.rule_type == enums.RuleType.MORTGAGE_SMART and target_id:
             if target_id in context.account_balances and context.account_balances[target_id] < 0:
                mortgage_bal = abs(context.account_balances[target_id]); percentage = rule.transfer_value or 10.0; state_key = f"rule_{rule.id}"
                if state_key not in context.mortgage_state: context.mortgage_state[state_key] = {"allowance": 0, "paid": 0}
                rule_month = rule.start_date.month if rule.start_date else 1
                if context.month_start.month == rule_month:
                    if state_key in context.mortgage_state:
                        prev = context.mortgage_state[state_key]
                        if prev["allowance"] > 0: context.mortgage_stats.append(schemas.MortgageStat(year_start=context.month_start.year - 1, rule_id=rule.id, rule_name=rule.name or "Overpayment Rule", allowance=prev["allowance"] / 100.0, paid=prev["paid"] / 100.0, headroom=(prev["allowance"] - prev["paid"]) / 100.0))
                    allowance = int(mortgage_bal * (percentage / 100.0)); context.mortgage_state[state_key] = {"allowance": allowance, "paid": 0}
                state = context.mortgage_state[state_key]; remaining = state["allowance"] - state["paid"]
                months_until = (rule_month - context.month_start.month) % 12; 
                if months_until == 0: months_until = 12
                if remaining > 0:
                    monthly_slice = int(remaining / months_until)
                    if source_bal >= (trigger_pence + monthly_slice):
                        transfer_amount = monthly_slice; current_debt = abs(context.account_balances[target_id])
                        if transfer_amount > current_debt: transfer_amount = current_debt
                        context.mortgage_state[state_key]["paid"] += transfer_amount; reason = f"Smart Smooth"
                    else: reason = "Skipped: Low Funds"
        if target_id and transfer_amount > 0:
            headroom = _get_contribution_headroom(context, target_id, scenario.tax_limits)
            if headroom < 999999999999:
                if headroom <= 0: transfer_amount = 0; reason = f"Skipped: Tax Limit Reached"; context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=target_id, message=f"Tax Limit: Rule '{rule.name}' skipped.", source_type="rule", source_id=rule.id))
                elif transfer_amount > headroom: transfer_amount = headroom; reason += f" (Trimmed)"; context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=target_id, message=f"Tax Limit: Rule '{rule.name}' trimmed.", source_type="rule", source_id=rule.id))
        if transfer_amount > 0:
            cgt_tax = 0
            if source_acc:
                cost_portion, gain = _calculate_disposal_impact(transfer_amount, source_bal, context.account_book_costs[source_id], source_acc.account_type, source_acc.tax_wrapper)
                if gain > 0:
                    owner_id = source_acc.owners[0].id if source_acc.owners else 0
                    if owner_id not in context.ytd_gains: context.ytd_gains[owner_id] = 0
                    earnings = context.ytd_earnings.get(owner_id, {}).get('taxable', 0)
                    cgt_tax = TaxService.calculate_capital_gains_tax(gain, context.ytd_gains[owner_id], earnings)
                    context.ytd_gains[owner_id] += gain
                context.account_book_costs[source_id] -= cost_portion
            context.account_balances[source_id] -= transfer_amount
            context.flows[source_id]["transfers_out"] += transfer_amount / 100.0
            context.flows[source_id]["cgt"] += cgt_tax / 100.0
            target_name = "External"
            if target_id and target_id in context.account_balances:
                net_received = transfer_amount - cgt_tax
                context.account_balances[target_id] += net_received
                context.account_book_costs[target_id] += net_received
                context.flows[target_id]["transfers_in"] += net_received / 100.0
                _track_contribution(context, target_id, net_received)
                acc = next((a for a in scenario.accounts if a.id == target_id), None)
                if acc: target_name = acc.name
                if acc and acc.account_type == enums.AccountType.MORTGAGE: context.flows[target_id]["mortgage_repayments_in"] += net_received / 100.0
            else: context.flows[source_id]["events"] += transfer_amount / 100.0 
            src_name = next((a.name for a in scenario.accounts if a.id == source_id), "?")
            context.rule_logs.append(schemas.RuleExecutionLog(date=context.month_start, rule_type=rule.rule_type.value, action=f"Moved {utils.format_currency(transfer_amount)}", amount=transfer_amount / 100.0, source_account=src_name, target_account=target_name, reason=reason))

def _process_standard_mortgage_payments(scenario: models.Scenario, context: ProjectionContext):
    for acc in context.all_accounts:
        if acc.account_type == enums.AccountType.MORTGAGE and context.account_balances[acc.id] < 0:
            safe_interest_rate = acc.interest_rate or 0.0
            is_fixed_period = False
            if acc.mortgage_start_date and acc.fixed_rate_period_years and acc.fixed_interest_rate is not None:
                fixed_end_date = acc.mortgage_start_date + relativedelta(years=acc.fixed_rate_period_years)
                if context.month_start < fixed_end_date: safe_interest_rate = acc.fixed_interest_rate; is_fixed_period = True
            monthly_repayment = 0
            if acc.original_loan_amount and acc.amortisation_period_years:
                if is_fixed_period: monthly_repayment = utils.calculate_mortgage_payment(acc.original_loan_amount, safe_interest_rate, acc.amortisation_period_years)
                elif acc.mortgage_start_date:
                    loan_end_date = acc.mortgage_start_date + relativedelta(years=acc.amortisation_period_years)
                    delta = relativedelta(loan_end_date, context.month_start); remaining_months = delta.years * 12 + delta.months
                    if remaining_months > 0:
                        monthly_rate = safe_interest_rate / 100 / 12
                        if monthly_rate > 0: numerator = monthly_rate * abs(context.account_balances[acc.id]); denominator = 1 - (1 + monthly_rate) ** (-remaining_months); monthly_repayment = round(numerator / denominator)
                        else: monthly_repayment = round(abs(context.account_balances[acc.id]) / remaining_months)
                    else: monthly_repayment = abs(context.account_balances[acc.id])
                else: monthly_repayment = utils.calculate_mortgage_payment(acc.original_loan_amount, safe_interest_rate, acc.amortisation_period_years)
            if monthly_repayment > 0:
                if (context.account_balances[acc.id] + monthly_repayment) > 0: monthly_repayment = abs(context.account_balances[acc.id])
                payment_account_id = acc.payment_from_account_id
                if payment_account_id and payment_account_id in context.account_balances:
                    context.account_balances[payment_account_id] -= monthly_repayment; context.flows[payment_account_id]["mortgage_payments_out"] += monthly_repayment / 100.0
                context.account_balances[acc.id] += monthly_repayment; context.flows[acc.id]["mortgage_repayments_in"] += monthly_repayment / 100.0

def _process_interest(scenario: models.Scenario, context: ProjectionContext):
    for acc in context.all_accounts:
        if acc.account_type == enums.AccountType.MORTGAGE and context.account_balances[acc.id] < 0:
            safe_interest_rate = acc.interest_rate or 0.0
            if acc.mortgage_start_date and acc.fixed_rate_period_years and acc.fixed_interest_rate is not None:
                fixed_end_date = acc.mortgage_start_date + relativedelta(years=acc.fixed_rate_period_years)
                if context.month_start < fixed_end_date: safe_interest_rate = acc.fixed_interest_rate
            monthly_rate = safe_interest_rate / 100 / 12; interest_charged = abs(context.account_balances[acc.id]) * monthly_rate
            context.account_balances[acc.id] -= round(interest_charged); context.flows[acc.id]["interest"] -= round(interest_charged) / 100.0
        elif acc.account_type == enums.AccountType.RSU_GRANT: pass
        elif acc.account_type != enums.AccountType.MORTGAGE:
            safe_interest_rate = acc.interest_rate or 0.0
            if safe_interest_rate != 0:
                monthly_rate = safe_interest_rate / 100 / 12; interest_gross = context.account_balances[acc.id] * monthly_rate; interest_gross_int = round(interest_gross)
                tax_deducted = 0
                
                # TAX LOGIC: 
                # 1. Wrappers (ISA/Pension) -> No Monthly Tax
                # 2. Property / Main Residence -> No Monthly Tax (It's Capital Growth)
                # 3. Cash/Investment -> Monthly Tax applies
                
                is_taxable = (not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.NONE)
                is_real_property = (acc.account_type in [enums.AccountType.PROPERTY, enums.AccountType.MAIN_RESIDENCE])

                if interest_gross_int > 0 and is_taxable and not is_real_property:
                    owner_id = acc.owners[0].id if acc.owners else 0
                    earnings = context.ytd_earnings.get(owner_id, {}).get('taxable', 0)
                    prior_interest = context.ytd_interest.get(owner_id, 0)
                    tax_deducted = TaxService.calculate_savings_tax(interest_gross_int, earnings + prior_interest, prior_interest)
                    if owner_id not in context.ytd_interest: context.ytd_interest[owner_id] = 0
                    context.ytd_interest[owner_id] += interest_gross_int
                
                interest_net_int = interest_gross_int - tax_deducted
                context.account_balances[acc.id] += interest_net_int; context.flows[acc.id]["interest"] += interest_gross_int / 100.0; context.flows[acc.id]["tax"] += tax_deducted / 100.0

def _detect_milestones(context: ProjectionContext):
    # 1. Debt Freedom - Individual
    for acc in context.all_accounts:
        if acc.account_type in [enums.AccountType.MORTGAGE, enums.AccountType.LOAN]:
            curr = context.account_balances[acc.id]
            prev = context.prev_balances.get(acc.id, acc.starting_balance)
            
            # Check for IMMEDIATE Crossover (Month 0)
            if context.month_start == context.all_accounts[0].scenario.start_date: 
                 if curr >= 0 and prev < 0: # Only if it was debt initially
                     context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label=f"Paid Off: {acc.name}", type="milestone"))
            
            # Normal Crossover
            if prev < 0 and curr >= 0:
                # Don't double count if it was immediate
                if context.month_start != context.all_accounts[0].scenario.start_date:
                    context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label=f"Paid Off: {acc.name}", type="milestone"))

    # 2. RSU Cleared
    for acc in context.all_accounts:
        if acc.account_type == enums.AccountType.RSU_GRANT:
            curr = context.account_balances[acc.id]
            prev = context.prev_balances.get(acc.id, acc.starting_balance)
            if prev > 0 and curr <= 0:
                context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label=f"Vested: {acc.name}", type="milestone"))

    # 3. Liquid vs Liabilities Crossover (Insolvency Flip)
    curr_liquid = 0; curr_debt = 0; prev_liquid = 0; prev_debt = 0
    for acc in context.all_accounts:
        curr_bal = context.account_balances[acc.id]
        prev_bal = context.prev_balances.get(acc.id, acc.starting_balance)
        
        # Only count CASH and INVESTMENT as "Liquid"
        # Explicitly Exclude PENSION, PROPERTY, MAIN_RESIDENCE, RSU_GRANT
        if acc.account_type in [enums.AccountType.CASH, enums.AccountType.INVESTMENT]:
            
            # FIX: Pension wrappers are NOT liquid, even if Type is Investment/Cash
            if acc.tax_wrapper == enums.TaxWrapper.PENSION:
                continue

            if curr_bal > 0: curr_liquid += curr_bal
            if prev_bal > 0: prev_liquid += prev_bal
        elif acc.account_type in [enums.AccountType.MORTGAGE, enums.AccountType.LOAN]:
            if curr_bal < 0: curr_debt += abs(curr_bal)
            if prev_bal < 0: prev_debt += abs(prev_bal)
    
    # Milestone: Liquid Assets exceed Total Debt for the first time
    # Check prev_debt > 0 to ensure we actually *had* debt to clear
    if prev_liquid < prev_debt and curr_liquid >= curr_debt and prev_debt > 0:
         context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label="Liquid assets exceed liabilities", type="milestone"))

def apply_simulation_overrides(scenario: models.Scenario, overrides: List[schemas.SimulationOverride]):
    for override in overrides:
        if override.type == 'account':
            acc = next((a for a in scenario.accounts if a.id == override.id), None)
            if acc and hasattr(acc, override.field): setattr(acc, override.field, override.value)
        elif override.type == 'income':
            for owner in scenario.owners:
                inc = next((i for i in owner.income_sources if i.id == override.id), None)
                if inc and hasattr(inc, override.field): setattr(inc, override.field, override.value)
        elif override.type == 'cost':
            cost = next((c for c in scenario.costs if c.id == override.id), None)
            if cost and hasattr(cost, override.field): setattr(cost, override.field, override.value)
        elif override.type == 'transfer':
            trans = next((t for t in scenario.transfers if t.id == override.id), None)
            if trans and hasattr(trans, override.field): setattr(trans, override.field, override.value)
        elif override.type == 'event':
            evt = next((e for e in scenario.financial_events if e.id == override.id), None)
            if evt and hasattr(evt, override.field): setattr(evt, override.field, override.value)
        elif override.type == 'tax_limit':
            limit = next((t for t in scenario.tax_limits if t.id == override.id), None)
            if limit and hasattr(limit, override.field): setattr(limit, override.field, override.value)
        elif override.type == 'rule':
            rule = next((r for r in scenario.automation_rules if r.id == override.id), None)
            if rule and hasattr(rule, override.field): setattr(rule, override.field, override.value)

def run_projection(db: Session, scenario: models.Scenario, months: int) -> schemas.Projection:
    all_accounts = scenario.accounts
    if not all_accounts: return schemas.Projection(data_points=[])
    start_date: date = scenario.start_date
    initial_balances = {acc.id: acc.starting_balance for acc in all_accounts}
    initial_costs = {acc.id: (acc.book_cost if acc.book_cost is not None else acc.starting_balance) for acc in all_accounts}
    
    # Collect manual annotations
    context = ProjectionContext(month_start=start_date, account_balances=initial_balances, account_book_costs=initial_costs, flows={}, all_accounts=all_accounts)
    for ann in scenario.chart_annotations:
        context.annotations.append(schemas.ProjectionAnnotation(date=ann.date, label=ann.label, type=ann.annotation_type))

    initial_breakdown, initial_total = _calculate_gbp_balances(context.account_balances, all_accounts, scenario.gbp_to_usd_rate, start_date)
    data_points = []
    data_points.append(schemas.ProjectionDataPoint(date=start_date, balance=initial_total, account_balances=initial_breakdown, flows={}))
    projection_anchor = start_date.replace(day=1)
    current_fy = utils.get_uk_fiscal_year(start_date)
    
    for i in range(months):
        context.prev_balances = context.account_balances.copy()
        projection_month_start = projection_anchor + relativedelta(months=i)
        context.month_start = projection_month_start
        new_fy = utils.get_uk_fiscal_year(projection_month_start)
        if new_fy != current_fy: context.ytd_contributions = {}; context.ytd_earnings = {}; context.ytd_interest = {}; context.ytd_gains = {}; current_fy = new_fy
        context.flows = {acc.id: {"income": 0, "costs": 0, "transfers_in": 0, "transfers_out": 0, "mortgage_payments_out": 0, "mortgage_repayments_in": 0, "interest": 0, "events": 0, "tax": 0, "cgt": 0, "employer_contribution": 0} for acc in all_accounts}
        _process_income(scenario, context)
        _process_costs(scenario, context)
        _process_transfers(scenario, context)
        _process_events(scenario, context)
        _process_rsu_vesting(scenario, context)
        _process_standard_mortgage_payments(scenario, context)
        _process_rules(scenario, context)
        _process_interest(scenario, context)
        
        _detect_milestones(context)

        current_breakdown, current_total = _calculate_gbp_balances(context.account_balances, all_accounts, scenario.gbp_to_usd_rate, projection_month_start)
        end_of_month = projection_month_start + relativedelta(months=1, days=-1)
        flows_for_schema = {acc_id: schemas.ProjectionFlows(**flow_data) for acc_id, flow_data in context.flows.items()}
        data_points.append(schemas.ProjectionDataPoint(date=end_of_month, balance=current_total, account_balances=current_breakdown, flows=flows_for_schema))
        
        # NEGATIVE BALANCE CHECK
        for acc in all_accounts:
            if acc.account_type == enums.AccountType.CASH or acc.account_type == enums.AccountType.INVESTMENT:
                current_bal = context.account_balances[acc.id]
                min_bal = acc.min_balance or 0
                if current_bal < min_bal:
                    context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=acc.id, message=f"Negative Balance: {acc.name} is overdrawn ({utils.format_currency(current_bal)}).", source_type="balance", source_id=acc.id))

    unique_warnings = []
    seen_warnings = set() 
    for w in context.warnings:
        year = w.date.year
        if w.source_type == "balance": key = (year, w.account_id, "balance")
        elif w.source_type in ["income", "transfer", "event", "rsu_vest"]: key = (year, w.source_type, w.source_id, w.account_id)
        else: key = (w.account_id, w.message)
        if key not in seen_warnings: unique_warnings.append(w); seen_warnings.add(key)
            
    return schemas.Projection(data_points=data_points, warnings=unique_warnings, rule_logs=context.rule_logs, mortgage_stats=context.mortgage_stats, annotations=context.annotations)
