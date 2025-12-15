from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/transfers",
    tags=["transfers"],
)

@router.post("/", response_model=schemas.Transfer)
def create_transfer(transfer: schemas.TransferCreate, db: Session = Depends(get_db)):
    crud.create_scenario_snapshot(db, transfer.scenario_id, f"Create Transfer: {transfer.name}")
    db_scenario = crud.get_scenario(db, scenario_id=transfer.scenario_id)
    if db_scenario is None:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    db_from_account = crud.get_account(db, account_id=transfer.from_account_id)
    if db_from_account is None:
        raise HTTPException(status_code=404, detail="From account not found")
    
    db_to_account = crud.get_account(db, account_id=transfer.to_account_id)
    if db_to_account is None:
        raise HTTPException(status_code=404, detail="To account not found")

    return crud.create_transfer(db=db, transfer=transfer)

@router.get("/", response_model=list[schemas.Transfer])
def read_transfers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    transfers = crud.get_transfers(db, skip=skip, limit=limit)
    return transfers

@router.get("/{transfer_id}", response_model=schemas.Transfer)
def read_transfer(transfer_id: int, db: Session = Depends(get_db)):
    db_transfer = crud.get_transfer(db, transfer_id=transfer_id)
    if db_transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return db_transfer

@router.put("/{transfer_id}", response_model=schemas.Transfer)
def update_transfer(transfer_id: int, transfer: schemas.TransferUpdate, db: Session = Depends(get_db)):
    db_transfer = crud.get_transfer(db, transfer_id=transfer_id)
    if db_transfer:
        crud.create_scenario_snapshot(db, db_transfer.scenario_id, f"Update Transfer: {db_transfer.name}")

    db_transfer = crud.update_transfer(db, transfer_id=transfer_id, transfer=transfer)
    if db_transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return db_transfer

@router.delete("/{transfer_id}", response_model=schemas.Transfer)
def delete_transfer(transfer_id: int, db: Session = Depends(get_db)):
    db_transfer = crud.get_transfer(db, transfer_id=transfer_id)
    if db_transfer:
        crud.create_scenario_snapshot(db, db_transfer.scenario_id, f"Delete Transfer: {db_transfer.name}")

    db_transfer = crud.delete_transfer(db, transfer_id=transfer_id)
    if db_transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return db_transfer
