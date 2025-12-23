from app import models, enums, schemas
from app.engine.context import ProjectionContext

def process_costs(scenario: models.Scenario, context: ProjectionContext):
    seen_ids = set(); unique_costs = []
    for c in scenario.costs:
        if c.id not in seen_ids: unique_costs.append(c); seen_ids.add(c.id)

    for cost in unique_costs:
        if cost.account_id not in context.account_balances: continue
        if cost.start_date is None: continue
        
        if not (cost.start_date.replace(day=1) <= context.month_start and (cost.end_date is None or cost.end_date >= context.month_start)): continue

        value = int(cost.value)
        target_account = next((acc for acc in context.all_accounts if acc.id == cost.account_id), None)
        if target_account and cost.currency != target_account.currency:
            if cost.currency == enums.Currency.USD and target_account.currency == enums.Currency.GBP:
                value = round(value / scenario.gbp_to_usd_rate)
            elif cost.currency == enums.Currency.GBP and target_account.currency == enums.Currency.USD:
                value = round(value * scenario.gbp_to_usd_rate)

        # Robust Cadence
        cadence_str = cost.cadence.value if hasattr(cost.cadence, 'value') else str(cost.cadence)
        
        should = False
        if cadence_str == 'once':
             if context.month_start.year == cost.start_date.year and context.month_start.month == cost.start_date.month: should = True
        elif cadence_str == 'monthly': should = True
        elif cadence_str == 'quarterly' and context.month_start.month in [1, 4, 7, 10]: should = True
        elif cadence_str == 'annually' and context.month_start.month == cost.start_date.month: should = True
            
        if should:
            context.account_balances[cost.account_id] -= value
            context.flows[cost.account_id]["costs"] += value
