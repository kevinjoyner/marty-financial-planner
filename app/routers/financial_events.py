from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/financial_events",
    tags=["financial_events"],
)

@router.post("/", response_model=schemas.FinancialEvent)
def create_financial_event(event: schemas.FinancialEventCreate, db: Session = Depends(get_db)):
    crud.create_scenario_snapshot(db, event.scenario_id, f"Create Event: {event.name}")
    db_scenario = crud.get_scenario(db, scenario_id=event.scenario_id)
    if db_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return crud.create_financial_event(db=db, event=event)

@router.get("/{event_id}", response_model=schemas.FinancialEvent)
def read_financial_event(event_id: int, db: Session = Depends(get_db)):
    db_event = crud.get_financial_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Financial event not found")
    return db_event

@router.put("/{event_id}", response_model=schemas.FinancialEvent)
def update_financial_event(
    event_id: int, event: schemas.FinancialEventUpdate, db: Session = Depends(get_db)
):
    db_event = crud.get_financial_event(db, event_id=event_id)
    if db_event:
        crud.create_scenario_snapshot(db, db_event.scenario_id, f"Update Event: {db_event.name}")

    db_event = crud.update_financial_event(db, event_id=event_id, event=event)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Financial event not found")
    return db_event

@router.delete("/{event_id}", response_model=schemas.FinancialEvent)
def delete_financial_event(event_id: int, db: Session = Depends(get_db)):
    db_event = crud.get_financial_event(db, event_id=event_id)
    if db_event:
        crud.create_scenario_snapshot(db, db_event.scenario_id, f"Delete Event: {db_event.name}")

    db_event = crud.delete_financial_event(db, event_id=event_id)
    if db_event is None:
        raise HTTPException(status_code=404, detail="Financial event not found")
    return db_event
