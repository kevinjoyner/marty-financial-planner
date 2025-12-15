from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/costs",
    tags=["costs"],
)

@router.post("/", response_model=schemas.Cost)
def create_cost(cost: schemas.CostCreate, db: Session = Depends(get_db)):
    crud.create_scenario_snapshot(db, cost.scenario_id, f"Create Cost: {cost.name}")
    db_scenario = crud.get_scenario(db, scenario_id=cost.scenario_id)
    if db_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    db_account = crud.get_account(db, account_id=cost.account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    return crud.create_cost(db=db, cost=cost)

@router.get("/", response_model=list[schemas.Cost])
def read_costs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    costs = crud.get_costs(db, skip=skip, limit=limit)
    return costs

@router.get("/{cost_id}", response_model=schemas.Cost)
def read_cost(cost_id: int, db: Session = Depends(get_db)):
    db_cost = crud.get_cost(db, cost_id=cost_id)
    if db_cost is None:
        raise HTTPException(status_code=404, detail="Cost not found")
    return db_cost

@router.put("/{cost_id}", response_model=schemas.Cost)
def update_cost(cost_id: int, cost: schemas.CostUpdate, db: Session = Depends(get_db)):
    db_cost = crud.get_cost(db, cost_id=cost_id)
    if db_cost:
        crud.create_scenario_snapshot(db, db_cost.scenario_id, f"Update Cost: {db_cost.name}")

    db_cost = crud.update_cost(db, cost_id=cost_id, cost=cost)
    if db_cost is None:
        raise HTTPException(status_code=404, detail="Cost not found")
    return db_cost

@router.delete("/{cost_id}", response_model=schemas.Cost)
def delete_cost(cost_id: int, db: Session = Depends(get_db)):
    db_cost = crud.get_cost(db, cost_id=cost_id)
    if db_cost:
        crud.create_scenario_snapshot(db, db_cost.scenario_id, f"Delete Cost: {db_cost.name}")

    db_cost = crud.delete_cost(db, cost_id=cost_id)
    if db_cost is None:
        raise HTTPException(status_code=404, detail="Cost not found")
    return db_cost
