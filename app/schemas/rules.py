from pydantic import BaseModel, ConfigDict, Field
from typing import Optional
from datetime import date
from ..enums import RuleType, Cadence

class AutomationRuleBase(BaseModel):
    name: Optional[str] = "New Rule" 
    priority: Optional[int] = 0
    rule_type: RuleType
    source_account_id: Optional[int] = None
    target_account_id: Optional[int] = None
    trigger_value: float 
    transfer_value: Optional[float] = None 
    transfer_cap: Optional[float] = None
    start_date: Optional[date] = None      
    end_date: Optional[date] = None
    
    # FIX: Make cadence Optional to handle legacy NULLs
    cadence: Optional[Cadence] = Cadence.MONTHLY
    
    notes: Optional[str] = None

class AutomationRuleCreate(AutomationRuleBase):
    scenario_id: int

class AutomationRuleUpdate(BaseModel):
    name: Optional[str] = None
    priority: Optional[int] = None
    rule_type: Optional[RuleType] = None
    source_account_id: Optional[int] = None
    target_account_id: Optional[int] = None
    trigger_value: Optional[float] = None
    transfer_value: Optional[float] = None
    transfer_cap: Optional[float] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    cadence: Optional[Cadence] = None
    notes: Optional[str] = None

class AutomationRule(AutomationRuleBase):
    id: int
    scenario_id: int
    model_config = ConfigDict(from_attributes=True)
