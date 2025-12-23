from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from ..enums import AccountType, Cadence, Currency, TaxWrapper
from .shared import AccountBase, OwnerBase
from .items import Cost, FinancialEvent, Transfer, ChartAnnotation
from .rules import AutomationRule
from .owners import Owner, IncomeSource
from .accounts import Account

class SimulationOverrideBase(BaseModel):
    type: str  
    id: int
    field: str 
    value: Any

class ScenarioForkRequest(BaseModel):
    name: str
    description: Optional[str] = None
    overrides: List[SimulationOverrideBase] = []

class TaxLimitBase(BaseModel):
    name: str
    amount: int
    wrappers: List[str]
    account_types: Optional[List[str]] = None 
    start_date: date
    end_date: Optional[date] = None
    frequency: Optional[str] = "Annually"

class TaxLimit(TaxLimitBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

class DecumulationStrategyBase(BaseModel):
    name: str
    strategy_type: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    enabled: bool = True

class DecumulationStrategy(DecumulationStrategyBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    start_date: date
    gbp_to_usd_rate: float = 1.25

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    start_date: Optional[date] = None
    gbp_to_usd_rate: Optional[float] = None

class Scenario(ScenarioBase):
    id: int
    owners: List[Owner] = []
    accounts: List[Account] = []
    costs: List[Cost] = []
    financial_events: List[FinancialEvent] = []
    transfers: List[Transfer] = []
    automation_rules: List[AutomationRule] = []
    tax_limits: List[TaxLimit] = [] 
    chart_annotations: List[ChartAnnotation] = []
    decumulation_strategies: List[DecumulationStrategy] = []
    model_config = ConfigDict(from_attributes=True)

class ScenarioHistory(BaseModel):
    id: int
    scenario_id: int
    timestamp: datetime
    action_description: str
    model_config = ConfigDict(from_attributes=True)

class ScenarioImport(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    gbp_to_usd_rate: Optional[float] = 1.25
    
    owners: List[Dict[str, Any]] = []
    accounts: List[Dict[str, Any]] = []
    costs: List[Dict[str, Any]] = []
    transfers: List[Dict[str, Any]] = []
    financial_events: List[Dict[str, Any]] = []
    tax_limits: List[Dict[str, Any]] = []
    automation_rules: List[Dict[str, Any]] = []
    chart_annotations: List[Dict[str, Any]] = []
    decumulation_strategies: List[Dict[str, Any]] = []
