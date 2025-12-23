from app import models, enums, utils, schemas
from app.engine.context import ProjectionContext
from app.engine.helpers import _get_enum_value, get_contribution_headroom, track_contribution, calculate_disposal_impact
from app.services.tax import TaxService

def process_rules(scenario: models.Scenario, context: ProjectionContext):
    seen_ids = set(); unique_rules = []
    for r in scenario.automation_rules:
        if r.id not in seen_ids: unique_rules.append(r); seen_ids.add(r.id)
    
    sorted_rules = sorted(unique_rules, key=lambda r: r.priority)
    
    for rule in sorted_rules:
        # Date checks
        if rule.start_date and context.month_start < rule.start_date.replace(day=1): continue
        if rule.end_date and context.month_start > rule.end_date: continue

        # Robust Cadence
        cadence_str = _get_enum_value(rule.cadence)
        should_run = False
        
        start_month = rule.start_date.month if rule.start_date else 1
        start_year = rule.start_date.year if rule.start_date else context.month_start.year # Default to current year if None? Or meaningless for 'once'?

        if cadence_str == 'once':
            if rule.start_date and context.month_start.year == start_year and context.month_start.month == start_month: should_run = True
        elif cadence_str == 'monthly': should_run = True
        elif cadence_str == 'quarterly' and context.month_start.month in [1, 4, 7, 10]: should_run = True
        elif cadence_str == 'annually' and context.month_start.month == start_month: should_run = True 
        
        if not should_run: continue

        source_id = rule.source_account_id
        target_id = rule.target_account_id
        
        if source_id not in context.account_balances: continue
        
        source_bal = context.account_balances[source_id]
        target_bal = context.account_balances.get(target_id, 0)
        source_acc = next((a for a in context.all_accounts if a.id == source_id), None)
        
        # Robust Rule Type
        rule_type_str = _get_enum_value(rule.rule_type)
        trigger_pence = int(rule.trigger_value)
        
        transfer_amount = 0
        reason = ""

        if rule_type_str == 'sweep':
            if source_bal > trigger_pence:
                transfer_amount = source_bal - trigger_pence
                reason = "Sweep"
        elif rule_type_str == 'top_up' and target_id:
            if target_bal < trigger_pence:
                deficit = trigger_pence - target_bal
                transfer_amount = min(deficit, source_bal) if source_bal > 0 else 0
                reason = "Top-Up"
        elif rule_type_str == 'transfer': # Smart Transfer
            fixed_val = int(rule.transfer_value or 0)
            if source_bal >= (trigger_pence + fixed_val):
                transfer_amount = fixed_val
                reason = "Smart Transfer"
            else:
                reason = "Skipped: Low Funds"
        elif rule_type_str == 'mortgage_smart' and target_id:
             if target_id in context.account_balances and context.account_balances[target_id] < 0:
                mortgage_bal = abs(context.account_balances[target_id])
                percentage = rule.transfer_value or 10.0
                state_key = f"rule_{rule.id}"
                
                # Init Mortgage Rule State
                if state_key not in context.mortgage_state:
                    context.mortgage_state[state_key] = {"allowance": 0, "paid": 0}
                
                rule_month = rule.start_date.month if rule.start_date else 1
                
                # Annual Reset of Allowance
                if context.month_start.month == rule_month:
                    if state_key in context.mortgage_state:
                        prev = context.mortgage_state[state_key]
                        if prev["allowance"] > 0:
                            context.mortgage_stats.append(schemas.MortgageStat(
                                year_start=context.month_start.year - 1, 
                                rule_id=rule.id, 
                                rule_name=rule.name or "Overpayment Rule", 
                                allowance=prev["allowance"], 
                                paid=prev["paid"], 
                                headroom=(prev["allowance"] - prev["paid"])
                            ))
                    allowance = int(mortgage_bal * (percentage / 100.0))
                    context.mortgage_state[state_key] = {"allowance": allowance, "paid": 0}

                state = context.mortgage_state[state_key]
                remaining = state["allowance"] - state["paid"]
                
                months_until = (rule_month - context.month_start.month) % 12
                if months_until == 0: months_until = 12
                
                if remaining > 0:
                    monthly_slice = int(remaining / months_until)
                    if source_bal >= (trigger_pence + monthly_slice):
                        transfer_amount = monthly_slice
                        current_debt = abs(context.account_balances[target_id])
                        if transfer_amount > current_debt: transfer_amount = current_debt
                        
                        context.mortgage_state[state_key]["paid"] += transfer_amount
                        reason = "Smart Smooth"
                    else:
                        reason = "Skipped: Low Funds"

        # Execute Transfer
        if target_id and transfer_amount > 0:
            headroom = get_contribution_headroom(context, target_id, scenario.tax_limits)
            if headroom < 999999999999:
                if headroom <= 0:
                    transfer_amount = 0
                    reason = "Skipped: Tax Limit Reached"
                    context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=target_id, message=f"Tax Limit: Rule '{rule.name}' skipped.", source_type="rule", source_id=rule.id))
                elif transfer_amount > headroom:
                    transfer_amount = headroom
                    reason += " (Trimmed)"
                    context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=target_id, message=f"Tax Limit: Rule '{rule.name}' trimmed.", source_type="rule", source_id=rule.id))

        if transfer_amount > 0:
            cgt_tax = 0
            if source_acc:
                cost_portion, gain = calculate_disposal_impact(transfer_amount, source_bal, context.account_book_costs[source_id], source_acc.account_type, source_acc.tax_wrapper)
                
                if gain > 0 and source_acc.owners:
                    num_owners = len(source_acc.owners)
                    gain_per_owner = int(gain / num_owners)
                    total_cgt = 0
                    for owner in source_acc.owners:
                        if owner.id not in context.ytd_gains: context.ytd_gains[owner.id] = 0
                        earnings = context.ytd_earnings.get(owner.id, {}).get('taxable', 0)
                        tax_val = TaxService.calculate_capital_gains_tax(gain_per_owner, context.ytd_gains[owner.id], earnings)
                        context.ytd_gains[owner.id] += gain_per_owner
                        total_cgt += tax_val
                    cgt_tax = total_cgt
                
                context.account_book_costs[source_id] -= cost_portion

            # Perform Move
            context.account_balances[source_id] -= transfer_amount
            context.flows[source_id]["transfers_out"] += transfer_amount
            context.flows[source_id]["cgt"] += cgt_tax
            
            target_name = "External"
            if target_id and target_id in context.account_balances:
                net_received = transfer_amount - cgt_tax
                context.account_balances[target_id] += net_received
                context.account_book_costs[target_id] += net_received
                
                context.flows[target_id]["transfers_in"] += net_received
                track_contribution(context, target_id, net_received)
                
                acc = next((a for a in scenario.accounts if a.id == target_id), None)
                if acc: target_name = acc.name
                if acc and _get_enum_value(acc.account_type) == "Mortgage":
                    context.flows[target_id]["mortgage_repayments_in"] += net_received
            else:
                 context.flows[source_id]["events"] += transfer_amount
                 
            src_name = next((a.name for a in scenario.accounts if a.id == source_id), "?")
            context.rule_logs.append(schemas.RuleExecutionLog(date=context.month_start, rule_type=rule_type_str, action=f"Moved {utils.format_currency(transfer_amount)}", amount=int(transfer_amount), source_account=src_name, target_account=target_name, reason=reason))
