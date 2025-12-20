from dateutil.relativedelta import relativedelta
from app import models, enums, utils
from app.engine.context import ProjectionContext

def process_standard_mortgage_payments(scenario: models.Scenario, context: ProjectionContext):
    for acc in context.all_accounts:
        if acc.account_type == enums.AccountType.MORTGAGE and context.account_balances[acc.id] < 0:
            safe_interest_rate = acc.interest_rate or 0.0
            is_fixed_period = False
            if acc.mortgage_start_date and acc.fixed_rate_period_years and acc.fixed_interest_rate is not None:
                fixed_end_date = acc.mortgage_start_date + relativedelta(years=acc.fixed_rate_period_years)
                if context.month_start < fixed_end_date: safe_interest_rate = acc.fixed_interest_rate; is_fixed_period = True
            monthly_repayment = 0
            if acc.original_loan_amount and acc.amortisation_period_years:
                if is_fixed_period: monthly_repayment = utils.calculate_mortgage_payment(acc.original_loan_amount, safe_interest_rate, acc.amortisation_period_years)
                elif acc.mortgage_start_date:
                    loan_end_date = acc.mortgage_start_date + relativedelta(years=acc.amortisation_period_years)
                    delta = relativedelta(loan_end_date, context.month_start); remaining_months = delta.years * 12 + delta.months
                    if remaining_months > 0:
                        monthly_rate = safe_interest_rate / 100 / 12
                        if monthly_rate > 0: numerator = monthly_rate * abs(context.account_balances[acc.id]); denominator = 1 - (1 + monthly_rate) ** (-remaining_months); monthly_repayment = round(numerator / denominator)
                        else: monthly_repayment = round(abs(context.account_balances[acc.id]) / remaining_months)
                    else: monthly_repayment = abs(context.account_balances[acc.id])
                else: monthly_repayment = utils.calculate_mortgage_payment(acc.original_loan_amount, safe_interest_rate, acc.amortisation_period_years)
            if monthly_repayment > 0:
                if (context.account_balances[acc.id] + monthly_repayment) > 0: monthly_repayment = abs(context.account_balances[acc.id])
                payment_account_id = acc.payment_from_account_id
                if payment_account_id and payment_account_id in context.account_balances:
                    context.account_balances[payment_account_id] -= monthly_repayment; context.flows[payment_account_id]["mortgage_payments_out"] += monthly_repayment / 100.0
                context.account_balances[acc.id] += monthly_repayment; context.flows[acc.id]["mortgage_repayments_in"] += monthly_repayment / 100.0
