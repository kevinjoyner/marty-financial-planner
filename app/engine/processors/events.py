from app import models, enums, schemas
from app.engine.context import ProjectionContext
from dateutil.relativedelta import relativedelta
from app.engine.helpers import track_contribution, get_contribution_headroom, calculate_disposal_impact
from app.services.tax import TaxService

def process_events(scenario: models.Scenario, context: ProjectionContext):
    next_month_start = context.month_start + relativedelta(months=1)
    seen_ids = set(); unique_events = []
    for e in scenario.financial_events:
        if e.id not in seen_ids: unique_events.append(e); seen_ids.add(e.id)

    for event in unique_events:
        # Check date falls within this month
        if not (event.event_date >= context.month_start and event.event_date < next_month_start and event.event_date >= scenario.start_date):
            continue
            
        if event.show_on_chart:
            context.annotations.append(schemas.ProjectionAnnotation(date=event.event_date, label=event.name, type="transaction"))
        
        # Robust Type Check
        evt_type = str(event.event_type.value) if hasattr(event.event_type, 'value') else str(event.event_type)
        is_income_expense = (evt_type == 'income_expense')
        is_transfer = (evt_type == 'transfer')

        if is_income_expense and event.from_account_id in context.account_balances:
            val = int(event.value)
            if val > 0:
                 headroom = get_contribution_headroom(context, event.from_account_id, scenario.tax_limits)
                 if headroom < val:
                     context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=event.from_account_id, message=f"Tax Limit: Event '{event.name}' exceeds allowance.", source_type="event", source_id=event.id))
                 track_contribution(context, event.from_account_id, val)
            
            context.account_balances[event.from_account_id] += val
            context.account_book_costs[event.from_account_id] += val 
            context.flows[event.from_account_id]["events"] += val / 100.0

        elif is_transfer and event.from_account_id in context.account_balances and event.to_account_id in context.account_balances:
            val = int(event.value)
            headroom = get_contribution_headroom(context, event.to_account_id, scenario.tax_limits)
            if headroom < val:
                 context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=event.to_account_id, message=f"Tax Limit: Transfer Event '{event.name}' exceeds allowance.", source_type="event", source_id=event.id))
            
            from_acc = next((a for a in context.all_accounts if a.id == event.from_account_id), None)
            cgt_tax = 0
            cost_portion = val 
            
            if from_acc:
                cost_portion, gain = calculate_disposal_impact(val, context.account_balances[event.from_account_id], context.account_book_costs[event.from_account_id], from_acc.account_type, from_acc.tax_wrapper)
                
                if gain > 0 and from_acc.owners:
                    num_owners = len(from_acc.owners)
                    gain_per_owner = int(gain / num_owners)
                    total_cgt = 0
                    for owner in from_acc.owners:
                        if owner.id not in context.ytd_gains: context.ytd_gains[owner.id] = 0
                        earnings = context.ytd_earnings.get(owner.id, {}).get('taxable', 0)
                        tax = TaxService.calculate_capital_gains_tax(gain_per_owner, context.ytd_gains[owner.id], earnings)
                        context.ytd_gains[owner.id] += gain_per_owner
                        total_cgt += tax
                    cgt_tax = total_cgt

            context.account_balances[event.from_account_id] -= val
            context.account_book_costs[event.from_account_id] -= cost_portion 
            context.flows[event.from_account_id]["transfers_out"] += val / 100.0
            context.flows[event.from_account_id]["cgt"] += cgt_tax / 100.0
            
            net_received = val - cgt_tax
            context.account_balances[event.to_account_id] += net_received
            context.account_book_costs[event.to_account_id] += net_received
            context.flows[event.to_account_id]["transfers_in"] += net_received / 100.0
            track_contribution(context, event.to_account_id, net_received)
