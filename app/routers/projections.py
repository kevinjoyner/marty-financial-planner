from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from ..database import get_db
from .. import models, schemas, crud, engine

router = APIRouter()

class ProjectionRequest(schemas.BaseModel):
    months: Optional[int] = 120
    overrides: Optional[List[schemas.SimulationOverride]] = []

@router.post("/projections/{scenario_id}/project", response_model=schemas.Projection)
def run_projection_endpoint(
    scenario_id: int, 
    request: Optional[ProjectionRequest] = None,
    months: int = Query(120),
    db: Session = Depends(get_db)
):
    # Support both Query param and JSON body for months
    sim_months = request.months if request and request.months else months
    
    # 1. Duplicate for temp simulation
    # We use the duplicate functionality to create a transient scenario object
    # But we don't save it to DB if we can avoid it. 
    # However, our engine runs on DB models. 
    # For now, we apply overrides to the LIVE object in memory (risky but typical for this pattern)
    # OR we make a transient copy.
    
    scenario = crud.scenarios.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    # Apply overrides in-memory for this request context only
    # Note: 'apply_simulation_overrides' modifies the object in place. 
    # Since we fetched it from this session, we must be careful NOT to commit these changes.
    if request and request.overrides:
        engine.apply_simulation_overrides(scenario, request.overrides)
        
    result = engine.run_projection(db, scenario, sim_months)
    
    # Rollback to discard any override changes to the DB session objects
    db.rollback() 
    
    return result
