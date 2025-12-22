from app import models, enums, schemas
from app.engine.context import ProjectionContext
from app.services.tax import TaxService
from app.engine.tax_logic import calculate_disposal_impact, validate_pension_access
import logging

# Max iterations for the gross-up solver to prevent infinite loops
MAX_ITERATIONS = 10

def process_decumulation(scenario: models.Scenario, context: ProjectionContext):
    """
    Checks for cash deficits and sells assets to cover them based on the active strategy.
    """
    # 1. Check if Decumulation is Active
    active_strategy = None
    if scenario.decumulation_strategies:
        for s in scenario.decumulation_strategies:
            if not s.enabled: continue
            start = s.start_date or scenario.start_date
            end = s.end_date
            if context.month_start >= start and (end is None or context.month_start <= end):
                active_strategy = s
                break
    
    # If no strategy is active, we do nothing
    if not active_strategy: return 

    # 2. Identify Deficit (Total cash needed across all overdrawn cash accounts)
    deficit_accounts = []
    total_deficit = 0
    
    for acc in context.all_accounts:
        if acc.account_type == enums.AccountType.CASH:
            current_bal = context.account_balances[acc.id]
            min_bal = acc.min_balance or 0
            if current_bal < min_bal:
                shortfall = min_bal - current_bal
                # Safety Cap: Don't try to fill infinite holes
                if shortfall > 10000000: 
                    context.warnings.append(schemas.ProjectionWarning(
                        date=context.month_start, 
                        account_id=acc.id, 
                        message=f"Decumulation Safety: Deficit of {shortfall/100} is too large to auto-fill.", 
                        source_type="balance", 
                        source_id=acc.id
                    ))
                    continue 
                    
                deficit_accounts.append({'id': acc.id, 'amount': shortfall})
                total_deficit += shortfall

    if total_deficit <= 0: return

    # 3. Identify Candidate Sources
    candidates = []
    for acc in context.all_accounts:
        bal = context.account_balances.get(acc.id, 0)
        if bal <= 0: continue
        
        # Don't sell from the account that is in deficit
        if any(d['id'] == acc.id for d in deficit_accounts): continue 

        priority = 99
        
        # PRIORITY 1: General Investments (GIA) - Pay CGT first
        if acc.account_type == enums.AccountType.INVESTMENT and (not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.GIA or acc.tax_wrapper == enums.TaxWrapper.NONE):
            priority = 1
            
        # PRIORITY 2: ISAs - Tax Free
        elif acc.tax_wrapper == enums.TaxWrapper.ISA:
            priority = 2
            
        # PRIORITY 3: Pensions - Taxable Income
        elif acc.tax_wrapper == enums.TaxWrapper.PENSION:
            error = validate_pension_access(context, acc.id)
            if error:
                continue
            priority = 3
            
        if priority < 99:
            candidates.append({'acc': acc, 'available': bal, 'priority': priority})

    candidates.sort(key=lambda x: x['priority'])

    # 4. Fill the Deficits
    for deficit_record in deficit_accounts:
        needed_net = deficit_record['amount']
        target_id = deficit_record['id']
        
        # Helper to get target name for logging
        target_name = next((a.name for a in context.all_accounts if a.id == target_id), "Unknown Account")
        
        if needed_net <= 0: continue
        
        for source in candidates:
            if needed_net <= 0: break
            if source['available'] <= 0: continue
            
            source_acc = source['acc']
            
            # --- THE SOLVER ---
            gross_sell, tax_due, cgt_due = solve_gross_withdrawal(
                needed_net, 
                source_acc, 
                source['available'], 
                context, 
                scenario
            )
            
            if gross_sell == 0: continue 
            
            # Update Balances
            net_proceeds = gross_sell - tax_due - cgt_due
            
            # 1. Decrease Source
            context.account_balances[source_acc.id] -= gross_sell
            
            # Calculate Book Cost reduction
            cost_portion, _ = calculate_disposal_impact(
                gross_sell, 
                context.prev_balances.get(source_acc.id, source['available']),
                context.account_book_costs.get(source_acc.id, 0),
                source_acc.account_type,
                source_acc.tax_wrapper
            )
            context.account_book_costs[source_acc.id] -= cost_portion
            
            # Flows OUT
            context.flows[source_acc.id]["transfers_out"] += gross_sell / 100.0
            
            # 2. Increase Target (Net)
            context.account_balances[target_id] += net_proceeds
            context.account_book_costs[target_id] += net_proceeds 
            context.flows[target_id]["transfers_in"] += net_proceeds / 100.0
            
            # 3. Record Tax
            if tax_due > 0:
                context.flows[source_acc.id]["tax"] += tax_due / 100.0
                if source_acc.owners:
                    owner_id = source_acc.owners[0].id
                    if source_acc.tax_wrapper == enums.TaxWrapper.PENSION:
                         taxable_part = gross_sell * 0.75
                         context.ytd_earnings[owner_id]['taxable'] = context.ytd_earnings.get(owner_id, {}).get('taxable', 0) + taxable_part

            if cgt_due > 0:
                context.flows[source_acc.id]["cgt"] += cgt_due / 100.0
                if source_acc.owners:
                    owner_id = source_acc.owners[0].id
                    _, gain = calculate_disposal_impact(gross_sell, source['available'], context.account_book_costs.get(source_acc.id, 0), source_acc.account_type, source_acc.tax_wrapper)
                    context.ytd_gains[owner_id] = context.ytd_gains.get(owner_id, 0) + gain

            # Update loop variables
            source['available'] -= gross_sell
            needed_net -= net_proceeds
            
            # 4. LOGGING (Fixed: Using Object instead of String)
            context.rule_logs.append(
                schemas.RuleExecutionLog(
                    date=context.month_start,
                    rule_type="decumulation",
                    action="sell",
                    amount=float(gross_sell) / 100.0,
                    source_account=source_acc.name,
                    target_account=target_name,
                    reason="Deficit Coverage"
                )
            )

