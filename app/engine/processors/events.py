from app import models, enums
from app.engine.context import ProjectionContext
from dateutil.relativedelta import relativedelta

def process_events(scenario: models.Scenario, context: ProjectionContext):
    next_month_start = context.month_start + relativedelta(months=1)
    
    # Filter unique events by ID to avoid duplicates if scenario loaded oddly
    seen_ids = set()
    unique_events = []
    for e in scenario.financial_events:
        if e.id not in seen_ids:
            unique_events.append(e)
            seen_ids.add(e.id)

    for event in unique_events:
        # Check date falls within this month
        # FIX: Use .date instead of .event_date
        if not (event.date >= context.month_start and event.date < next_month_start and event.date >= scenario.start_date):
            continue
            
        val = event.value / 100.0 # Convert to float for flows
        
        # Apply Logic
        if event.type == 'windfall' or event.type == 'income':
            # Credit to account
            if event.to_account_id and event.to_account_id in context.account_balances:
                context.account_balances[event.to_account_id] += event.value
                if event.to_account_id not in context.flows: context.flows[event.to_account_id] = {}
                if "events" not in context.flows[event.to_account_id]: context.flows[event.to_account_id]["events"] = 0
                context.flows[event.to_account_id]["events"] += val
                
        elif event.type == 'expense':
            # Debit from account
            if event.from_account_id and event.from_account_id in context.account_balances:
                 context.account_balances[event.from_account_id] -= event.value
                 if event.from_account_id not in context.flows: context.flows[event.from_account_id] = {}
                 if "events" not in context.flows[event.from_account_id]: context.flows[event.from_account_id]["events"] = 0
                 context.flows[event.from_account_id]["events"] -= val
