from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date
from ..enums import AccountType, TaxWrapper, Currency

class AccountBase(BaseModel):
    name: str
    notes: Optional[str] = None
    account_type: AccountType
    tax_wrapper: Optional[TaxWrapper] = None
    starting_balance: int
    book_cost: Optional[int] = None
    min_balance: Optional[int] = 0
    interest_rate: Optional[float] = 0.0
    
    original_loan_amount: Optional[int] = None
    amortisation_period_years: Optional[int] = None
    mortgage_start_date: Optional[date] = None
    fixed_rate_period_years: Optional[int] = None
    fixed_interest_rate: Optional[float] = None
    is_primary_account: bool = False
    currency: Currency = Currency.GBP
    payment_from_account_id: Optional[int] = None
    
    # RSU Fields
    rsu_target_account_id: Optional[int] = None
    vesting_schedule: Optional[List[dict]] = None
    grant_date: Optional[date] = None
    unit_price: Optional[int] = None
    vesting_cadence: Optional[str] = 'monthly'

class OwnerBase(BaseModel):
    name: str
    notes: Optional[str] = None
