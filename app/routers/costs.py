from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, database

router = APIRouter(prefix="/api/costs", tags=["costs"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Cost])
def read_costs(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_costs(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.Cost)
def create_cost(cost: schemas.CostCreate, db: Session = Depends(get_db)):
    return crud.create_cost(db=db, cost=cost)

@router.put("/{cost_id}", response_model=schemas.Cost)
def update_cost(cost_id: int, cost: schemas.CostUpdate, db: Session = Depends(get_db)):
    return crud.update_cost(db, cost_id, cost)

@router.delete("/{cost_id}")
def delete_cost(cost_id: int, db: Session = Depends(get_db)):
    return crud.delete_cost(db, cost_id)
