from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models, schemas

router = APIRouter()

# --- Owners ---
@router.post("/owners/", response_model=schemas.Owner)
def create_owner(item: schemas.OwnerCreate, db: Session = Depends(get_db)):
    db_item = models.Owner(**item.model_dump())
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.get("/owners/{item_id}", response_model=schemas.Owner)
def read_owner(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Owner).filter(models.Owner.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Owner not found")
    return db_item

@router.put("/owners/{item_id}", response_model=schemas.Owner)
def update_owner(item_id: int, item: schemas.OwnerUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.Owner).filter(models.Owner.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Owner not found")
    for k, v in item.model_dump(exclude_unset=True).items(): setattr(db_item, k, v)
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.delete("/owners/{item_id}")
def delete_owner(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Owner).filter(models.Owner.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Owner not found")
    db.delete(db_item); db.commit()
    return {"ok": True}

# --- Accounts ---
@router.post("/accounts/", response_model=schemas.Account)
def create_account(item: schemas.AccountCreate, db: Session = Depends(get_db)):
    owner_ids = item.owner_ids
    item_data = item.model_dump(exclude={'owner_ids'})
    db_item = models.Account(**item_data)
    if owner_ids:
        owners = db.query(models.Owner).filter(models.Owner.id.in_(owner_ids)).all()
        db_item.owners = owners
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.get("/accounts/{item_id}", response_model=schemas.Account)
def read_account(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Account).filter(models.Account.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Account not found")
    return db_item

@router.put("/accounts/{item_id}", response_model=schemas.Account)
def update_account(item_id: int, item: schemas.AccountUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.Account).filter(models.Account.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Account not found")
    data = item.model_dump(exclude_unset=True)
    if 'owner_ids' in data:
        o_ids = data.pop('owner_ids')
        if o_ids is not None:
            owners = db.query(models.Owner).filter(models.Owner.id.in_(o_ids)).all()
            db_item.owners = owners
    for k, v in data.items(): setattr(db_item, k, v)
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.delete("/accounts/{item_id}")
def delete_account(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Account).filter(models.Account.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Account not found")
    db.delete(db_item); db.commit()
    return {"ok": True}

# --- Income ---
@router.post("/income_sources/", response_model=schemas.IncomeSource)
def create_income(item: schemas.IncomeSourceCreate, db: Session = Depends(get_db)):
    db_item = models.IncomeSource(**item.model_dump())
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.get("/income_sources/{item_id}", response_model=schemas.IncomeSource)
def read_income(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.IncomeSource).filter(models.IncomeSource.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    return db_item

@router.put("/income_sources/{item_id}", response_model=schemas.IncomeSource)
def update_income(item_id: int, item: schemas.IncomeSourceUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.IncomeSource).filter(models.IncomeSource.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    for k, v in item.model_dump(exclude_unset=True).items(): setattr(db_item, k, v)
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.delete("/income_sources/{item_id}")
def delete_income(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.IncomeSource).filter(models.IncomeSource.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_item); db.commit()
    return {"ok": True}

# --- Costs ---
@router.post("/costs/", response_model=schemas.Cost)
def create_cost(item: schemas.CostCreate, db: Session = Depends(get_db)):
    db_item = models.Cost(**item.model_dump())
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.get("/costs/{item_id}", response_model=schemas.Cost)
def read_cost(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Cost).filter(models.Cost.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    return db_item

@router.put("/costs/{item_id}", response_model=schemas.Cost)
def update_cost(item_id: int, item: schemas.CostUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.Cost).filter(models.Cost.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    for k, v in item.model_dump(exclude_unset=True).items(): setattr(db_item, k, v)
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.delete("/costs/{item_id}")
def delete_cost(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Cost).filter(models.Cost.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_item); db.commit()
    return {"ok": True}

# --- Transfers ---
@router.post("/transfers/", response_model=schemas.Transfer)
def create_transfer(item: schemas.TransferCreate, db: Session = Depends(get_db)):
    db_item = models.Transfer(**item.model_dump())
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.put("/transfers/{item_id}", response_model=schemas.Transfer)
def update_transfer(item_id: int, item: schemas.TransferUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.Transfer).filter(models.Transfer.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    for k, v in item.model_dump(exclude_unset=True).items(): setattr(db_item, k, v)
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.delete("/transfers/{item_id}")
def delete_transfer(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.Transfer).filter(models.Transfer.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_item); db.commit()
    return {"ok": True}

# --- Events ---
@router.post("/financial_events/", response_model=schemas.FinancialEvent)
def create_event(item: schemas.FinancialEventCreate, db: Session = Depends(get_db)):
    db_item = models.FinancialEvent(**item.model_dump())
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.put("/financial_events/{item_id}", response_model=schemas.FinancialEvent)
def update_event(item_id: int, item: schemas.FinancialEventUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.FinancialEvent).filter(models.FinancialEvent.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    for k, v in item.model_dump(exclude_unset=True).items(): setattr(db_item, k, v)
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.delete("/financial_events/{item_id}")
def delete_event(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.FinancialEvent).filter(models.FinancialEvent.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_item); db.commit()
    return {"ok": True}

# --- Rules ---
@router.post("/automation_rules/", response_model=schemas.AutomationRule)
def create_rule(item: schemas.AutomationRuleCreate, db: Session = Depends(get_db)):
    db_item = models.AutomationRule(**item.model_dump())
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.put("/automation_rules/{item_id}", response_model=schemas.AutomationRule)
def update_rule(item_id: int, item: schemas.AutomationRuleUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.AutomationRule).filter(models.AutomationRule.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    for k, v in item.model_dump(exclude_unset=True).items(): setattr(db_item, k, v)
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.delete("/automation_rules/{item_id}")
def delete_rule(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.AutomationRule).filter(models.AutomationRule.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_item); db.commit()
    return {"ok": True}

# --- Tax Limits ---
@router.post("/tax_limits/", response_model=schemas.TaxLimit)
def create_limit(item: schemas.TaxLimit, db: Session = Depends(get_db)):
    db_item = models.TaxLimit(**item.model_dump(exclude={'id'}))
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.put("/tax_limits/{item_id}", response_model=schemas.TaxLimit)
def update_limit(item_id: int, item: schemas.TaxLimit, db: Session = Depends(get_db)):
    db_item = db.query(models.TaxLimit).filter(models.TaxLimit.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    for k, v in item.model_dump(exclude={'id'}, exclude_unset=True).items(): setattr(db_item, k, v)
    db.add(db_item); db.commit(); db.refresh(db_item)
    return db_item

@router.delete("/tax_limits/{item_id}")
def delete_limit(item_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.TaxLimit).filter(models.TaxLimit.id == item_id).first()
    if not db_item: raise HTTPException(status_code=404, detail="Not found")
    db.delete(db_item); db.commit()
    return {"ok": True}
