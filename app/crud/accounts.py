from sqlalchemy.orm import Session, selectinload
from .. import models, schemas
from .base import _parse_date

def get_owner(db: Session, owner_id: int):
    return db.query(models.Owner).filter(models.Owner.id == owner_id).first()

def get_owners(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Owner).offset(skip).limit(limit).all()

def create_owner(db: Session, owner: schemas.OwnerCreate):
    db_owner = models.Owner(**owner.model_dump())
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner

def update_owner(db: Session, owner_id: int, owner: schemas.OwnerUpdate):
    db_owner = get_owner(db, owner_id=owner_id)
    if not db_owner: return None
    update_data = owner.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_owner, key, value)
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner

def delete_owner(db: Session, owner_id: int):
    db_owner = get_owner(db, owner_id=owner_id)
    if not db_owner: return None
    db.delete(db_owner)
    db.commit()
    return db_owner

def get_account(db: Session, account_id: int):
    return (
        db.query(models.Account)
        .options(selectinload(models.Account.owners))
        .filter(models.Account.id == account_id)
        .first()
    )

def get_accounts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Account).offset(skip).limit(limit).all()

def create_account(db: Session, account: schemas.AccountCreate):
    if not account.owner_ids: return None
    owners = db.query(models.Owner).filter(models.Owner.id.in_(account.owner_ids)).all()
    if len(owners) != len(account.owner_ids): return None

    account_data = account.model_dump(exclude={"owner_ids"})
    account_data["account_type"] = account_data["account_type"].value
    
    # DEFAULT BOOK COST LOGIC
    # If not provided, assume the starting balance is the cost basis (cash injection)
    if account_data.get('book_cost') is None:
        account_data['book_cost'] = account_data.get('starting_balance', 0)
    
    if account_data.get('mortgage_start_date'): account_data['mortgage_start_date'] = _parse_date(account_data['mortgage_start_date'])
    if account_data.get('grant_date'): account_data['grant_date'] = _parse_date(account_data['grant_date'])

    db_account = models.Account(**account_data)
    db_account.owners = owners
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def update_account(db: Session, account_id: int, account: schemas.AccountUpdate):
    db_account = get_account(db, account_id=account_id)
    if not db_account: return None
    update_data = account.model_dump(exclude_unset=True)
    
    if "owner_ids" in update_data:
        owner_ids = update_data.pop("owner_ids")
        if owner_ids is not None:
            owners = db.query(models.Owner).filter(models.Owner.id.in_(owner_ids)).all()
            if len(owners) == len(owner_ids): db_account.owners = owners

    if 'mortgage_start_date' in update_data: update_data['mortgage_start_date'] = _parse_date(update_data['mortgage_start_date'])
    if 'grant_date' in update_data: update_data['grant_date'] = _parse_date(update_data['grant_date'])

    for key, value in update_data.items():
        setattr(db_account, key, value)
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

def delete_account(db: Session, account_id: int):
    db_account = get_account(db, account_id=account_id)
    if not db_account: return None
    db.delete(db_account)
    db.commit()
    return db_account
