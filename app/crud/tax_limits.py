from sqlalchemy.orm import Session
from .. import models, schemas

def create_tax_limit(db: Session, limit: schemas.TaxLimitBase, scenario_id: int):
    db_limit = models.TaxLimit(**limit.model_dump(), scenario_id=scenario_id)
    db.add(db_limit)
    db.commit()
    db.refresh(db_limit)
    return db_limit

def update_tax_limit(db: Session, limit_id: int, limit: schemas.TaxLimitBase):
    db_limit = db.query(models.TaxLimit).filter(models.TaxLimit.id == limit_id).first()
    if not db_limit: return None
    
    update_data = limit.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_limit, key, value)
        
    db.add(db_limit)
    db.commit()
    db.refresh(db_limit)
    return db_limit

def delete_tax_limit(db: Session, limit_id: int):
    db_limit = db.query(models.TaxLimit).filter(models.TaxLimit.id == limit_id).first()
    if not db_limit: return None
    db.delete(db_limit)
    db.commit()
    return db_limit
