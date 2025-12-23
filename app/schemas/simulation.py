from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import date

class SimulationPayload(BaseModel):
    scenario_id: int
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    overrides: Optional[List[Dict[str, Any]]] = None
