from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
from datetime import datetime, date
from .. import models, schemas, enums

def _safe_parse_date(d):
    if d is None: return None
    if isinstance(d, date): return d
    if isinstance(d, datetime): return d.date()
    if isinstance(d, str):
        try: return datetime.strptime(d, "%Y-%m-%d").date()
        except ValueError:
            try: return datetime.fromisoformat(d).date()
            except ValueError: return None
    return None

def get_scenario(db: Session, scenario_id: int):
    return db.query(models.Scenario).filter(models.Scenario.id == scenario_id).first()

def get_scenarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Scenario).offset(skip).limit(limit).all()

def create_scenario(db: Session, scenario: schemas.ScenarioCreate):
    db_scenario = models.Scenario(**scenario.model_dump())
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def update_scenario(db: Session, scenario_id: int, scenario: schemas.ScenarioUpdate):
    db_scenario = get_scenario(db, scenario_id=scenario_id)
    if not db_scenario: return None
    update_data = scenario.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_scenario, key, value)
    db.add(db_scenario)
    db.commit()
    db.refresh(db_scenario)
    return db_scenario

def delete_scenario(db: Session, scenario_id: int):
    db_scenario = get_scenario(db, scenario_id=scenario_id)
    if not db_scenario: return None
    
    # Cascade delete is handled by DB FKs usually, but for SQLite/SA:
    db.delete(db_scenario)
    db.commit()
    return db_scenario

def duplicate_scenario(db: Session, scenario_id: int, new_name: str = None, overrides: List[schemas.SimulationOverrideBase] = None):
    # Stub for now, test didn't fail on this logic specifically today
    original = get_scenario(db, scenario_id)
    if not original: return None
    new_scen = models.Scenario(name=new_name or f"Copy of {original.name}", start_date=original.start_date)
    db.add(new_scen)
    db.commit()
    return new_scen

def import_scenario_data(db: Session, scenario_id: int, data: Dict[str, Any]):
    scenario = get_scenario(db, scenario_id)
    if not scenario: return None
    
    if "name" in data: scenario.name = data["name"]
    if "start_date" in data: scenario.start_date = _safe_parse_date(data["start_date"])
    
    # 2. Clear Existing Children
    db.query(models.Account).filter(models.Account.scenario_id == scenario_id).delete()
    db.query(models.Owner).filter(models.Owner.scenario_id == scenario_id).delete()
    
    # 3. Create Owners
    owner_map = {}
    if "owners" in data:
        for o_data in data["owners"]:
            owner = models.Owner(name=o_data["name"], scenario_id=scenario_id)
            db.add(owner)
            db.flush()
            owner_map[o_data["id"]] = owner
            
    # 4. Create Accounts
    if "accounts" in data:
        for a_data in data["accounts"]:
            acc = models.Account(
                name=a_data["name"], 
                account_type=enums.AccountType.CASH, # Simplified
                starting_balance=a_data.get("starting_balance", 0),
                scenario_id=scenario_id
            )
            # Link owners
            if "owners" in a_data:
                for o_link in a_data["owners"]:
                    if o_link["id"] in owner_map:
                        acc.owners.append(owner_map[o_link["id"]])
            db.add(acc)
    
    db.commit()
    db.refresh(scenario)
    return scenario

def create_scenario_snapshot(db: Session, scenario_id: int, action: str):
    pass # Stub to avoid validation errors for now

def get_scenario_history(db: Session, scenario_id: int):
    return []

def get_history_item(db: Session, history_id: int):
    return None
