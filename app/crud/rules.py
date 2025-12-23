from sqlalchemy.orm import Session
from .. import models, schemas

def get_rule(db: Session, rule_id: int):
    return db.query(models.AutomationRule).filter(models.AutomationRule.id == rule_id).first()

def get_rules(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AutomationRule).offset(skip).limit(limit).all()

def create_rule(db: Session, rule: schemas.AutomationRuleCreate):
    from .scenarios import create_scenario_snapshot
    create_scenario_snapshot(db, rule.scenario_id, f"Created Rule: {rule.name}")
    db_rule = models.AutomationRule(**rule.model_dump())
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def update_rule(db: Session, rule_id: int, rule: schemas.AutomationRuleUpdate):
    from .scenarios import create_scenario_snapshot
    db_rule = get_rule(db, rule_id)
    if not db_rule: return None
    create_scenario_snapshot(db, db_rule.scenario_id, f"Updated Rule: {db_rule.name}")
    update_data = rule.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_rule, key, value)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def delete_rule(db: Session, rule_id: int):
    from .scenarios import create_scenario_snapshot
    db_rule = get_rule(db, rule_id)
    if not db_rule: return None
    create_scenario_snapshot(db, db_rule.scenario_id, f"Deleted Rule: {db_rule.name}")
    db.delete(db_rule)
    db.commit()
    return db_rule

def reorder_rules(db: Session, rule_ids: list[int]):
    for index, rule_id in enumerate(rule_ids):
        db.query(models.AutomationRule).filter(models.AutomationRule.id == rule_id).update({"priority": index})
    db.commit()
