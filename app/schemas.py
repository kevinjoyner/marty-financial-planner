from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import date
from . import enums

# --- BASE CLASSES ---
class TaxLimitBase(BaseModel):
    name: str
    amount: int
    wrappers: List[str]
    account_types: List[str] = []
    start_date: date
    end_date: Optional[date] = None
    frequency: str = "Annually"

class AutomationRuleBase(BaseModel):
    name: str
    rule_type: enums.RuleType
    source_account_id: int
    target_account_id: Optional[int] = None
    trigger_value: Optional[float] = 0
    transfer_value: Optional[float] = None
    priority: int = 0
    cadence: enums.Cadence = enums.Cadence.MONTHLY
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class FinancialEventBase(BaseModel):
    name: str
    value: int
    event_date: date
    event_type: enums.FinancialEventType
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None
    show_on_chart: bool = True

class IncomeSourceBase(BaseModel):
    name: str
    account_id: int
    owner_id: int
    net_value: int
    cadence: enums.Cadence
    start_date: date
    end_date: Optional[date] = None
    is_pre_tax: bool = False
    salary_sacrifice_value: Optional[int] = 0
    salary_sacrifice_account_id: Optional[int] = None
    taxable_benefit_value: Optional[int] = 0
    employer_pension_contribution: Optional[int] = 0
    currency: enums.Currency = enums.Currency.GBP
    notes: Optional[str] = None

class CostBase(BaseModel):
    name: str
    account_id: int
    value: int
    cadence: enums.Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: enums.Currency = enums.Currency.GBP

class TransferBase(BaseModel):
    name: str
    from_account_id: int
    to_account_id: int
    value: int
    cadence: enums.Cadence
    start_date: date
    end_date: Optional[date] = None
    show_on_chart: bool = False

class AccountBase(BaseModel):
    name: str
    account_type: enums.AccountType
    tax_wrapper: Optional[enums.TaxWrapper] = enums.TaxWrapper.NONE
    starting_balance: float
    min_balance: Optional[float] = 0
    interest_rate: Optional[float] = 0.0
    book_cost: Optional[float] = None
    currency: enums.Currency = enums.Currency.GBP
    # Mortgage specific
    original_loan_amount: Optional[float] = None
    mortgage_start_date: Optional[date] = None
    amortisation_period_years: Optional[int] = None
    fixed_interest_rate: Optional[float] = None
    fixed_rate_period_years: Optional[int] = None
    payment_from_account_id: Optional[int] = None
    # RSU specific
    unit_price: Optional[float] = None
    grant_date: Optional[date] = None
    vesting_schedule: Optional[List[Dict[str, Any]]] = None
    rsu_target_account_id: Optional[int] = None
    notes: Optional[str] = None

class OwnerBase(BaseModel):
    name: str
    birth_date: date
    retirement_age: Optional[int] = 65

class ScenarioBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    gbp_to_usd_rate: float = 1.25

# --- CREATE/UPDATE/READ ---

class TaxLimitCreate(TaxLimitBase): pass
class TaxLimitUpdate(TaxLimitBase): pass
class TaxLimit(TaxLimitBase):
    id: int
    scenario_id: int
    class Config: from_attributes = True

class AutomationRuleCreate(AutomationRuleBase): pass
class AutomationRuleUpdate(AutomationRuleBase): pass
class AutomationRule(AutomationRuleBase):
    id: int
    scenario_id: int
    class Config: from_attributes = True

class FinancialEventCreate(FinancialEventBase): pass
class FinancialEventUpdate(FinancialEventBase): pass
class FinancialEvent(FinancialEventBase):
    id: int
    scenario_id: int
    class Config: from_attributes = True

class IncomeSourceCreate(IncomeSourceBase): pass
class IncomeSourceUpdate(IncomeSourceBase): pass
class IncomeSource(IncomeSourceBase):
    id: int
    class Config: from_attributes = True

class CostCreate(CostBase): pass
class CostUpdate(CostBase): pass
class Cost(CostBase):
    id: int
    scenario_id: int
    class Config: from_attributes = True

class TransferCreate(TransferBase): pass
class TransferUpdate(TransferBase): pass
class Transfer(TransferBase):
    id: int
    scenario_id: int
    class Config: from_attributes = True

class AccountCreate(AccountBase):
    owner_ids: List[int] = []  # Explicitly allow owner_ids on creation

class AccountUpdate(AccountBase):
    owner_ids: List[int] = []

class Account(AccountBase):
    id: int
    scenario_id: int
    owners: List[OwnerBase] = [] # Read-only view of owners
    class Config: from_attributes = True

class OwnerCreate(OwnerBase): pass
class OwnerUpdate(OwnerBase): pass
class Owner(OwnerBase):
    id: int
    scenario_id: int
    income_sources: List[IncomeSource] = []
    class Config: from_attributes = True

class ChartAnnotation(BaseModel):
    date: date
    label: str
    annotation_type: str

class ScenarioCreate(ScenarioBase): pass
class ScenarioUpdate(ScenarioBase): pass
class Scenario(ScenarioBase):
    id: int
    created_at: datetime = None
    accounts: List[Account] = []
    owners: List[Owner] = []
    income_sources: List[IncomeSource] = [] # Legacy accessor? No, accessed via Owners usually
    costs: List[Cost] = []
    transfers: List[Transfer] = []
    financial_events: List[FinancialEvent] = []
    automation_rules: List[AutomationRule] = []
    tax_limits: List[TaxLimit] = []
    chart_annotations: List[ChartAnnotation] = []
    
    class Config: from_attributes = True

# --- API SPECIFIC ---
class ProjectionDataPoint(BaseModel):
    date: date
    balance: int
    account_balances: Dict[int, int]
    flows: Dict[str, Any]

class ProjectionWarning(BaseModel):
    date: date
    account_id: Optional[int]
    message: str
    source_type: str
    source_id: Optional[int]

class RuleExecutionLog(BaseModel):
    date: date
    rule_type: str
    action: str
    amount: float
    source_account: str
    target_account: str
    reason: str

class MortgageStat(BaseModel):
    year_start: int
    rule_id: int
    rule_name: str
    allowance: float
    paid: float
    headroom: float

class ProjectionAnnotation(BaseModel):
    date: date
    label: str
    type: str

class Projection(BaseModel):
    data_points: List[ProjectionDataPoint]
    warnings: List[ProjectionWarning]
    rule_logs: List[RuleExecutionLog]
    mortgage_stats: List[MortgageStat]
    annotations: List[ProjectionAnnotation]

class SimulationOverride(BaseModel):
    id: str # format "type-realId-field"
    type: str
    field: str
    value: Any

class ScenarioForkRequest(BaseModel):
    name: str
    description: Optional[str] = None
    overrides: List[SimulationOverride]

class ScenarioImport(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    gbp_to_usd_rate: float = 1.25
    accounts: List[Dict[str, Any]] = []
    owners: List[Dict[str, Any]] = []
    costs: List[Dict[str, Any]] = []
    transfers: List[Dict[str, Any]] = []
    financial_events: List[Dict[str, Any]] = []
    automation_rules: List[Dict[str, Any]] = []
    tax_limits: List[Dict[str, Any]] = []

class ScenarioHistory(BaseModel):
    id: int
    scenario_id: int
    timestamp: datetime
    change_summary: str
    snapshot_data: Dict[str, Any]
    class Config: from_attributes = True
