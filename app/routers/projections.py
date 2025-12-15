from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Optional
import sys

from .. import crud, engine
from ..database import get_db
from ..schemas.projection import Projection, ProjectionRequest

router = APIRouter(
    prefix="/projections",
    tags=["projections"],
)

@router.post("/{scenario_id}/project", response_model=Projection)
def project_scenario(
    scenario_id: int, 
    # Standard Query Param
    months: int = Query(12),
    # Body Payload - OPTIONAL
    payload: Optional[ProjectionRequest] = Body(default=None),
    db: Session = Depends(get_db)
):
    db_scenario = crud.get_scenario(db, scenario_id=scenario_id)
    if db_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")

    final_months = months

    if payload:
        # 1. Apply Overrides
        if payload.overrides:
            engine.apply_simulation_overrides(db_scenario, payload.overrides)
        
        # 2. Determine Duration override
        if payload.simulation_months is not None:
            final_months = payload.simulation_months

    return engine.run_projection(db=db, scenario=db_scenario, months=final_months)
