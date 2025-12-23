from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, database

router = APIRouter(prefix="/api/income_sources", tags=["income_sources"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.IncomeSource])
def read_income_sources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_income_sources(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.IncomeSource)
def create_income_source(income_source: schemas.IncomeSourceCreate, db: Session = Depends(get_db)):
    return crud.create_income_source(db=db, income_source=income_source)

@router.put("/{income_source_id}", response_model=schemas.IncomeSource)
def update_income_source(income_source_id: int, income_source: schemas.IncomeSourceUpdate, db: Session = Depends(get_db)):
    return crud.update_income_source(db, income_source_id, income_source)

@router.delete("/{income_source_id}")
def delete_income_source(income_source_id: int, db: Session = Depends(get_db)):
    return crud.delete_income_source(db, income_source_id)
