from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/income_sources",
    tags=["income_sources"],
)

@router.post("/", response_model=schemas.IncomeSource)
def create_income_source(income_source: schemas.IncomeSourceCreate, db: Session = Depends(get_db)):
    db_owner = crud.get_owner(db, owner_id=income_source.owner_id)
    if db_owner is None:
        raise HTTPException(status_code=404, detail="Owner not found")
    
    crud.create_scenario_snapshot(db, db_owner.scenario_id, f"Create Income: {income_source.name}")

    db_account = crud.get_account(db, account_id=income_source.account_id)
    if db_account is None:
        raise HTTPException(status_code=404, detail="Account not found")

    # Attempt creation
    db_income = crud.create_income_source(db=db, income_source=income_source)
    if db_income is None:
        # This usually means the Owner is not linked to the Account
        raise HTTPException(status_code=400, detail="Invalid Request: Owner must be linked to the selected Account.")

    return db_income

@router.get("/", response_model=list[schemas.IncomeSource])
def read_income_sources(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    income_sources = crud.get_income_sources(db, skip=skip, limit=limit)
    return income_sources

@router.get("/{income_source_id}", response_model=schemas.IncomeSource)
def read_income_source(income_source_id: int, db: Session = Depends(get_db)):
    db_income_source = crud.get_income_source(db, income_source_id=income_source_id)
    if db_income_source is None:
        raise HTTPException(status_code=404, detail="Income source not found")
    return db_income_source

@router.put("/{income_source_id}", response_model=schemas.IncomeSource)
def update_income_source(
    income_source_id: int, income_source: schemas.IncomeSourceUpdate, db: Session = Depends(get_db)
):
    db_income_source = crud.get_income_source(db, income_source_id=income_source_id)
    if db_income_source:
        owner = crud.get_owner(db, db_income_source.owner_id)
        if owner:
            crud.create_scenario_snapshot(db, owner.scenario_id, f"Update Income: {db_income_source.name}")

    db_income_source = crud.update_income_source(db, income_source_id=income_source_id, income_source=income_source)
    if db_income_source is None:
        raise HTTPException(status_code=404, detail="Income source not found")
    return db_income_source

@router.delete("/{income_source_id}", response_model=schemas.IncomeSource)
def delete_income_source(income_source_id: int, db: Session = Depends(get_db)):
    db_income_source = crud.get_income_source(db, income_source_id=income_source_id)
    if db_income_source:
        owner = crud.get_owner(db, db_income_source.owner_id)
        if owner:
            crud.create_scenario_snapshot(db, owner.scenario_id, f"Delete Income: {db_income_source.name}")

    db_income_source = crud.delete_income_source(db, income_source_id=income_source_id)
    if db_income_source is None:
        raise HTTPException(status_code=404, detail="Income source not found")
    return db_income_source
