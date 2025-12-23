from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, date
from .. import models, schemas, database, engine, crud
from ..database import get_db
import os

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

from ..schemas.legacy import normalize_legacy_data

@router.get("/", response_model=List[schemas.Scenario])
def read_scenarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_scenarios(db, skip=skip, limit=limit)

@router.get("/{scenario_id}", response_model=schemas.Scenario)
def read_scenario(scenario_id: int, db: Session = Depends(get_db)):
    db_scenario = crud.get_scenario(db, scenario_id)
    if not db_scenario: raise HTTPException(status_code=404, detail="Scenario not found")
    return db_scenario

@router.post("/", response_model=schemas.Scenario)
def create_scenario(scenario: schemas.ScenarioCreate, db: Session = Depends(get_db)):
    # Optional: Apply to manually created scenarios too? 
    # For now, applying mainly to imports as requested, but good consistency to have here.
    if os.getenv("ENVIRONMENT") == "development" and not scenario.name.startswith("dev_"):
        scenario.name = f"dev_{scenario.name}"
    return crud.create_scenario(db, scenario)

@router.post("/{scenario_id}/fork", response_model=schemas.Scenario)
def fork_scenario(scenario_id: int, req: schemas.ScenarioForkRequest, db: Session = Depends(get_db)):
    new_name = req.name
    if os.getenv("ENVIRONMENT") == "development" and not new_name.startswith("dev_"):
        new_name = f"dev_{new_name}"
        
    new_scen = crud.duplicate_scenario(db, scenario_id, new_name=new_name, overrides=req.overrides)
    if not new_scen: raise HTTPException(404, "Scenario not found")
    if req.description:
        new_scen.description = req.description
        db.commit()
        db.refresh(new_scen)
    return new_scen

@router.post("/import_new", response_model=schemas.Scenario)
def import_new_scenario(request_data: Dict[str, Any] = Body(...), is_legacy: bool = Query(False), db: Session = Depends(get_db)):
    # 1. Legacy Normalization (Before Validation)
    if is_legacy:
        # We process the raw dict to fix types (Float -> Int Pence)
        clean_data = normalize_legacy_data(request_data)
    else:
        clean_data = request_data

    # 2. Strict Validation using Pydantic
    try:
        scenario_import = schemas.ScenarioImport.model_validate(clean_data)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"Validation Error: {str(e)}")
    
    # DEV ENVIRONMENT TAGGING
    if os.getenv("ENVIRONMENT") == "development":
        if not scenario_import.name.startswith("dev_"):
            scenario_import.name = f"dev_{scenario_import.name}"
    
    # 3. Create the Shell Scenario
    db_scenario = models.Scenario(
        name=scenario_import.name,
        description=scenario_import.description,
        start_date=scenario_import.start_date,
        gbp_to_usd_rate=scenario_import.gbp_to_usd_rate
    )
    db.add(db_scenario)
    # db.commit() REMOVED to enable single transaction in CRUD
    db.flush()
    db.refresh(db_scenario)

    # 4. Use Shared CRUD logic to populate children
    # We pass the Pydantic object now, not the dict
    return crud.import_scenario_data(db, db_scenario.id, scenario_import)

@router.post("/{scenario_id}/duplicate", response_model=schemas.Scenario)
def duplicate_scenario(scenario_id: int, db: Session = Depends(get_db)):
    new_scen = crud.duplicate_scenario(db, scenario_id)
    if not new_scen: raise HTTPException(404, "Scenario not found")
    return new_scen

@router.delete("/{scenario_id}")
def delete_scenario(scenario_id: int, db: Session = Depends(get_db)):
    crud.delete_scenario(db, scenario_id)
    return {"ok": True}

@router.put("/{scenario_id}", response_model=schemas.Scenario)
def update_scenario(scenario_id: int, scenario: schemas.ScenarioUpdate, db: Session = Depends(get_db)):
    db_scenario = crud.update_scenario(db, scenario_id, scenario)
    if not db_scenario: raise HTTPException(status_code=404, detail="Scenario not found")
    return db_scenario

# --- HISTORY ROUTES ---
@router.get("/{scenario_id}/history", response_model=List[schemas.ScenarioHistory])
def get_history(scenario_id: int, db: Session = Depends(get_db)):
    return crud.get_scenario_history(db, scenario_id)

@router.post("/{scenario_id}/history/{history_id}/restore", response_model=schemas.Scenario)
def restore_history(scenario_id: int, history_id: int, db: Session = Depends(get_db)):
    history_item = crud.get_history_item(db, history_id)
    if not history_item: raise HTTPException(404, "History item not found")
    
    snapshot = history_item.snapshot_data
    # Note: We probably don't need to re-tag history restores as they are likely already tagged or internal
    new_scenario = crud.create_scenario(db, schemas.ScenarioCreate(name=f"Restored: {snapshot['name']}", start_date=snapshot['start_date']))
    crud.import_scenario_data(db, new_scenario.id, snapshot)
    
    return new_scenario
