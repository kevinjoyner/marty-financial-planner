from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import models, schemas

router = APIRouter()

@router.post("/decumulation_strategies/", response_model=schemas.DecumulationStrategy)
def create_strategy(strategy: schemas.DecumulationStrategyCreate, db: Session = Depends(get_db)):
    db_item = models.DecumulationStrategy(**strategy.model_dump())
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.put("/decumulation_strategies/{strategy_id}", response_model=schemas.DecumulationStrategy)
def update_strategy(strategy_id: int, strategy: schemas.DecumulationStrategyUpdate, db: Session = Depends(get_db)):
    db_item = db.query(models.DecumulationStrategy).filter(models.DecumulationStrategy.id == strategy_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    update_data = strategy.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_item, key, value)
    
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    return db_item

@router.delete("/decumulation_strategies/{strategy_id}")
def delete_strategy(strategy_id: int, db: Session = Depends(get_db)):
    db_item = db.query(models.DecumulationStrategy).filter(models.DecumulationStrategy.id == strategy_id).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Strategy not found")
    
    db.delete(db_item)
    db.commit()
    return {"ok": True}
