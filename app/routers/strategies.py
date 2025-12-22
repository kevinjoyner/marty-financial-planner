from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/scenarios/{scenario_id}/strategies",
    tags=["strategies"]
)

@router.get("/", response_model=List[schemas.DecumulationStrategy])
def read_strategies(scenario_id: int, db: Session = Depends(get_db)):
    # Verify scenario exists
    if not crud.get_scenario(db, scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
    return crud.get_strategies_by_scenario(db, scenario_id)

@router.post("/", response_model=schemas.DecumulationStrategy)
def create_strategy(scenario_id: int, strategy: schemas.DecumulationStrategyBase, db: Session = Depends(get_db)):
    if not crud.get_scenario(db, scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
    return crud.create_strategy(db, strategy, scenario_id)

@router.put("/{strategy_id}", response_model=schemas.DecumulationStrategy)
def update_strategy(scenario_id: int, strategy_id: int, strategy: schemas.DecumulationStrategyBase, db: Session = Depends(get_db)):
    # Verify scenario exists
    if not crud.get_scenario(db, scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")
        
    db_strat = crud.get_strategy(db, strategy_id)
    if not db_strat or db_strat.scenario_id != scenario_id:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    return crud.update_strategy(db, strategy_id, strategy)

@router.delete("/{strategy_id}", response_model=schemas.DecumulationStrategy)
def delete_strategy(scenario_id: int, strategy_id: int, db: Session = Depends(get_db)):
    if not crud.get_scenario(db, scenario_id):
        raise HTTPException(status_code=404, detail="Scenario not found")

    db_strat = crud.get_strategy(db, strategy_id)
    if not db_strat or db_strat.scenario_id != scenario_id:
        raise HTTPException(status_code=404, detail="Strategy not found")
        
    return crud.delete_strategy(db, strategy_id)
