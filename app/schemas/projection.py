from pydantic import BaseModel
from typing import Dict, List, Any, Optional
from datetime import date

# --- OUTPUT SCHEMAS ---
class ProjectionFlows(BaseModel):
    income: float = 0
    costs: float = 0
    transfers_in: float = 0
    transfers_out: float = 0
    mortgage_payments_out: float = 0
    mortgage_repayments_in: float = 0
    interest: float = 0
    events: float = 0
    tax: float = 0
    cgt: float = 0
    employer_contribution: float = 0

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

class ProjectionDataPoint(BaseModel):
    date: date
    balance: float
    account_balances: Dict[int, float]
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
