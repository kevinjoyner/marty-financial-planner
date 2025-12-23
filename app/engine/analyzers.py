from dateutil.relativedelta import relativedelta
from app import enums, schemas
from app.engine.context import ProjectionContext

def detect_milestones(context: ProjectionContext):
    
    # 0. Retirement Party
    # Iterate unique owners found on accounts.
    seen_owners = set()
    for acc in context.all_accounts:
        if acc.owners:
            for owner in acc.owners:
                if owner.id in seen_owners: continue
                seen_owners.add(owner.id)
                
                if owner.birth_date and owner.retirement_age:
                    # Check age this month
                    age_rel = relativedelta(context.month_start, owner.birth_date)
                    # If exactly X years and 0 months
                    if age_rel.years == owner.retirement_age and age_rel.months == 0:
                        context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label=f"Retirement: {owner.name}", type="milestone"))

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
    if prev_liquid < prev_debt and curr_liquid >= curr_debt and prev_debt > 0:
         # FIX: Check if already added to avoid duplicates from volatility
         if not any(a.label == "Liquid assets exceed liabilities" for a in context.annotations):
             context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label="Liquid assets exceed liabilities", type="milestone"))

    # ALERT: Insolvency (Running out of money)
    # Check if Liquid Assets drop below 0 (excluding debt) - this means even cash/investments are gone/overdrawn
    # or strictly, if total liquid balance is negative.
    if curr_liquid < 0:
        # Check if we already have this alert for this month to avoid span spam
        if not any(a.label == "Insolvency Risk" and a.date == context.month_start for a in context.annotations):
             context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label="Insolvency Risk", type="insolvency"))

