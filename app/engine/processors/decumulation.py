from app import models, enums, schemas, utils
from app.engine.context import ProjectionContext
from app.engine.tax_logic import track_contribution, calculate_disposal_impact, validate_pension_access
from typing import List

def process_decumulation(scenario: models.Scenario, context: ProjectionContext):
    """
    1. Identify active strategy for this month.
    2. Check for Cash Accounts with balance < min_balance (Deficit).
    3. If Deficit exists, sweep funds from Assets (Cash > GIA > ISA > Pension).
    """
    
    # 1. Find Active Strategy
    active_strategy = None
    if scenario.decumulation_strategies:
        for s in scenario.decumulation_strategies:
            start = s.start_date or scenario.start_date
            end = s.end_date
            if context.month_start >= start and (end is None or context.month_start <= end):
                active_strategy = s
                break
    
    # For now, if no strategy is explicitly defined, we do NOTHING.
    # User must enable "Automated Decumulation" via a strategy record.
    if not active_strategy:
        return 

    # 2. Identify Deficit
    deficit_accounts = []
    total_deficit = 0
    
    for acc in context.all_accounts:
        # Check Cash-like accounts (Using CASH as CURRENT doesn't exist in enum yet)
        if acc.account_type == enums.AccountType.CASH:
            current_bal = context.account_balances[acc.id]
            min_bal = acc.min_balance or 0
            if current_bal < min_bal:
                shortfall = min_bal - current_bal
                deficit_accounts.append({'id': acc.id, 'amount': shortfall})
                total_deficit += shortfall

    if total_deficit <= 0:
        return

    # 3. Identify Source Assets (Prioritized)
    # Priority: Cash Surplus > GIA > ISA > Pension
    # We gather all candidate accounts and sort them.
    
    candidates = []
    for acc in context.all_accounts:
        bal = context.account_balances[acc.id]
        if bal <= 0: continue
        
        # Don't withdraw from the deficit account itself
        if any(d['id'] == acc.id for d in deficit_accounts): continue

        priority = 99
        
        # Priority 1: Excess Cash
        if acc.account_type == enums.AccountType.CASH:
            # Only use amount ABOVE min_balance
            available = bal - (acc.min_balance or 0)
            if available > 0:
                candidates.append({'acc': acc, 'available': available, 'priority': 1})
        
        # Priority 2: GIA (General Investment)
        elif acc.account_type == enums.AccountType.INVESTMENT and (not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.GIA or acc.tax_wrapper == enums.TaxWrapper.NONE):
            candidates.append({'acc': acc, 'available': bal, 'priority': 2})
            
        # Priority 3: ISA
        elif acc.tax_wrapper == enums.TaxWrapper.ISA:
            candidates.append({'acc': acc, 'available': bal, 'priority': 3})
            
        # Priority 4: Pension (Check Age Lock)
        elif acc.tax_wrapper == enums.TaxWrapper.PENSION:
            # Check age lock
            if not validate_pension_access(context, acc.id):
                candidates.append({'acc': acc, 'available': bal, 'priority': 4})

    # Sort by priority
    candidates.sort(key=lambda x: x['priority'])

    # 4. Execute Transfers (Fill the hole)
    # We fill accounts one by one.
    
    for deficit_record in deficit_accounts:
        needed = deficit_record['amount']
        target_id = deficit_record['id']
        
        if needed <= 0: continue
        
        for source in candidates:
            if needed <= 0: break
            if source['available'] <= 0: continue
            
            take = min(needed, source['available'])
            
            # Execute Move
            # a) Withdraw from Source
            source_acc = source['acc']
            
            # Calculate Tax/Cost Basis
            cgt_tax = 0
            cost_portion, gain = calculate_disposal_impact(take, context.account_balances[source_acc.id], context.account_book_costs[source_acc.id], source_acc.account_type, source_acc.tax_wrapper)
            
            # (Note: We track CGT here but don't apply full tax logic for GIA yet, just tracking basic cost basis reduction)
            
            context.account_balances[source_acc.id] -= take
            context.account_book_costs[source_acc.id] -= cost_portion
            context.flows[source_acc.id]["transfers_out"] += take / 100.0
            
            # Update local availability tracker
            source['available'] -= take
            
            # b) Deposit to Target
            net_received = take # Assume no tax deducted at source for simple transfers currently (except maybe future pension tax)
            context.account_balances[target_id] += net_received
            context.account_book_costs[target_id] += net_received
            context.flows[target_id]["transfers_in"] += net_received / 100.0
            
            # Log
            context.rule_logs.append(schemas.RuleExecutionLog(
                date=context.month_start, 
                rule_type="Decumulation", 
                action=f"Sold {utils.format_currency(take)}", 
                amount=take/100.0, 
                source_account=source_acc.name, 
                target_account="Deficit", 
                reason="Cover Shortfall"
            ))
            
            needed -= take
