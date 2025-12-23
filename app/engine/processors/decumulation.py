from app import models, enums
from app.engine.context import ProjectionContext
from app.services.tax import TaxService
from app.engine.helpers import _get_enum_value

def process_decumulation(scenario: models.Scenario, context: ProjectionContext):
    """
    Handle auto-spending from liquid assets if Cash accounts are insufficient.
    Strategy:
    1. Identify Cash accounts with negative balance.
    2. Sum total deficit.
    3. Withdraw from liquid assets to cover deficit.
       Priority: ISA -> GIA (Investments) -> Pension.
    """
    # 1. Calculate Deficit in Cash Accounts
    total_deficit = 0
    cash_accounts = []

    for acc in context.all_accounts:
        if _get_enum_value(acc.account_type) == "Cash":
            bal = context.account_balances.get(acc.id, 0)
            if bal < 0:
                total_deficit += abs(bal)
                cash_accounts.append(acc) # These are where we need money

    if total_deficit <= 0:
        return

    # 2. Identify Sources
    isas = []
    gias = []
    pensions = []

    for acc in context.all_accounts:
        bal = context.account_balances.get(acc.id, 0)
        if bal <= 0: continue

        # Check type/wrapper
        a_type = _get_enum_value(acc.account_type)
        wrapper = _get_enum_value(acc.tax_wrapper)

        if a_type == "Investment" or a_type == "Cash": # Don't sell Property/Mortgage
             if wrapper == "ISA":
                 isas.append(acc)
             elif wrapper == "Pension":
                 pensions.append(acc)
             elif wrapper == "General Investment Account" or wrapper == "None" or wrapper is None:
                 gias.append(acc)

    # 3. Withdraw Logic (Simplified Priority: ISA -> GIA -> Pension)
    remaining_deficit = total_deficit

    # Process ISAs (Tax Free)
    for acc in isas:
        if remaining_deficit <= 0: break
        available = context.account_balances.get(acc.id, 0)
        to_withdraw = min(available, remaining_deficit)

        context.account_balances[acc.id] -= to_withdraw
        remaining_deficit -= to_withdraw

        # Move to Cash (Split across deficit accounts or just dump in first? First for simplicity)
        target_acc = cash_accounts[0] # Assume at least one since deficit > 0
        context.account_balances[target_acc.id] += to_withdraw

        # Log Flow
        if acc.id not in context.flows: context.flows[acc.id] = {}
        if "transfers_out" not in context.flows[acc.id]: context.flows[acc.id]["transfers_out"] = 0
        context.flows[acc.id]["transfers_out"] += to_withdraw / 100.0

        if target_acc.id not in context.flows: context.flows[target_acc.id] = {}
        if "transfers_in" not in context.flows[target_acc.id]: context.flows[target_acc.id]["transfers_in"] = 0
        context.flows[target_acc.id]["transfers_in"] += to_withdraw / 100.0

    if remaining_deficit <= 0: return

    # Process GIAs (Capital Gains Tax - Simplified: Assume Cash Basis / No Tax for this step unless we implement CGT logic)
    # The brief implies specific focus on Pension Tax.
    for acc in gias:
        if remaining_deficit <= 0: break
        available = context.account_balances.get(acc.id, 0)
        to_withdraw = min(available, remaining_deficit)

        context.account_balances[acc.id] -= to_withdraw
        remaining_deficit -= to_withdraw

        target_acc = cash_accounts[0]
        context.account_balances[target_acc.id] += to_withdraw

        if acc.id not in context.flows: context.flows[acc.id] = {}
        if "transfers_out" not in context.flows[acc.id]: context.flows[acc.id]["transfers_out"] = 0
        context.flows[acc.id]["transfers_out"] += to_withdraw / 100.0

    if remaining_deficit <= 0: return

    # Process Pensions (Taxable)
    for acc in pensions:
        if remaining_deficit <= 0: break
        available = context.account_balances.get(acc.id, 0)

        # We need NET `remaining_deficit`. So we need to withdraw GROSS.
        # solve_gross_withdrawal expects net amount in PENCE?
        # Let's assume yes.

        gross_needed = solve_gross_withdrawal(remaining_deficit, "Pension", context, owner_id=acc.owners[0].id if acc.owners else None)

        to_withdraw_gross = min(available, gross_needed)

        # If available < gross_needed, we only get partial Net.
        # But wait, tax calculation changes if amount changes.
        # Simplified: If capped by available, just take all available and calculate tax on it.
        if available < gross_needed:
             to_withdraw_gross = available

        # Calculate Tax on actual Gross
        # We need the owner ID to check marginal rate
        owner_id = acc.owners[0].id if acc.owners else None
        tax_deducted = 0

        if owner_id:
            # Pension specific rule: 25% Tax Free. 75% Taxable.
            tax_free_portion = int(to_withdraw_gross * 0.25)
            taxable_portion = to_withdraw_gross - tax_free_portion

            ytd = context.ytd_earnings.get(owner_id, {'taxable': 0, 'ni': 0})
            current_taxable = ytd['taxable']

            tax_before = TaxService._calculate_income_tax(current_taxable / 100.0) * 100
            tax_after = TaxService._calculate_income_tax((current_taxable + taxable_portion) / 100.0) * 100
            tax_deducted = int(tax_after - tax_before)

            # Update YTD? Usually yes.
            context.ytd_earnings[owner_id]['taxable'] += taxable_portion

        net_proceeds = to_withdraw_gross - tax_deducted

        # Execute
        context.account_balances[acc.id] -= to_withdraw_gross
        target_acc = cash_accounts[0]
        context.account_balances[target_acc.id] += net_proceeds
        remaining_deficit -= net_proceeds # Reduces net deficit

        # Log Flows
        if acc.id not in context.flows: context.flows[acc.id] = {}
        if "transfers_out" not in context.flows[acc.id]: context.flows[acc.id]["transfers_out"] = 0
        context.flows[acc.id]["transfers_out"] += to_withdraw_gross / 100.0

        if "tax" not in context.flows[acc.id]: context.flows[acc.id]["tax"] = 0
        context.flows[acc.id]["tax"] += tax_deducted / 100.0

        if target_acc.id not in context.flows: context.flows[target_acc.id] = {}
        if "transfers_in" not in context.flows[target_acc.id]: context.flows[target_acc.id]["transfers_in"] = 0
        context.flows[target_acc.id]["transfers_in"] += net_proceeds / 100.0


