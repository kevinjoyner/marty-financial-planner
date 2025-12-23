from sqlalchemy.orm import Session
from .. import models, schemas

# --- INCOME SOURCES ---
def get_income_sources(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.IncomeSource).offset(skip).limit(limit).all()

def create_income_source(db: Session, income_source: schemas.IncomeSourceCreate):
    db_income_source = models.IncomeSource(**income_source.model_dump())
    db.add(db_income_source)
    db.commit()
    db.refresh(db_income_source)
    return db_income_source

def update_income_source(db: Session, income_source_id: int, income_source: schemas.IncomeSourceCreate):
    db_inc = db.query(models.IncomeSource).filter(models.IncomeSource.id == income_source_id).first()
    if not db_inc: return None
    update_data = income_source.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inc, key, value)
    db.add(db_inc)
    db.commit()
    db.refresh(db_inc)
    return db_inc

def delete_income_source(db: Session, income_source_id: int):
    db_inc = db.query(models.IncomeSource).filter(models.IncomeSource.id == income_source_id).first()
    if not db_inc: return None
    db.delete(db_inc)
    db.commit()
    return db_inc

# --- COSTS ---
def get_costs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cost).offset(skip).limit(limit).all()

def create_cost(db: Session, cost: schemas.CostCreate):
    db_cost = models.Cost(**cost.model_dump())
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

def update_cost(db: Session, cost_id: int, cost: schemas.CostCreate):
    db_cost = db.query(models.Cost).filter(models.Cost.id == cost_id).first()
    if not db_cost: return None
    update_data = cost.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cost, key, value)
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

def delete_cost(db: Session, cost_id: int):
    db_cost = db.query(models.Cost).filter(models.Cost.id == cost_id).first()
    if not db_cost: return None
    db.delete(db_cost)
    db.commit()
    return db_cost

# --- TRANSFERS ---
def get_transfers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Transfer).offset(skip).limit(limit).all()

def create_transfer(db: Session, transfer: schemas.TransferCreate):
    db_transfer = models.Transfer(**transfer.model_dump())
    db.add(db_transfer)
    db.commit()
    db.refresh(db_transfer)
    return db_transfer

def update_transfer(db: Session, transfer_id: int, transfer: schemas.TransferCreate):
    db_trans = db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()
    if not db_trans: return None
    update_data = transfer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_trans, key, value)
    db.add(db_trans)
    db.commit()
    db.refresh(db_trans)
    return db_trans

def delete_transfer(db: Session, transfer_id: int):
    db_trans = db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()
    if not db_trans: return None
    db.delete(db_trans)
    db.commit()
    return db_trans

# --- FINANCIAL EVENTS ---
def get_financial_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FinancialEvent).offset(skip).limit(limit).all()

def create_financial_event(db: Session, event: schemas.FinancialEventCreate):
    db_event = models.FinancialEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def update_financial_event(db: Session, event_id: int, event: schemas.FinancialEventCreate):
    db_event = db.query(models.FinancialEvent).filter(models.FinancialEvent.id == event_id).first()
    if not db_event: return None
    update_data = event.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def delete_financial_event(db: Session, event_id: int):
    db_event = db.query(models.FinancialEvent).filter(models.FinancialEvent.id == event_id).first()
    if not db_event: return None
    db.delete(db_event)
    db.commit()
    return db_event
