from app import models, enums, schemas
try:
    from app import utils
except ImportError:
    utils = None

from app.engine.context import ProjectionContext
from app.engine.tax_logic import calculate_disposal_impact, validate_pension_access
import logging

def process_decumulation(scenario: models.Scenario, context: ProjectionContext):
    # 1. Find Active Strategy
    active_strategy = None
    if scenario.decumulation_strategies:
        for s in scenario.decumulation_strategies:
            if not s.enabled: continue
            start = s.start_date or scenario.start_date
            end = s.end_date
            if context.month_start >= start and (end is None or context.month_start <= end):
                active_strategy = s
                break
    
    if not active_strategy: return 

    # 2. Identify Deficit
    deficit_accounts = []
    total_deficit = 0
    
    for acc in context.all_accounts:
        if acc.account_type == enums.AccountType.CASH:
            current_bal = context.account_balances[acc.id]
            min_bal = acc.min_balance or 0
            if current_bal < min_bal:
                shortfall = min_bal - current_bal
                if shortfall > 100000000: continue # Safety cap
                deficit_accounts.append({'id': acc.id, 'amount': shortfall})
                total_deficit += shortfall

    if total_deficit <= 0: return

    # 3. Identify Sources
    candidates = []
    for acc in context.all_accounts:
        bal = context.account_balances[acc.id]
        if bal <= 0: continue
        if any(d['id'] == acc.id for d in deficit_accounts): continue 

        priority = 99
        if acc.account_type == enums.AccountType.CASH:
            available = bal - (acc.min_balance or 0)
            if available > 0:
                candidates.append({'acc': acc, 'available': available, 'priority': 1})
        elif acc.account_type == enums.AccountType.INVESTMENT and (not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.GIA or acc.tax_wrapper == enums.TaxWrapper.NONE):
            candidates.append({'acc': acc, 'available': bal, 'priority': 2})
        elif acc.tax_wrapper == enums.TaxWrapper.ISA:
            candidates.append({'acc': acc, 'available': bal, 'priority': 3})
        elif acc.tax_wrapper == enums.TaxWrapper.PENSION:
            if validate_pension_access(context, acc.id):
                candidates.append({'acc': acc, 'available': bal, 'priority': 4})

    candidates.sort(key=lambda x: x['priority'])

    # 4. Execute
    for deficit_record in deficit_accounts:
        needed = deficit_record['amount']
        target_id = deficit_record['id']
        
        if needed <= 0: continue
        
        for source in candidates:
            if needed <= 0: break
            if source['available'] <= 0: continue
            
            take = min(needed, source['available'])
            
            # Move Money
            source_acc = source['acc']
            cost_portion, gain = calculate_disposal_impact(take, context.account_balances[source_acc.id], context.account_book_costs[source_acc.id], source_acc.account_type, source_acc.tax_wrapper)
            
            context.account_balances[source_acc.id] -= take
            context.account_book_costs[source_acc.id] -= cost_portion
            context.flows[source_acc.id]["transfers_out"] += take / 100.0
            
            source['available'] -= take
            
            context.account_balances[target_id] += take
            context.account_book_costs[target_id] += take
            context.flows[target_id]["transfers_in"] += take / 100.0
            
            # LOGGING DISABLED to prevent ERR_CONTENT_LENGTH_MISMATCH
            # Ideally we would log a summary, but for stability now, we skip it.
            needed -= take
