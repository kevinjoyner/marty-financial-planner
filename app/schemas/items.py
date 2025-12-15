from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date
from ..enums import Cadence, Currency, FinancialEventType

# --- CHART ANNOTATION ---
class ChartAnnotationBase(BaseModel):
    date: date
    label: str
    annotation_type: str = "manual"

class ChartAnnotationCreate(ChartAnnotationBase):
    scenario_id: int

class ChartAnnotationUpdate(BaseModel):
    date: Optional[date] = None
    label: Optional[str] = None
    annotation_type: Optional[str] = None

class ChartAnnotation(ChartAnnotationBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

# --- INCOME ---
class IncomeSourceBase(BaseModel):
    name: str
    notes: Optional[str] = None
    net_value: int
    is_pre_tax: bool = False
    
    salary_sacrifice_value: Optional[int] = 0
    salary_sacrifice_account_id: Optional[int] = None
    taxable_benefit_value: Optional[int] = 0
    employer_pension_contribution: Optional[int] = 0
    
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    account_id: int

class IncomeSourceCreate(IncomeSourceBase):
    owner_id: int

class IncomeSourceUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    net_value: Optional[int] = None
    is_pre_tax: Optional[bool] = None
    
    salary_sacrifice_value: Optional[int] = None
    salary_sacrifice_account_id: Optional[int] = None
    taxable_benefit_value: Optional[int] = None
    employer_pension_contribution: Optional[int] = None
    
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: Optional[Currency] = None
    account_id: Optional[int] = None

class IncomeSource(IncomeSourceBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)

# --- COSTS ---
class CostBase(BaseModel):
    name: str
    notes: Optional[str] = None
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    is_recurring: bool
    currency: Currency = Currency.GBP
    account_id: int

class CostCreate(CostBase):
    scenario_id: int

class CostUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_recurring: Optional[bool] = None
    currency: Optional[Currency] = None
    account_id: Optional[int] = None

class Cost(CostBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

# --- EVENTS ---
class FinancialEventBase(BaseModel):
    name: str
    notes: Optional[str] = None
    value: int
    event_date: date
    currency: Currency = Currency.GBP
    event_type: FinancialEventType = FinancialEventType.INCOME_EXPENSE
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    show_on_chart: bool = False

class FinancialEventCreate(FinancialEventBase):
    scenario_id: int

class FinancialEventUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    value: Optional[int] = None
    event_date: Optional[date] = None
    currency: Optional[Currency] = None
    event_type: Optional[FinancialEventType] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    show_on_chart: Optional[bool] = None

class FinancialEvent(FinancialEventBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

# --- TRANSFERS ---
class TransferBase(BaseModel):
    name: str
    notes: Optional[str] = None
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    from_account_id: int
    to_account_id: int
    show_on_chart: bool = False

class TransferCreate(TransferBase):
    scenario_id: int

class TransferUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: Optional[Currency] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    show_on_chart: Optional[bool] = None

class Transfer(TransferBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)
