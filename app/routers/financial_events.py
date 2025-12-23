from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, database

router = APIRouter(prefix="/api/financial_events", tags=["financial_events"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.FinancialEvent])
def read_financial_events(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_financial_events(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.FinancialEvent)
def create_financial_event(event: schemas.FinancialEventCreate, db: Session = Depends(get_db)):
    return crud.create_financial_event(db=db, event=event)

@router.put("/{event_id}", response_model=schemas.FinancialEvent)
def update_financial_event(event_id: int, event: schemas.FinancialEventUpdate, db: Session = Depends(get_db)):
    return crud.update_financial_event(db, event_id, event)

@router.delete("/{event_id}")
def delete_financial_event(event_id: int, db: Session = Depends(get_db)):
    return crud.delete_financial_event(db, event_id)
