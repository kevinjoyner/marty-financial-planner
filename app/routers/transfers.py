from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, database

router = APIRouter(prefix="/api/transfers", tags=["transfers"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Transfer])
def read_transfers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_transfers(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.Transfer)
def create_transfer(transfer: schemas.TransferCreate, db: Session = Depends(get_db)):
    return crud.create_transfer(db=db, transfer=transfer)

@router.get("/{transfer_id}", response_model=schemas.Transfer)
def read_transfer(transfer_id: int, db: Session = Depends(get_db)):
    db_transfer = crud.get_transfer(db, transfer_id=transfer_id)
    if db_transfer is None:
        raise HTTPException(status_code=404, detail="Transfer not found")
    return db_transfer

@router.put("/{transfer_id}", response_model=schemas.Transfer)
def update_transfer(transfer_id: int, transfer: schemas.TransferUpdate, db: Session = Depends(get_db)):
    return crud.update_transfer(db, transfer_id, transfer)

@router.delete("/{transfer_id}")
def delete_transfer(transfer_id: int, db: Session = Depends(get_db)):
    return crud.delete_transfer(db, transfer_id)
