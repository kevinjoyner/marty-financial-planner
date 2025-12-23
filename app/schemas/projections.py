from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

class ProjectionDataPoint(BaseModel):
    date: date
    balance: int
    liquid_assets: int
    account_balances: Dict[int, int]
    flows: Dict[int, Dict[str, float]]

class ProjectionAnnotation(BaseModel):
    date: date
    label: str
    type: str

class ProjectionWarning(BaseModel):
    date: date
    message: str
    type: str

class ProjectionResult(BaseModel):
    data_points: List[ProjectionDataPoint]
    annotations: List[ProjectionAnnotation] = []
    warnings: List[ProjectionWarning] = []
    rule_logs: List[Any] = [] # Simplified for now
