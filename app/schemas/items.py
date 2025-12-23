from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, List
from datetime import date
from ..enums import Cadence, Currency

# --- INCOME SOURCE ---
class IncomeSourceBase(BaseModel):
    name: str
    net_value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    growth_rate: Optional[float] = 0.0
    account_id: int
    
    is_pre_tax: bool = False
    salary_sacrifice_value: int = 0
    salary_sacrifice_account_id: Optional[int] = None
    employer_pension_contribution: int = 0
    taxable_benefit_value: int = 0

class IncomeSourceCreate(IncomeSourceBase):
    owner_id: int

class IncomeSourceUpdate(BaseModel):
    name: Optional[str] = None
    net_value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    growth_rate: Optional[float] = None
    account_id: Optional[int] = None
    owner_id: Optional[int] = None
    
    is_pre_tax: Optional[bool] = None
    salary_sacrifice_value: Optional[int] = None
    salary_sacrifice_account_id: Optional[int] = None
    employer_pension_contribution: Optional[int] = None
    taxable_benefit_value: Optional[int] = None

class IncomeSource(IncomeSourceBase):
    id: int
    owner_id: int
    model_config = ConfigDict(from_attributes=True)

# --- COST ---
class CostBase(BaseModel):
    name: str
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    inflation_rate: Optional[float] = 0.0
    account_id: Optional[int] = None
    is_recurring: bool = True
    currency: Currency = Currency.GBP

class CostCreate(CostBase):
    scenario_id: int

class CostUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    inflation_rate: Optional[float] = None
    account_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    currency: Optional[Currency] = None

class Cost(CostBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

# --- TRANSFER ---
class TransferBase(BaseModel):
    name: str
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    from_account_id: int
    to_account_id: int
    currency: Currency = Currency.GBP
    show_on_chart: bool = False

class TransferCreate(TransferBase):
    scenario_id: int

class TransferUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    currency: Optional[Currency] = None
    show_on_chart: Optional[bool] = None

class Transfer(TransferBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

# --- FINANCIAL EVENT ---
class FinancialEventBase(BaseModel):
    name: str
    date: date
    value: int
    type: str
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None

class FinancialEventCreate(FinancialEventBase):
    scenario_id: int

class FinancialEventUpdate(BaseModel):
    name: Optional[str] = None
    date: Optional[date] = None
    value: Optional[int] = None
    type: Optional[str] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None

class FinancialEvent(FinancialEventBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

# --- CHART ANNOTATION ---
class ChartAnnotationBase(BaseModel):
    date: date
    label: str
    annotation_type: str = 'info'

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
