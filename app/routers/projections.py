from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db
from .. import models, schemas, engine, crud

router = APIRouter()

class ProjectionRequest(BaseModel):
    months: int = 600
    overrides: Optional[List[schemas.SimulationOverride]] = []

@router.post("/projections/{scenario_id}/project", response_model=schemas.Projection)
def project_scenario(scenario_id: int, request: ProjectionRequest = None, db: Session = Depends(get_db)):
    # Handle direct query param calls (legacy fallback) or body
    months = request.months if request else 120
    overrides = request.overrides if request else []
    
    scenario = crud.scenarios.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    return engine.run_projection(db, scenario, months, overrides)
