from sqlalchemy.orm import Session
from .. import models, schemas

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
    db_owner = get_owner(db, owner_id)
    if not db_owner:
        return None
    
    # exclude_unset=True ensures we don't overwrite fields with None unless explicitly set to None (but here schema defaults are None)
    # Actually, usually for PUT we want to replace. But exclude_unset is safer for partials.
    update_data = owner.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_owner, key, value)
    
    db.add(db_owner)
    db.commit()
    db.refresh(db_owner)
    return db_owner

def delete_owner(db: Session, owner: models.Owner):
    db.delete(owner)
    db.commit()