def solve_gross_withdrawal(
    net_amount: int,
    tax_wrapper: str,
    context: ProjectionContext,
    owner_id: int = None
) -> int:
    """
    Solves for Gross withdrawal required to receive `net_amount`.
    Iterative solver due to progressive tax bands.
    """
    if tax_wrapper != "Pension":
        return net_amount # ISA/GIA assumed 0 tax for this context

    if not owner_id:
        return net_amount # Cannot calc tax without owner

    # Initial Guess: Net = Gross (0% tax)
    # Better Guess: Assume 20% basic rate on 75% taxable -> 15% effective.
    # Gross ~ Net / 0.85
    guess_gross = int(net_amount / 0.85)

    # Iteration
    for _ in range(5): # 5 iterations usually enough for tax bands
        # Calculate Net from Guess
        tax_free = int(guess_gross * 0.25)
        taxable = guess_gross - tax_free

        ytd = context.ytd_earnings.get(owner_id, {'taxable': 0})
        current_taxable = ytd['taxable']

        tax_before = TaxService._calculate_income_tax(current_taxable / 100.0) * 100
        tax_after = TaxService._calculate_income_tax((current_taxable + taxable) / 100.0) * 100
        tax = int(tax_after - tax_before)

        net_actual = guess_gross - tax

        diff = net_amount - net_actual
        if abs(diff) < 5: # Within 5 pence
            return guess_gross

        # Adjust guess
        # If we are short (diff > 0), we need more gross.
        # Adjustment = Diff / (1 - MarginalRate).
        # Marginal Rate approx 0.15 to 0.45.
        # Safe step: just add diff? No, that's too slow.
        # Add diff * 1.2
        guess_gross += int(diff * 1.1)

    return guess_gross
