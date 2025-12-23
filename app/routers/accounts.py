from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, models, schemas, database

router = APIRouter(prefix="/api/accounts", tags=["accounts"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.Account])
def read_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_accounts(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    return crud.create_account(db=db, account=account)

@router.get("/{account_id}", response_model=schemas.Account)
def read_account(account_id: int, db: Session = Depends(get_db)):
    db_account = crud.get_account(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account

@router.put("/{account_id}", response_model=schemas.Account)
def update_account(account_id: int, account: schemas.AccountUpdate, db: Session = Depends(get_db)):
    db_account = crud.update_account(db, account_id=account_id, account=account)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account

@router.delete("/{account_id}")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    db_account = crud.delete_account(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"status": "success"}
