from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas, crud

router = APIRouter()

@router.get("/scenarios/", response_model=List[schemas.Scenario])
def read_scenarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.scenarios.get_scenarios(db, skip=skip, limit=limit)

@router.get("/scenarios/{scenario_id}", response_model=schemas.Scenario)
def read_scenario(scenario_id: int, db: Session = Depends(get_db)):
    db_scenario = crud.scenarios.get_scenario(db, scenario_id=scenario_id)
    if db_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return db_scenario

@router.post("/scenarios/", response_model=schemas.Scenario)
def create_scenario(scenario: schemas.ScenarioCreate, db: Session = Depends(get_db)):
    return crud.scenarios.create_scenario(db=db, scenario=scenario)

@router.put("/scenarios/{scenario_id}", response_model=schemas.Scenario)
def update_scenario(scenario_id: int, scenario: schemas.ScenarioUpdate, db: Session = Depends(get_db)):
    return crud.scenarios.update_scenario(db, scenario_id, scenario)

@router.delete("/scenarios/{scenario_id}")
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    success = crud.scenarios.delete_scenario(db, scenario_id)
    if not success:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return {"ok": True}

@router.post("/scenarios/{scenario_id}/duplicate", response_model=schemas.Scenario)
def duplicate_scenario(scenario_id: int, db: Session = Depends(get_db)):
    new_scenario = crud.scenarios.duplicate_scenario(db, scenario_id)
    if not new_scenario:
        raise HTTPException(status_code=404, detail="Original scenario not found")
    return new_scenario

@router.post("/scenarios/import_new", response_model=schemas.Scenario)
def import_new_scenario(scenario_data: schemas.ScenarioImport, db: Session = Depends(get_db)):
    raw_data = scenario_data.model_dump()
    
    # Create Shell
    db_scenario = models.Scenario(
        name=raw_data["name"],
        description=raw_data.get("description"),
        start_date=raw_data["start_date"],
        gbp_to_usd_rate=raw_data.get("gbp_to_usd_rate", 1.25)
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    
    # Populate
    return crud.scenarios.import_scenario_data(db, db_scenario.id, raw_data)
