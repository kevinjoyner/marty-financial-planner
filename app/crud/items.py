from sqlalchemy.orm import Session, selectinload
from .. import models, schemas
from .base import _parse_date

# --- COSTS ---
def get_cost(db: Session, cost_id: int):
    return db.query(models.Cost).filter(models.Cost.id == cost_id).first()

def get_costs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Cost).offset(skip).limit(limit).all()

def create_cost(db: Session, cost: schemas.CostCreate):
    account = db.query(models.Account).filter(
        models.Account.id == cost.account_id,
        models.Account.scenario_id == cost.scenario_id
    ).first()
    if not account: return None

    cost_data = cost.model_dump()
    cost_data["cadence"] = cost_data["cadence"].value
    db_cost = models.Cost(**cost_data)
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

def update_cost(db: Session, cost_id: int, cost: schemas.CostUpdate):
    db_cost = get_cost(db, cost_id=cost_id)
    if not db_cost: return None
    update_data = cost.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_cost, key, value)
    db.add(db_cost)
    db.commit()
    db.refresh(db_cost)
    return db_cost

def delete_cost(db: Session, cost_id: int):
    db_cost = get_cost(db, cost_id=cost_id)
    if not db_cost: return None
    db.delete(db_cost)
    db.commit()
    return db_cost

# --- INCOME ---
def get_income_source(db: Session, income_source_id: int):
    return db.query(models.IncomeSource).filter(models.IncomeSource.id == income_source_id).first()

def get_income_sources(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.IncomeSource).offset(skip).limit(limit).all()

def create_income_source(db: Session, income_source: schemas.IncomeSourceCreate):
    account = db.query(models.Account).options(selectinload(models.Account.owners)).filter(
        models.Account.id == income_source.account_id
    ).first()
    if not account: return None
    
    owner_ids = {owner.id for owner in account.owners}
    if income_source.owner_id not in owner_ids: return None

    income_data = income_source.model_dump()
    income_data["cadence"] = income_data["cadence"].value
    db_income_source = models.IncomeSource(**income_data)
    db.add(db_income_source)
    db.commit()
    db.refresh(db_income_source)
    return db_income_source

def update_income_source(db: Session, income_source_id: int, income_source: schemas.IncomeSourceUpdate):
    db_income_source = get_income_source(db, income_source_id=income_source_id)
    if not db_income_source: return None
    update_data = income_source.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_income_source, key, value)
    db.add(db_income_source)
    db.commit()
    db.refresh(db_income_source)
    return db_income_source

def delete_income_source(db: Session, income_source_id: int):
    db_income = get_income_source(db, income_source_id=income_source_id)
    if not db_income: return None
    db.delete(db_income)
    db.commit()
    return db_income

# --- EVENTS ---
def get_financial_event(db: Session, event_id: int):
    return db.query(models.FinancialEvent).filter(models.FinancialEvent.id == event_id).first()

def get_financial_events(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.FinancialEvent).offset(skip).limit(limit).all()

def create_financial_event(db: Session, event: schemas.FinancialEventCreate):
    if event.event_type.value == 'transfer':
        if not event.from_account_id or not event.to_account_id: return None
    elif not event.from_account_id: return None
            
    db_event = models.FinancialEvent(**event.model_dump())
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def update_financial_event(db: Session, event_id: int, event: schemas.FinancialEventUpdate):
    db_event = get_financial_event(db, event_id=event_id)
    if not db_event: return None
    update_data = event.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_event, key, value)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return db_event

def delete_financial_event(db: Session, event_id: int):
    db_event = get_financial_event(db, event_id=event_id)
    if not db_event: return None
    db.delete(db_event)
    db.commit()
    return db_event

# --- TRANSFERS ---
def get_transfer(db: Session, transfer_id: int):
    return db.query(models.Transfer).filter(models.Transfer.id == transfer_id).first()

def get_transfers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Transfer).offset(skip).limit(limit).all()

def create_transfer(db: Session, transfer: schemas.TransferCreate):
    from_account = db.query(models.Account).filter(models.Account.id == transfer.from_account_id).first()
    to_account = db.query(models.Account).filter(models.Account.id == transfer.to_account_id).first()
    if not from_account or not to_account: return None

    transfer_data = transfer.model_dump()
    transfer_data["cadence"] = transfer_data["cadence"].value
    db_transfer = models.Transfer(**transfer_data)
    db.add(db_transfer)
    db.commit()
    db.refresh(db_transfer)
    return db_transfer

def update_transfer(db: Session, transfer_id: int, transfer: schemas.TransferUpdate):
    db_transfer = get_transfer(db, transfer_id=transfer_id)
    if not db_transfer: return None
    update_data = transfer.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_transfer, key, value)
    db.add(db_transfer)
    db.commit()
    db.refresh(db_transfer)
    return db_transfer

def delete_transfer(db: Session, transfer_id: int):
    db_transfer = get_transfer(db, transfer_id=transfer_id)
    if not db_transfer: return None
    db.delete(db_transfer)
    db.commit()
    return db_transfer
