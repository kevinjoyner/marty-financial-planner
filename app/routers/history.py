from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas, crud

router = APIRouter()

@router.get("/scenarios/{scenario_id}/history", response_model=List[schemas.ScenarioHistory])
def get_scenario_history(scenario_id: int, db: Session = Depends(get_db)):
    # Assuming relationship or simple query
    # We defined a relationship 'history' on Scenario
    scenario = crud.scenarios.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    # Sort by timestamp desc
    return sorted(scenario.history, key=lambda x: x.timestamp, reverse=True)

@router.post("/history/{history_id}/restore")
def restore_scenario(history_id: int, db: Session = Depends(get_db)):
    success = crud.scenarios.restore_scenario_from_history(db, history_id)
    if not success:
        raise HTTPException(status_code=400, detail="Restore failed or history item not found")
    return {"status": "restored"}
