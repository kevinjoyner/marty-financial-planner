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

class ImportIncomeSource(BaseModel):
    name: str
    amount: Optional[int] = None
    net_value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    growth_rate: float = 0.0
    is_pre_tax: bool = False
    salary_sacrifice_value: int = 0
    taxable_benefit_value: int = 0
    employer_pension_contribution: int = 0
    notes: Optional[str] = None
    
    # Relations (ID only)
    account_id: Optional[int] = None
    salary_sacrifice_account_id: Optional[int] = None

class ImportOwner(BaseModel):
    id: Optional[int] = None
    name: str
    birth_date: Optional[date] = None
    retirement_age: int = 65
    notes: Optional[str] = None
    income_sources: List[ImportIncomeSource] = []

class ImportAccount(BaseModel):
    id: Optional[int] = None
    name: str
    notes: Optional[str] = None
    account_type: AccountType
    tax_wrapper: TaxWrapper = TaxWrapper.NONE
    currency: Currency = Currency.GBP
    starting_balance: int
    min_balance: Optional[int] = None
    interest_rate: float = 0.0
    book_cost: Optional[int] = None
    
    # Mortgage
    original_loan_amount: Optional[int] = None
    mortgage_start_date: Optional[date] = None
    amortisation_period_years: Optional[int] = None
    fixed_interest_rate: Optional[float] = None
    fixed_rate_period_years: Optional[int] = None
    payment_from_account_id: Optional[int] = None
    is_primary_account: bool = False
    
    # RSU
    grant_date: Optional[date] = None
    vesting_schedule: Optional[List[Dict[str, Any]]] = None 
    vesting_cadence: Optional[str] = "monthly"
    unit_price: Optional[int] = None
    rsu_target_account_id: Optional[int] = None
    
    # Owners linkage
    owners: List[Any] = []

class ImportCost(BaseModel):
    name: str
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    growth_rate: float = 0.0
    is_recurring: bool = True
    notes: Optional[str] = None
    account_id: int

class ImportTransfer(BaseModel):
    name: str
    value: int
    cadence: Cadence
    start_date: date
    end_date: Optional[date] = None
    currency: Currency = Currency.GBP
    show_on_chart: bool = False
    notes: Optional[str] = None
    from_account_id: int
    to_account_id: int

class ImportFinancialEvent(BaseModel):
    name: str
    value: int
    event_date: date
    event_type: str
    currency: Currency = Currency.GBP
    show_on_chart: bool = False
    notes: Optional[str] = None
    from_account_id: Optional[int] = None
    to_account_id: Optional[int] = None

class ImportTaxLimit(BaseModel):
    name: str
    amount: int
    wrappers: List[str]
    account_types: Optional[List[str]] = None
    start_date: date
    end_date: Optional[date] = None
    frequency: str = "Annually"

class ImportAutomationRule(BaseModel):
    name: str
    rule_type: str
    source_account_id: int
    target_account_id: Optional[int] = None
    trigger_value: int
    transfer_value: Optional[int] = None
    transfer_cap: Optional[int] = None
    cadence: str = "monthly"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    priority: int = 0
    notes: Optional[str] = None

class ImportChartAnnotation(BaseModel):
    date: date
    label: str
    annotation_type: str = "manual"

class ImportDecumulationStrategy(BaseModel):
    name: str
    strategy_type: str = "Standard"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    enabled: bool = True

class ScenarioImport(BaseModel):
    name: str
    description: Optional[str] = None
    start_date: date
    gbp_to_usd_rate: Optional[float] = 1.25
    
    owners: List[ImportOwner] = []
    accounts: List[ImportAccount] = []
    costs: List[ImportCost] = []
    transfers: List[ImportTransfer] = []
    financial_events: List[ImportFinancialEvent] = []
    tax_limits: List[ImportTaxLimit] = []
    automation_rules: List[ImportAutomationRule] = []
    chart_annotations: List[ImportChartAnnotation] = []
    decumulation_strategies: List[ImportDecumulationStrategy] = []