def utils_fmt(pence):
    return f"£{pence/100:,.2f}"

def solve_gross_withdrawal(net_needed: int, account: models.Account, max_available: int, context: ProjectionContext, scenario: models.Scenario) -> tuple[int, int, int]:
    """
    Returns (gross_sell, income_tax, cgt)
    """
    
    # 1. Simple Case: ISA or Cash (No Tax)
    if account.tax_wrapper == enums.TaxWrapper.ISA:
        take = min(net_needed, max_available)
        return take, 0, 0
        
    # 2. Complex Case: Iterative Solver
    current_gross_guess = min(net_needed, max_available)
    
    for i in range(MAX_ITERATIONS):
        income_tax = 0
        cgt = 0
        
        owner_id = account.owners[0].id if account.owners else None
        
        if account.tax_wrapper == enums.TaxWrapper.PENSION and owner_id:
             # UFPLS Logic: 25% Tax Free, 75% Taxed at Marginal Rate
             taxable_portion = int(current_gross_guess * 0.75)
             
             ytd = context.ytd_earnings.get(owner_id, {'taxable': 0, 'ni': 0})
             ytd_taxable = ytd['taxable']
             
             current_tax_paid = TaxService._calculate_income_tax(ytd_taxable / 100.0) * 100
             new_tax_total = TaxService._calculate_income_tax((ytd_taxable + taxable_portion) / 100.0) * 100
             
             income_tax = int(new_tax_total - current_tax_paid)
             
        elif (account.tax_wrapper == enums.TaxWrapper.GIA or account.tax_wrapper == enums.TaxWrapper.NONE) and owner_id:
            # CGT Logic
            current_bal = context.account_balances[account.id] 
            current_book = context.account_book_costs[account.id]
            
            _, gain = calculate_disposal_impact(current_gross_guess, current_bal, current_book, account.account_type, account.tax_wrapper)
            
            ytd_gains = context.ytd_gains.get(owner_id, 0)
            ytd_income = context.ytd_earnings.get(owner_id, {}).get('taxable', 0)
            
            cgt = TaxService.calculate_capital_gains_tax(gain, ytd_gains, ytd_income)

        # Result of this guess
        net_result = current_gross_guess - income_tax - cgt
        diff = net_needed - net_result
        
        # Strict Tolerance: Match or 1p surplus
        if diff == 0:
            return current_gross_guess, income_tax, cgt
            
        if diff == -1: 
            return current_gross_guess, income_tax, cgt
            
        # Adjust guess
        new_guess = current_gross_guess + diff
        
        if new_guess > max_available:
            if current_gross_guess == max_available:
                return current_gross_guess, income_tax, cgt
            current_gross_guess = max_available
        else:
            current_gross_guess = int(new_guess)
            
    # Best effort
    return current_gross_guess, income_tax, cgt
