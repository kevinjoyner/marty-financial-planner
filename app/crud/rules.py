from sqlalchemy.orm import Session
from .. import models, schemas
from .scenarios import create_scenario_snapshot

def get_rule(db: Session, rule_id: int):
    return db.query(models.AutomationRule).filter(models.AutomationRule.id == rule_id).first()

def create_rule(db: Session, rule: schemas.AutomationRuleCreate):
    create_scenario_snapshot(db, rule.scenario_id, f"Create Rule: {rule.rule_type.value}")
    db_rule = models.AutomationRule(**rule.model_dump())
    # Enums
    db_rule.rule_type = rule.rule_type.value
    db_rule.cadence = rule.cadence.value
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def update_rule(db: Session, rule_id: int, rule: schemas.AutomationRuleUpdate):
    db_rule = get_rule(db, rule_id)
    if not db_rule: return None
    # db_rule.rule_type is stored as a string in the DB, so we use it directly
    create_scenario_snapshot(db, db_rule.scenario_id, f"Update Rule: {db_rule.rule_type}")
    update_data = rule.model_dump(exclude_unset=True)
    if 'rule_type' in update_data and update_data['rule_type']: update_data['rule_type'] = update_data['rule_type'].value
    if 'cadence' in update_data and update_data['cadence']: update_data['cadence'] = update_data['cadence'].value
    for key, value in update_data.items(): setattr(db_rule, key, value)
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    return db_rule

def delete_rule(db: Session, rule_id: int):
    db_rule = get_rule(db, rule_id)
    if not db_rule: return None
    # db_rule.rule_type is stored as a string in the DB, so we use it directly
    create_scenario_snapshot(db, db_rule.scenario_id, f"Delete Rule: {db_rule.rule_type}")
    db.delete(db_rule)
    db.commit()
    return db_rule

def reorder_rules(db: Session, rule_ids: list[int]):
    """Updates priority of rules based on the index in the provided list."""
    # We assume all rules belong to the same scenario for simplicity in this context,
    # or we just update them regardless. 
    # Ideally we snapshot the scenario of the first rule.
    if not rule_ids: return
    
    first_rule = get_rule(db, rule_ids[0])
    if first_rule:
        create_scenario_snapshot(db, first_rule.scenario_id, "Reorder Automation Rules")

    for index, rule_id in enumerate(rule_ids):
        db.query(models.AutomationRule).filter(models.AutomationRule.id == rule_id).update({"priority": index + 1})
    
    db.commit()
    return True
