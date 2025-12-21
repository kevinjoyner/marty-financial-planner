from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date
from ..enums import RuleType, Cadence

class AutomationRuleBase(BaseModel):
    name: str
    scenario_id: int
    rule_type: RuleType
    source_account_id: int
    target_account_id: Optional[int] = None
    trigger_value: int = 0
    transfer_value: Optional[float] = None
    transfer_cap: Optional[int] = None
    priority: int = 0
    cadence: Cadence = Cadence.MONTHLY
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

class AutomationRuleCreate(AutomationRuleBase):
    pass

class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    rule_type: Optional[RuleType] = None
    source_account_id: Optional[int] = None
    target_account_id: Optional[int] = None
    trigger_value: Optional[int] = None
    transfer_value: Optional[float] = None
    transfer_cap: Optional[int] = None
    priority: Optional[int] = None
    cadence: Optional[Cadence] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    notes: Optional[str] = None

class AutomationRule(AutomationRuleBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
