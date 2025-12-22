from sqlalchemy.orm import Session
from .. import models, schemas

def get_strategy(db: Session, strategy_id: int):
    return db.query(models.DecumulationStrategy).filter(models.DecumulationStrategy.id == strategy_id).first()

def get_strategies_by_scenario(db: Session, scenario_id: int):
    return db.query(models.DecumulationStrategy).filter(models.DecumulationStrategy.scenario_id == scenario_id).all()

def create_strategy(db: Session, strategy: schemas.DecumulationStrategyBase, scenario_id: int):
    db_obj = models.DecumulationStrategy(
        scenario_id=scenario_id,
        **strategy.model_dump()
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_strategy(db: Session, strategy_id: int, strategy: schemas.DecumulationStrategyBase):
    db_obj = get_strategy(db, strategy_id)
    if not db_obj: return None
    
    data = strategy.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(db_obj, k, v)
        
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_strategy(db: Session, strategy_id: int):
    db_obj = get_strategy(db, strategy_id)
    if not db_obj: return None
    db.delete(db_obj)
    db.commit()
    return db_obj
