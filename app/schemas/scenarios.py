from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import date, datetime
from ..enums import AccountType, Cadence, Currency, TaxWrapper
from .shared import AccountBase, OwnerBase
# Import basics, but we will define ChartAnnotation locally to be safe
from .items import IncomeSource, Cost, FinancialEvent, Transfer
from .rules import AutomationRule

class ChartAnnotation(BaseModel):
    id: int
    scenario_id: int
    date: date
    label: str
    annotation_type: str = "manual"
    model_config = ConfigDict(from_attributes=True)

class SimulationOverride(BaseModel):
    type: str  
    id: int
    field: str 
    value: Any

class ScenarioForkRequest(BaseModel):
    name: str
    description: Optional[str] = None
    overrides: List[SimulationOverride] = []

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

class AccountCreate(AccountBase):
    owner_ids: List[int]
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
    rsu_target_account_id: Optional[int] = None
    vesting_schedule: Optional[List[dict]] = None
    grant_date: Optional[date] = None 
    unit_price: Optional[int] = None
    owner_ids: Optional[List[int]] = None

class OwnerInAccount(OwnerBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class Account(AccountBase):
    id: int
    owners: List[OwnerInAccount] = []
    model_config = ConfigDict(from_attributes=True)

class AccountInOwner(AccountBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class OwnerCreate(OwnerBase):
    scenario_id: int

class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    scenario_id: Optional[int] = None
    birth_date: Optional[date] = None
    retirement_age: Optional[int] = None

class Owner(OwnerBase):
    id: int
    accounts: List[AccountInOwner] = []
    income_sources: List[IncomeSource] = []
    model_config = ConfigDict(from_attributes=True)

# --- DECUMULATION STRATEGIES ---
# FIX: Make everything optional to handle potential bad data in DB
class DecumulationStrategyBase(BaseModel):
    name: Optional[str] = "Automated Decumulation" 
    strategy_type: Optional[str] = "automated"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    enabled: Optional[bool] = True

class DecumulationStrategyCreate(DecumulationStrategyBase):
    scenario_id: int

class DecumulationStrategyUpdate(BaseModel):
    name: Optional[str] = None
    strategy_type: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    enabled: Optional[bool] = None

class DecumulationStrategy(DecumulationStrategyBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)

# --- SCENARIO ---
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
