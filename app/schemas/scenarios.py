from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date
from .owners import Owner
from .accounts import Account
from .items import Cost, Transfer, FinancialEvent, ChartAnnotation
from .rules import AutomationRule
from .strategies import DecumulationStrategy

# TaxLimit schema usually simple enough to inline or put in items
class TaxLimitBase(BaseModel):
    name: str
    amount: int
    wrappers: List[str]
    account_types: Optional[List[str]] = None
    start_date: date
    end_date: Optional[date] = None
    frequency: str = "Annually"

class TaxLimitCreate(TaxLimitBase):
    scenario_id: int

class TaxLimit(TaxLimitBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    gbp_to_usd_rate: float = 1.25

class ScenarioCreate(ScenarioBase):
    pass

class ScenarioUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_date: Optional[date] = None
    gbp_to_usd_rate: Optional[float] = None

class Scenario(ScenarioBase):
    id: int
    owners: List[Owner] = []
    accounts: List[Account] = []
    costs: List[Cost] = []
    transfers: List[Transfer] = []
    financial_events: List[FinancialEvent] = []
    tax_limits: List[TaxLimit] = []
    automation_rules: List[AutomationRule] = []
    chart_annotations: List[ChartAnnotation] = []
    decumulation_strategies: List[DecumulationStrategy] = []
    
    model_config = ConfigDict(from_attributes=True)
