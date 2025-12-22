from app import models, enums
from app.engine.context import ProjectionContext
from typing import List, Any
from dateutil.relativedelta import relativedelta

def _get_enum_value(obj: Any) -> str:
    """Safely get string value from an Enum or a String."""
    if obj is None: return None
    return obj.value if hasattr(obj, 'value') else str(obj)

def calculate_disposal_impact(withdrawal_amount: int, current_balance: int, current_book_cost: int, account_type: Any, tax_wrapper: Any) -> tuple[int, int]:
    # Robust Enum Access
    wrapper_val = _get_enum_value(tax_wrapper)
    type_val = _get_enum_value(account_type)
    
    # EXEMPTIONS: 
    # 1. Tax Wrappers (ISA/Pension) - if wrapper is not None/Empty
    if wrapper_val and wrapper_val != "None": return 0, 0
    
    # 2. Exempt Account Types
    # Note: Ensure these match the string values in enums.py
    if type_val in ["Cash", "Mortgage", "Loan", "Main Residence"]: return 0, 0
    
    if current_balance <= 0 or withdrawal_amount <= 0: return 0, 0
    
    fraction = withdrawal_amount / current_balance
    if fraction > 1.0: fraction = 1.0
    
    cost_portion = int(current_book_cost * fraction)
    gain = withdrawal_amount - cost_portion
    return cost_portion, gain

def calculate_gbp_balances(current_balances, accounts, rate, month_start=None):
    gbp_balances = {}
    total = 0
    account_map = {acc.id: acc for acc in accounts}
    for acc_id, bal in current_balances.items():
        acc = account_map.get(acc_id)
        if not acc: continue
        val_gbp = bal
        
        type_val = _get_enum_value(acc.account_type)
        currency_val = _get_enum_value(acc.currency)
        
        if type_val == "RSU Grant":
            if not acc.grant_date or not acc.unit_price: val_gbp = 0
            else:
                months_elapsed = 0
                if month_start and month_start > acc.grant_date:
                    diff = relativedelta(month_start, acc.grant_date.replace(day=1))
                    months_elapsed = diff.years * 12 + diff.months
                safe_rate = acc.interest_rate or 0.0
                monthly_rate = safe_rate / 100 / 12
                current_price = acc.unit_price * ((1 + monthly_rate) ** months_elapsed)
                units = bal / 100.0
                val_gbp = int(units * current_price)
                if currency_val == "USD": val_gbp = round(val_gbp / rate)
        elif currency_val == "USD":
            val_gbp = round(bal / rate)
            
        gbp_balances[acc_id] = val_gbp / 100.0
        total += val_gbp
    return gbp_balances, total / 100.0

def track_contribution(context: ProjectionContext, account_id: int, amount: int):
    if amount <= 0: return
    acc = next((a for a in context.all_accounts if a.id == account_id), None)
    if not acc: return
    
    # Robust Enum Access
    wrapper_val = _get_enum_value(acc.tax_wrapper)
    
    if not wrapper_val or wrapper_val == "None": return

    if acc.owners:
        owner_id = acc.owners[0].id
        type_val = _get_enum_value(acc.account_type)
        
        if owner_id not in context.ytd_contributions: context.ytd_contributions[owner_id] = {}
        
        key = f"{wrapper_val}:{type_val}"
        context.ytd_contributions[owner_id][key] = context.ytd_contributions[owner_id].get(key, 0) + amount

def get_contribution_headroom(context: ProjectionContext, account_id: int, tax_limits: List[models.TaxLimit]):
    acc = next((a for a in context.all_accounts if a.id == account_id), None)
    if not acc: return 999999999999
    
    wrapper_val = _get_enum_value(acc.tax_wrapper)
    
    if not wrapper_val or wrapper_val == "None": return 999999999999
    if not acc.owners: return 0
    
    owner_id = acc.owners[0].id
    type_val = _get_enum_value(acc.account_type)
    
    applicable_limits = []
    for limit in tax_limits:
        if limit.start_date <= context.month_start and (limit.end_date is None or limit.end_date >= context.month_start):
            if wrapper_val in limit.wrappers:
                if limit.account_types and len(limit.account_types) > 0:
                    if type_val not in limit.account_types: continue 
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
