from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from .. import crud, schemas, database

router = APIRouter(prefix="/api/automation_rules", tags=["automation_rules"])

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/", response_model=List[schemas.AutomationRule])
def read_rules(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_rules(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.AutomationRule)
def create_rule(rule: schemas.AutomationRuleCreate, db: Session = Depends(get_db)):
    return crud.create_rule(db, rule)

@router.put("/reorder")
def reorder_rules(rule_ids: List[int], db: Session = Depends(get_db)):
    # Call directly from crud.rules to ensure function is found
    crud.rules.reorder_rules(db, rule_ids)
    return {"status": "ok"}

@router.get("/{rule_id}", response_model=schemas.AutomationRule)
def read_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = crud.get_rule(db, rule_id=rule_id)
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return db_rule

@router.put("/{rule_id}", response_model=schemas.AutomationRule)
def update_rule(rule_id: int, rule: schemas.AutomationRuleUpdate, db: Session = Depends(get_db)):
    db_rule = crud.update_rule(db, rule_id=rule_id, rule=rule)
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return db_rule

@router.delete("/{rule_id}")
def delete_rule(rule_id: int, db: Session = Depends(get_db)):
    db_rule = crud.delete_rule(db, rule_id=rule_id)
    if db_rule is None:
        raise HTTPException(status_code=404, detail="Rule not found")
    return {"status": "success"}
