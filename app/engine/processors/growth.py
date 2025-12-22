from app import models, enums
from app.engine.context import ProjectionContext

def process_growth(scenario: models.Scenario, context: ProjectionContext):
    """
    Apply monthly growth/interest to assets.
    """
    for acc in context.all_accounts:
        # 1. Skip types that don't grow via this processor
        # Mortgages/Loans are handled in mortgage.py
        # RSU Grants are share counts, they don't grow via interest (the price grows in valuation)
        if acc.account_type in [enums.AccountType.MORTGAGE, enums.AccountType.LOAN, enums.AccountType.RSU_GRANT]:
            continue
            
        rate = acc.interest_rate
        if not rate or rate == 0:
            continue
            
        balance = context.account_balances.get(acc.id, 0)
        if balance == 0:
            continue
            
        # 2. Calculate Monthly Growth
        # Formula: (1 + annual_rate)^(1/12) - 1
        monthly_factor = (1 + (rate / 100.0)) ** (1.0/12.0)
        growth_amount = int(balance * (monthly_factor - 1))
        
        if growth_amount != 0:
            # 3. Apply to Balance
            context.account_balances[acc.id] += growth_amount
            
            # 4. Log Flow (for charts/reporting)
            if acc.id in context.flows:
                if 'growth' not in context.flows[acc.id]:
                     context.flows[acc.id]['growth'] = 0.0
                context.flows[acc.id]['growth'] += growth_amount / 100.0
            
            # 5. Tax Logic: Savings Interest
            # If this is a Cash account and NOT in a tax wrapper, it counts towards the Personal Savings Allowance.
            is_cash = (acc.account_type == enums.AccountType.CASH)
            is_unwrapped = (not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.NONE)
            
            if is_cash and is_unwrapped:
                 if acc.owners:
                    owner_id = acc.owners[0].id
                    if owner_id not in context.ytd_interest:
                        context.ytd_interest[owner_id] = 0
                    context.ytd_interest[owner_id] += growth_amount
