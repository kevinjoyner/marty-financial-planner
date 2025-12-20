from dateutil.relativedelta import relativedelta
from app import enums

def calculate_gbp_balances(current_balances, accounts, rate, month_start=None):
    gbp_balances = {}
    total = 0
    account_map = {acc.id: acc for acc in accounts}
    for acc_id, bal in current_balances.items():
        acc = account_map.get(acc_id)
        if not acc: continue
        val_gbp = bal
        if acc.account_type == enums.AccountType.RSU_GRANT:
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
                if acc.currency == enums.Currency.USD: val_gbp = round(val_gbp / rate)
        elif acc.currency == enums.Currency.USD:
            val_gbp = round(bal / rate)
        gbp_balances[acc_id] = val_gbp / 100.0
        total += val_gbp
    return gbp_balances, total / 100.0
