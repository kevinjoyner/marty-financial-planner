import math

def calculate_mortgage_payment(principal: float, annual_interest_rate: float, years: int) -> int:
    """
    Calculates monthly mortgage payment. Returns value in pence (int).
    principal: Loan amount in pence
    annual_interest_rate: Percentage (e.g. 4.5 for 4.5%)
    years: Loan term
    """
    if not principal or not years:
        return 0
        
    if annual_interest_rate == 0:
        return int(principal / (years * 12))

    monthly_rate = annual_interest_rate / 100 / 12
    num_payments = years * 12
    
    numerator = principal * (monthly_rate * (1 + monthly_rate) ** num_payments)
    denominator = ((1 + monthly_rate) ** num_payments) - 1
    
    return int(numerator / denominator)

def format_currency(value_pence):
    return f"£{value_pence / 100:,.2f}"

def get_uk_fiscal_year(date_obj):
    """
    Returns the year in which the UK Fiscal Year started for the given date.
    UK Tax Year starts 6th April.
    Example: 
    - 2025-04-05 is FY 2024
    - 2025-04-06 is FY 2025
    """
    if date_obj.month < 4:
        return date_obj.year - 1
    elif date_obj.month == 4 and date_obj.day < 6:
        return date_obj.year - 1
    else:
        return date_obj.year
