from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import date

# --- OUTPUT SCHEMAS ---
from .types import Money

# --- OUTPUT SCHEMAS ---
class ProjectionFlows(BaseModel):
    income: Money = 0
    costs: Money = 0
    transfers_in: Money = 0
    transfers_out: Money = 0
    mortgage_payments_out: Money = 0
    mortgage_repayments_in: Money = 0
    interest: Money = 0
    events: Money = 0
    tax: Money = 0
    cgt: Money = 0
    employer_contribution: Money = 0
    growth: Money = 0

class ProjectionWarning(BaseModel):
    date: date
    account_id: int
    message: str
    source_type: str = "system"
    source_id: int = 0

class ProjectionAnnotation(BaseModel):
    date: date
    label: str
    type: str = "default" 

class RuleExecutionLog(BaseModel):
    date: date
    rule_type: str
    action: str
    amount: Money
    source_account: str
    target_account: str
    reason: str

class MortgageStat(BaseModel):
    year_start: int
    rule_id: int
    rule_name: str
    allowance: Money
    paid: Money
    headroom: Money

class ProjectionDataPoint(BaseModel):
    date: date
    balance: Money
    liquid_assets: Money
    account_balances: Dict[int, Money]
    flows: Dict[int, ProjectionFlows] = {}

class Projection(BaseModel):
    data_points: List[ProjectionDataPoint]
    warnings: List[ProjectionWarning] = []
    annotations: List[ProjectionAnnotation] = []
    rule_logs: List[RuleExecutionLog] = [] 
    mortgage_stats: List[MortgageStat] = []

# Added to support the Engine's return type which includes metadata
class ProjectionResult(Projection):
    metadata: Optional[Dict[str, Any]] = {}

# --- INPUT SCHEMAS (SIMULATION) ---
class SimulationOverride(BaseModel):
    type: str  
    id: int
    field: str 
    value: Any 

class ProjectionRequest(BaseModel):
    simulation_months: Optional[int] = None
    overrides: List[SimulationOverride] = []
