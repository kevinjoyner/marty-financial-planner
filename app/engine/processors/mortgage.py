from app import models, enums, utils
from app.engine.context import ProjectionContext
from dateutil.relativedelta import relativedelta
from app.engine.helpers import _get_enum_value

def process_mortgages(scenario: models.Scenario, context: ProjectionContext):
    """
    Calculate and apply mortgage payments (Capital + Interest) for the month.
    """
    for acc in context.all_accounts:
        type_val = _get_enum_value(acc.account_type)
        if type_val != "Mortgage":
            continue
            
        current_bal = context.account_balances.get(acc.id, 0)
        
        # If already cleared (or positive), skip payment logic
        if current_bal >= 0:
            continue
            
        safe_interest_rate = acc.interest_rate or 0.0
        
        is_fixed_period = False
        if acc.mortgage_start_date and acc.fixed_rate_period_years and acc.fixed_interest_rate is not None:
            fixed_end_date = acc.mortgage_start_date + relativedelta(years=acc.fixed_rate_period_years)
            if context.month_start < fixed_end_date:
                safe_interest_rate = acc.fixed_interest_rate
                is_fixed_period = True
                
        monthly_repayment = 0
        if acc.original_loan_amount and acc.amortisation_period_years:
            if is_fixed_period:
                monthly_repayment = utils.calculate_mortgage_payment(acc.original_loan_amount, safe_interest_rate, acc.amortisation_period_years)
            elif acc.mortgage_start_date:
                loan_end_date = acc.mortgage_start_date + relativedelta(years=acc.amortisation_period_years)
                delta = relativedelta(loan_end_date, context.month_start)
                remaining_months = delta.years * 12 + delta.months
                
                if remaining_months > 0:
                    monthly_rate = safe_interest_rate / 100 / 12
                    if monthly_rate > 0:
                        numerator = monthly_rate * abs(current_bal)
                        denominator = 1 - (1 + monthly_rate) ** (-remaining_months)
                        monthly_repayment = round(numerator / denominator)
                    else:
                        monthly_repayment = round(abs(current_bal) / remaining_months)
                else:
                    monthly_repayment = abs(current_bal)
            else:
                monthly_repayment = utils.calculate_mortgage_payment(acc.original_loan_amount, safe_interest_rate, acc.amortisation_period_years)
        
        if monthly_repayment > 0:
            if (current_bal + monthly_repayment) > 0:
                monthly_repayment = abs(current_bal)
            
            payment_account_id = acc.payment_from_account_id
            if payment_account_id and payment_account_id in context.account_balances:
                context.account_balances[payment_account_id] -= monthly_repayment
                if payment_account_id not in context.flows: context.flows[payment_account_id] = {}
                if "mortgage_payments_out" not in context.flows[payment_account_id]: context.flows[payment_account_id]["mortgage_payments_out"] = 0
                context.flows[payment_account_id]["mortgage_payments_out"] += monthly_repayment / 100.0

            context.account_balances[acc.id] += monthly_repayment
            if acc.id not in context.flows: context.flows[acc.id] = {}
            if "mortgage_repayments_in" not in context.flows[acc.id]: context.flows[acc.id]["mortgage_repayments_in"] = 0
            context.flows[acc.id]["mortgage_repayments_in"] += monthly_repayment / 100.0
