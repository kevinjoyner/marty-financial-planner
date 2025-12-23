from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date
from ..enums import AccountType, TaxWrapper, Currency
from .shared import AccountBase, OwnerBase

class AccountCreate(AccountBase):
    owner_ids: Optional[List[int]] = []
    scenario_id: int

class AccountUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    account_type: Optional[AccountType] = None
    tax_wrapper: Optional[TaxWrapper] = None
    starting_balance: Optional[int] = None
    book_cost: Optional[int] = None
    min_balance: Optional[int] = None
    interest_rate: Optional[float] = None
    original_loan_amount: Optional[int] = None
    amortisation_period_years: Optional[int] = None
    mortgage_start_date: Optional[date] = None
    fixed_rate_period_years: Optional[int] = None
    fixed_interest_rate: Optional[float] = None
    is_primary_account: Optional[bool] = None
    currency: Optional[Currency] = None
    payment_from_account_id: Optional[int] = None

    # RSU Fields
    rsu_target_account_id: Optional[int] = None
    vesting_schedule: Optional[List[dict]] = None
    grant_date: Optional[date] = None
    unit_price: Optional[int] = None
    vesting_cadence: Optional[str] = None

    owner_ids: Optional[List[int]] = None

class OwnerInAccount(OwnerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Account(AccountBase):
    id: int
    scenario_id: int
    owners: List[OwnerInAccount] = []
    model_config = ConfigDict(from_attributes=True)
