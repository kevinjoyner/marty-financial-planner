from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..database import get_db
from ..crud import tax_limits as crud_limits

router = APIRouter(
    prefix="/tax_limits",
    tags=["tax_limits"],
)

@router.post("/{scenario_id}", response_model=schemas.TaxLimit)
def create_tax_limit(scenario_id: int, limit: schemas.TaxLimitBase, db: Session = Depends(get_db)):
    return crud_limits.create_tax_limit(db=db, limit=limit, scenario_id=scenario_id)

@router.put("/{limit_id}", response_model=schemas.TaxLimit)
def update_tax_limit(limit_id: int, limit: schemas.TaxLimitBase, db: Session = Depends(get_db)):
    db_limit = crud_limits.update_tax_limit(db, limit_id=limit_id, limit=limit)
    if db_limit is None:
        raise HTTPException(status_code=404, detail="Tax Limit not found")
    return db_limit

@router.delete("/{limit_id}")
def delete_tax_limit(limit_id: int, db: Session = Depends(get_db)):
    db_limit = crud_limits.delete_tax_limit(db, limit_id=limit_id)
    if db_limit is None:
        raise HTTPException(status_code=404, detail="Tax Limit not found")
    return {"ok": True}
