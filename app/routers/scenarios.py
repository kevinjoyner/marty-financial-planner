from fastapi import APIRouter, Depends, HTTPException, Query, Body
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import datetime, date
from .. import models, schemas, database, engine, crud
from ..database import get_db

router = APIRouter(prefix="/scenarios", tags=["scenarios"])

def _normalize_legacy_data(data: Dict[str, Any]) -> Dict[str, Any]:
    if "automation_rules" in data:
        for r in data["automation_rules"]:
            if "trigger_value" in r and r["trigger_value"] is not None: r["trigger_value"] = int(r["trigger_value"] * 100)
            if "transfer_value" in r and r["transfer_value"] is not None: r["transfer_value"] = int(r["transfer_value"] * 100)
    if "tax_limits" in data:
        for t in data["tax_limits"]:
            if "amount" in t and t["amount"] is not None: t["amount"] = int(t["amount"] * 100)
    if "accounts" in data:
        for a in data["accounts"]:
            if "starting_balance" in a: a["starting_balance"] = int(a["starting_balance"])
            if "original_loan_amount" in a and a["original_loan_amount"]: a["original_loan_amount"] = int(a["original_loan_amount"])
    if "costs" in data:
        for c in data["costs"]:
            if "value" in c: c["value"] = int(c["value"])
    return data

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
    return crud.create_scenario(db, scenario)

@router.post("/{scenario_id}/fork", response_model=schemas.Scenario)
def fork_scenario(scenario_id: int, req: schemas.ScenarioForkRequest, db: Session = Depends(get_db)):
    new_scen = crud.duplicate_scenario(db, scenario_id, new_name=req.name, overrides=req.overrides)
    if not new_scen: raise HTTPException(404, "Scenario not found")
    if req.description:
        new_scen.description = req.description
        db.commit()
        db.refresh(new_scen)
    return new_scen

@router.post("/import_new", response_model=schemas.Scenario)
def import_new_scenario(scenario_data: schemas.ScenarioImport, is_legacy: bool = Query(False), db: Session = Depends(get_db)):
    raw_data = scenario_data.model_dump()
    clean_data = _normalize_legacy_data(raw_data) if is_legacy else raw_data
    
    # 1. Create the Shell Scenario
    db_scenario = models.Scenario(
        name=clean_data["name"],
        description=clean_data.get("description"),
        start_date=clean_data["start_date"],
        gbp_to_usd_rate=clean_data.get("gbp_to_usd_rate", 1.25)
    )
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)

    # 2. Use Shared CRUD logic to populate children
    return crud.import_scenario_data(db, db_scenario.id, clean_data)

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
    new_scenario = crud.create_scenario(db, schemas.ScenarioCreate(name=f"Restored: {snapshot['name']}", start_date=snapshot['start_date']))
    crud.import_scenario_data(db, new_scenario.id, snapshot)
    
    return new_scenario
