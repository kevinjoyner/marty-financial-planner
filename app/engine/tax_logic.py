from typing import List
from app import enums, models
from .context import ProjectionContext

def calculate_disposal_impact(withdrawal_amount: int, current_balance: int, current_book_cost: int, account_type: enums.AccountType, tax_wrapper: enums.TaxWrapper) -> tuple[int, int]:
    # EXEMPTIONS: 
    # 1. Tax Wrappers (ISA/Pension)
    # 2. Cash/Debt accounts
    # 3. Main Residence (Private Residence Relief)
    if tax_wrapper and tax_wrapper != enums.TaxWrapper.NONE: return 0, 0
    if account_type in [enums.AccountType.CASH, enums.AccountType.MORTGAGE, enums.AccountType.LOAN, enums.AccountType.MAIN_RESIDENCE]: return 0, 0
    
    if current_balance <= 0 or withdrawal_amount <= 0: return 0, 0
    fraction = withdrawal_amount / current_balance
    if fraction > 1.0: fraction = 1.0
    cost_portion = int(current_book_cost * fraction)
    gain = withdrawal_amount - cost_portion
    return cost_portion, gain

def track_contribution(context: ProjectionContext, account_id: int, amount: int):
    if amount <= 0: return
    acc = next((a for a in context.all_accounts if a.id == account_id), None)
    if not acc or not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.NONE: return
    if acc.owners:
        owner_id = acc.owners[0].id
        wrapper_str = acc.tax_wrapper.value 
        type_str = acc.account_type.value
        if owner_id not in context.ytd_contributions: context.ytd_contributions[owner_id] = {}
        key = f"{wrapper_str}:{type_str}"
        context.ytd_contributions[owner_id][key] = context.ytd_contributions[owner_id].get(key, 0) + amount

def get_contribution_headroom(context: ProjectionContext, account_id: int, tax_limits: List[models.TaxLimit]):
    acc = next((a for a in context.all_accounts if a.id == account_id), None)
    if not acc or not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.NONE: return 999999999999
    if not acc.owners: return 0
    owner_id = acc.owners[0].id
    wrapper_str = acc.tax_wrapper.value
    type_str = acc.account_type.value
    applicable_limits = []
    for limit in tax_limits:
        if limit.start_date <= context.month_start and (limit.end_date is None or limit.end_date >= context.month_start):
            if wrapper_str in limit.wrappers:
                if limit.account_types and len(limit.account_types) > 0:
                    if type_str not in limit.account_types: continue 
                applicable_limits.append(limit)
    if not applicable_limits: return 999999999999
    min_headroom = 999999999999
    for limit in applicable_limits:
        limit_usage = 0
        if owner_id in context.ytd_contributions:
            user_contribs = context.ytd_contributions[owner_id]
            for key, amount in user_contribs.items():
                c_wrapper, c_type = key.split(":")
                wrapper_match = c_wrapper in limit.wrappers
                type_match = True
                if limit.account_types and len(limit.account_types) > 0:
                    if c_type not in limit.account_types: type_match = False
                if wrapper_match and type_match: limit_usage += amount
        headroom = max(0, limit.amount - limit_usage)
        if headroom < min_headroom: min_headroom = headroom
    return min_headroom
