from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas
from ..database import get_db

router = APIRouter(
    prefix="/automation_rules",
    tags=["rules"],
)

@router.post("/", response_model=schemas.AutomationRule)
def create_rule(rule: schemas.AutomationRuleCreate, db: Session = Depends(get_db)):
    return crud.create_rule(db, rule)

@router.get("/{rule_id}", response_model=schemas.AutomationRule)
def read_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = crud.get_rule(db, rule_id)
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return db_rule

@router.put("/reorder")
def reorder_rules(rule_ids: List[int] = Body(...), db: Session = Depends(get_db)):
    crud.reorder_rules(db, rule_ids)
    return {"ok": True}

@router.put("/{rule_id}", response_model=schemas.AutomationRule)
def update_rule(rule_id: int, rule: schemas.AutomationRuleUpdate, db: Session = Depends(get_db)):
    db_rule = crud.update_rule(db, rule_id, rule)
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return db_rule

@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = crud.delete_rule(db, rule_id)
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"ok": True}
