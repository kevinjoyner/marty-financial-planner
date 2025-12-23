from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import date
from ..enums import Cadence, Currency, FinancialEventType

# COSTS
class CostBase(BaseModel):
    name: str
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    growth_rate: Optional[float] = 0.0
    account_id: int
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

# TRANSFERS
class TransferBase(BaseModel):
    name: str
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    from_account_id: int
    to_account_id: int
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

# EVENTS
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

# ANNOTATIONS
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
