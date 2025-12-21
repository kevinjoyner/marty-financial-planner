from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import date

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

class ProjectionDataPoint(BaseModel):
    date: date
    balance: float
    account_balances: Dict[int, float] # AccountID -> Balance (Float/Pounds)
    flows: Dict[int, ProjectionFlows]  # AccountID -> Flows

class ProjectionWarning(BaseModel):
    date: date
    account_id: Optional[int] = None
    message: str
    source_type: str
    source_id: Optional[int] = None

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
