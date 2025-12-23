from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date
from .items import IncomeSource

class OwnerBase(BaseModel):
    name: str
    notes: Optional[str] = None
    birth_date: Optional[date] = None
    retirement_age: Optional[int] = None

class OwnerCreate(OwnerBase):
    scenario_id: int

class OwnerUpdate(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    birth_date: Optional[date] = None
    retirement_age: Optional[int] = None

class Owner(OwnerBase):
    id: int
    scenario_id: int
    income_sources: List[IncomeSource] = []
    
    model_config = ConfigDict(from_attributes=True)
