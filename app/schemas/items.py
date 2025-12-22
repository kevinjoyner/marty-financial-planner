from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any
from datetime import date
from ..enums import Cadence, Currency, FinancialEventType

class IncomeSourceBase(BaseModel):
    name: str
    amount: Optional[int] = None 
    net_value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    growth_rate: Optional[float] = 0.0
    account_id: int  # REVERTED: Mandatory
    is_pre_tax: bool = False
    salary_sacrifice_value: int = 0
    salary_sacrifice_account_id: Optional[int] = None # Remains Optional
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

class CostBase(BaseModel):
    name: str
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    growth_rate: Optional[float] = 0.0
    account_id: int # REVERTED: Mandatory
    is_recurring: bool = True
    notes: Optional[str] = None

class CostCreate(CostBase):
    scenario_id: int

class CostUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: Optional[Currency] = None
    account_id: Optional[int] = None
    is_recurring: Optional[bool] = None
    notes: Optional[str] = None

class Cost(CostBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

class TransferBase(BaseModel):
    name: str
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    from_account_id: int # REVERTED: Mandatory
    to_account_id: int   # REVERTED: Mandatory
    show_on_chart: bool = False
    notes: Optional[str] = None

class TransferCreate(TransferBase):
    scenario_id: int

class TransferUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    currency: Optional[Currency] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    show_on_chart: Optional[bool] = None
    notes: Optional[str] = None

class Transfer(TransferBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

class FinancialEventBase(BaseModel):
    name: str
    value: int
    event_date: date
    event_type: FinancialEventType
    currency: Currency = Currency.GBP
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    show_on_chart: bool = False
    notes: Optional[str] = None

class FinancialEventCreate(FinancialEventBase):
    scenario_id: int

class FinancialEventUpdate(BaseModel):
    name: Optional[str] = None
    value: Optional[int] = None
    event_date: Optional[date] = None
    event_type: Optional[FinancialEventType] = None
    currency: Optional[Currency] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    show_on_chart: Optional[bool] = None
    notes: Optional[str] = None

class FinancialEvent(FinancialEventBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

class ChartAnnotationBase(BaseModel):
    date: date
    label: str
    annotation_type: str = "manual"

class ChartAnnotationCreate(ChartAnnotationBase):
    scenario_id: int

class ChartAnnotation(ChartAnnotationBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)
