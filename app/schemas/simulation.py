from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union

class SimulationOverrideBase(BaseModel):
    type: str # 'account', 'income', 'cost', 'transfer', etc.
    id: int
    field: str
    value: Any

class SimulationPayload(BaseModel):
    simulation_months: Optional[int] = 60
    overrides: Optional[List[SimulationOverrideBase]] = []
