from app import models, enums, schemas, utils
from app.services.tax import TaxService
from app.engine.context import ProjectionContext
from app.engine.tax_logic import track_contribution, get_contribution_headroom, calculate_disposal_impact

def process_rules(scenario: models.Scenario, context: ProjectionContext):
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
            headroom = get_contribution_headroom(context, target_id, scenario.tax_limits)
            if headroom < 999999999999:
                if headroom <= 0: transfer_amount = 0; reason = f"Skipped: Tax Limit Reached"; context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=target_id, message=f"Tax Limit: Rule '{rule.name}' skipped.", source_type="rule", source_id=rule.id))
                elif transfer_amount > headroom: transfer_amount = headroom; reason += f" (Trimmed)"; context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=target_id, message=f"Tax Limit: Rule '{rule.name}' trimmed.", source_type="rule", source_id=rule.id))
        if transfer_amount > 0:
            cgt_tax = 0
            if source_acc:
                cost_portion, gain = calculate_disposal_impact(transfer_amount, source_bal, context.account_book_costs[source_id], source_acc.account_type, source_acc.tax_wrapper)
                
                # SPLIT GAIN LOGIC
                if gain > 0 and source_acc.owners:
                    num_owners = len(source_acc.owners)
                    gain_per_owner = int(gain / num_owners)
                    total_cgt = 0
                    for owner in source_acc.owners:
                        if owner.id not in context.ytd_gains: context.ytd_gains[owner.id] = 0
                        earnings = context.ytd_earnings.get(owner.id, {}).get('taxable', 0)
                        cgt_tax = TaxService.calculate_capital_gains_tax(gain_per_owner, context.ytd_gains[owner.id], earnings)
                        context.ytd_gains[owner.id] += gain_per_owner
                        total_cgt += cgt_tax
                    cgt_tax = total_cgt

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
                track_contribution(context, target_id, net_received)
                acc = next((a for a in scenario.accounts if a.id == target_id), None)
                if acc: target_name = acc.name
                if acc and acc.account_type == enums.AccountType.MORTGAGE: context.flows[target_id]["mortgage_repayments_in"] += net_received / 100.0
            else: context.flows[source_id]["events"] += transfer_amount / 100.0 
            src_name = next((a.name for a in scenario.accounts if a.id == source_id), "?")
            context.rule_logs.append(schemas.RuleExecutionLog(date=context.month_start, rule_type=rule.rule_type.value, action=f"Moved {utils.format_currency(transfer_amount)}", amount=transfer_amount / 100.0, source_account=src_name, target_account=target_name, reason=reason))
