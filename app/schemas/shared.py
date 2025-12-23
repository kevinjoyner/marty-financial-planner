from pydantic import BaseModel, model_validator
from typing import Optional, List, Dict, Any
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

    @model_validator(mode='before')
    @classmethod
    def normalize_account_type(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if data.get('account_type') == 'current':
                data['account_type'] = AccountType.CASH.value
        elif hasattr(data, 'account_type'):
            # Handle ORM objects or other objects
            val = getattr(data, 'account_type')
            if val == 'current':
                # We can't easily mutate the ORM object in a way that affects Pydantic validation 
                # if Pydantic is reading from attributes directly.
                # However, if 'from_attributes=True' is set, Pydantic converts to dict first (in v1) 
                # or reads fields (in v2). In v2 mode='before', we get the input.
                # If input is object, we can return a dict with the fixed value? 
                # Or we can't mutate the object.
                # Best approach for V2 with ORM: Convert to dict if it's an object we need to fix.
                # But that might break other things.
                # Actually, simply checking if it matches the Enum value "current" (which isn't in Enum)
                # and replacing it is the goal.
                # If we return a new object (or dict) that represents the fixed data, Pydantic uses that.
                try:
                    # Create a dict from the object, fixing the field
                    d = {k: getattr(data, k) for k in data.__dict__ if not k.startswith('_')}
                    d['account_type'] = AccountType.CASH.value
                    return d
                except Exception:
                    pass
        return data

class OwnerBase(BaseModel):
    name: str
    notes: Optional[str] = None
    birth_date: Optional[date] = None
    retirement_age: Optional[int] = None
