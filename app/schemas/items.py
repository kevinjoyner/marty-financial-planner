from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date
from ..enums import Cadence, Currency, FinancialEventType, RuleType

# --- INCOME ---
class IncomeSourceBase(BaseModel):
    name: str
    owner_id: int
    net_value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    is_pre_tax: bool = False
    salary_sacrifice_value: Optional[int] = 0
    salary_sacrifice_account_id: Optional[int] = None
    taxable_benefit_value: Optional[int] = 0
    employer_pension_contribution: Optional[int] = 0
    currency: Currency = Currency.GBP
    account_id: Optional[int] = None
    notes: Optional[str] = None
    growth_rate: Optional[float] = 0.0

class IncomeSourceCreate(IncomeSourceBase):
    pass

class IncomeSourceUpdate(BaseModel):
    name: Optional[str] = None
    net_value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_pre_tax: Optional[bool] = None
    salary_sacrifice_value: Optional[int] = None
    salary_sacrifice_account_id: Optional[int] = None
    taxable_benefit_value: Optional[int] = None
    employer_pension_contribution: Optional[int] = None
    currency: Optional[Currency] = None
    account_id: Optional[int] = None
    notes: Optional[str] = None
    growth_rate: Optional[float] = None

class IncomeSource(IncomeSourceBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- COSTS ---
class CostBase(BaseModel):
    name: str
    scenario_id: int
    account_id: int
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    notes: Optional[str] = None
    growth_rate: Optional[float] = 0.0
    is_recurring: bool = True

class CostCreate(CostBase):
    pass

class CostUpdate(BaseModel):
    name: Optional[str] = None
    account_id: Optional[int] = None
    value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: Optional[Currency] = None
    notes: Optional[str] = None
    growth_rate: Optional[float] = None
    is_recurring: Optional[bool] = None

class Cost(CostBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- TRANSFERS ---
class TransferBase(BaseModel):
    name: str
    scenario_id: int
    from_account_id: int
    to_account_id: int
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    notes: Optional[str] = None
    show_on_chart: bool = False

class TransferCreate(TransferBase):
    pass

class TransferUpdate(BaseModel):
    name: Optional[str] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: Optional[Currency] = None
    notes: Optional[str] = None
    show_on_chart: Optional[bool] = None

class Transfer(TransferBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- EVENTS ---
class FinancialEventBase(BaseModel):
    name: str
    scenario_id: int
    value: int
    event_date: date
    event_type: FinancialEventType
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    currency: Currency = Currency.GBP
    notes: Optional[str] = None
    show_on_chart: bool = True

class FinancialEventCreate(FinancialEventBase):
    pass

class FinancialEventUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[int] = None
    event_date: Optional[date] = None
    event_type: Optional[FinancialEventType] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    currency: Optional[Currency] = None
    notes: Optional[str] = None
    show_on_chart: Optional[bool] = None

class FinancialEvent(FinancialEventBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

# --- ANNOTATIONS ---
class ChartAnnotation(BaseModel):
    date: date
    label: str
    annotation_type: str
    model_config = ConfigDict(from_attributes=True)
