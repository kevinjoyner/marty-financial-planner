from app import models, enums, schemas
from app.engine.context import ProjectionContext
from app.services.tax import TaxService
from app.engine.helpers import track_contribution, get_contribution_headroom, calculate_disposal_impact

def process_transfers(scenario: models.Scenario, context: ProjectionContext):
    seen_ids = set(); unique_transfers = []
    for t in scenario.transfers:
        if t.id not in seen_ids: unique_transfers.append(t); seen_ids.add(t.id)

    for transfer in unique_transfers:
        if not (transfer.start_date.replace(day=1) <= context.month_start and (transfer.end_date is None or transfer.end_date >= context.month_start)): continue

        value = int(transfer.value)
        from_account = next((acc for acc in context.all_accounts if acc.id == transfer.from_account_id), None)
        to_account = next((acc for acc in context.all_accounts if acc.id == transfer.to_account_id), None)
        if not from_account or not to_account: continue

        if from_account.currency != to_account.currency:
            if from_account.currency == enums.Currency.USD and to_account.currency == enums.Currency.GBP:
                value = round(value / scenario.gbp_to_usd_rate)
            elif from_account.currency == enums.Currency.GBP and to_account.currency == enums.Currency.USD:
                value = round(value * scenario.gbp_to_usd_rate)

        # Robust Cadence
        cadence_str = transfer.cadence.value if hasattr(transfer.cadence, 'value') else str(transfer.cadence)

        should = False
        start_month = transfer.start_date.month if transfer.start_date else 1
        start_year = transfer.start_date.year if transfer.start_date else context.month_start.year

        if cadence_str == 'once':
             if transfer.start_date and context.month_start.year == start_year and context.month_start.month == start_month: should = True
        elif cadence_str == 'monthly': should = True
        elif cadence_str == 'quarterly' and context.month_start.month in [1, 4, 7, 10]: should = True
        elif cadence_str == 'annually' and context.month_start.month == start_month: should = True
            
        if should:
            if transfer.show_on_chart:
                context.annotations.append(schemas.ProjectionAnnotation(date=context.month_start, label=transfer.name, type="transaction"))
            
            headroom = get_contribution_headroom(context, transfer.to_account_id, scenario.tax_limits)
            if headroom < value:
                context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=transfer.to_account_id, message=f"Tax Limit: Transfer exceeds allowance.", source_type="transfer", source_id=transfer.id))

            cgt_tax = 0
            cost_portion, gain = calculate_disposal_impact(value, context.account_balances[from_account.id], context.account_book_costs[from_account.id], from_account.account_type, from_account.tax_wrapper)
            
            if gain > 0 and from_account.owners:
                num_owners = len(from_account.owners)
                gain_per_owner = int(gain / num_owners)
                total_cgt = 0
                for owner in from_account.owners:
                    if owner.id not in context.ytd_gains: context.ytd_gains[owner.id] = 0
                    earnings = context.ytd_earnings.get(owner.id, {}).get('taxable', 0)
                    tax = TaxService.calculate_capital_gains_tax(gain_per_owner, context.ytd_gains[owner.id], earnings)
                    context.ytd_gains[owner.id] += gain_per_owner
                    total_cgt += tax
                cgt_tax = total_cgt

            context.account_balances[transfer.from_account_id] -= value
            context.account_book_costs[transfer.from_account_id] -= cost_portion 
            context.flows[transfer.from_account_id]["transfers_out"] += value
            context.flows[transfer.from_account_id]["cgt"] += cgt_tax 
            net_received = value - cgt_tax 
            context.account_balances[transfer.to_account_id] += net_received
            context.account_book_costs[transfer.to_account_id] += net_received 
            context.flows[transfer.to_account_id]["transfers_in"] += net_received
            track_contribution(context, transfer.to_account_id, net_received)
