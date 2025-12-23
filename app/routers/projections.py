from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from .. import crud, schemas, database, models
from ..engine import core as engine

router = APIRouter(prefix="/api/projections", tags=["projections"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/{scenario_id}/project", response_model=schemas.ProjectionResult)
def project_scenario(
    scenario_id: int, 
    payload: schemas.SimulationPayload,
    db: Session = Depends(get_db)
):
    db_scenario = crud.get_scenario(db, scenario_id=scenario_id)
    if not db_scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Calculate months from start date to today + simulation_years? 
    # Or just use payload months.
    final_months = payload.simulation_months or 60 # Default 5 years
    
    return engine.run_projection(db=db, scenario=db_scenario, months=final_months, overrides=payload.overrides)
