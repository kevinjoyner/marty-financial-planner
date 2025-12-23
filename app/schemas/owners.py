from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date
from ..enums import Cadence, Currency
from .shared import OwnerBase

# INCOME
class IncomeSourceBase(BaseModel):
    name: str
    amount: Optional[int] = None
    net_value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    growth_rate: Optional[float] = 0.0
    account_id: Optional[int] = None
    is_pre_tax: bool = False
    salary_sacrifice_value: int = 0
    salary_sacrifice_account_id: Optional[int] = None
    taxable_benefit_value: int = 0
    employer_pension_contribution: int = 0
    notes: Optional[str] = None

class IncomeSourceCreate(IncomeSourceBase):
    owner_id: int

class IncomeSourceUpdate(BaseModel):
    name: Optional[str] = None
    net_value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: Optional[Currency] = None
    account_id: Optional[int] = None
    is_pre_tax: Optional[bool] = None
    salary_sacrifice_value: Optional[int] = None
    salary_sacrifice_account_id: Optional[int] = None
    taxable_benefit_value: Optional[int] = None
    employer_pension_contribution: Optional[int] = None
    notes: Optional[str] = None

class IncomeSource(IncomeSourceBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)

# OWNER
class OwnerCreate(OwnerBase):
    scenario_id: int

class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    scenario_id: Optional[int] = None
    birth_date: Optional[date] = None
    retirement_age: Optional[int] = None

# Forward declaration for AccountInOwner to avoid circular imports if possible,
# or we just use a simplified version here if needed.
# In scenarios.py, Owner has accounts: List[AccountInOwner].
# AccountInOwner was defined in scenarios.py as inheriting from AccountBase.

from .shared import AccountBase

class AccountInOwner(AccountBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Owner(OwnerBase):
    id: int
    scenario_id: int
    accounts: List[AccountInOwner] = []
    income_sources: List[IncomeSource] = []
    model_config = ConfigDict(from_attributes=True)
