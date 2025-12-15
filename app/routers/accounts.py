from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/accounts",
    tags=["accounts"],
)

@router.post("/", response_model=schemas.Account)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    crud.create_scenario_snapshot(db, account.scenario_id, f"Create Account: {account.name}")
    db_account = crud.create_account(db=db, account=account)
    if db_account is None:
        raise HTTPException(status_code=400, detail="Invalid owner_ids or scenario_id")
    return db_account

@router.get("/", response_model=list[schemas.Account])
def read_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    accounts = crud.get_accounts(db, skip=skip, limit=limit)
    return accounts

@router.get("/{account_id}", response_model=schemas.Account)
def read_account(account_id: int, db: Session = Depends(get_db)):
    db_account = crud.get_account(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account

@router.put("/{account_id}", response_model=schemas.Account)
def update_account(
    account_id: int, account: schemas.AccountUpdate, db: Session = Depends(get_db)
):
    db_account = crud.get_account(db, account_id=account_id)
    if db_account:
        crud.create_scenario_snapshot(db, db_account.scenario_id, f"Update Account: {db_account.name}")

    db_account = crud.update_account(db, account_id=account_id, account=account)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found or update data invalid")
    return db_account

@router.delete("/{account_id}", response_model=schemas.Account)
def delete_account(account_id: int, db: Session = Depends(get_db)):
    db_account = crud.get_account(db, account_id=account_id)
    if db_account:
        crud.create_scenario_snapshot(db, db_account.scenario_id, f"Delete Account: {db_account.name}")

    db_account = crud.delete_account(db, account_id=account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")
    return db_account
