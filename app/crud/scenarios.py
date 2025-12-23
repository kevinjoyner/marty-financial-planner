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
    
    # 1. Nullify self-referential keys in Accounts to prevent locking
    db.query(models.Account).filter(models.Account.scenario_id == scenario_id).update(
        {models.Account.payment_from_account_id: None, models.Account.rsu_target_account_id: None},
        synchronize_session=False
    )
    db.commit() 

    # 2. Delete all dependent children explicitly (Safe for SQLite FKs)
    db.query(models.Transfer).filter(models.Transfer.scenario_id == scenario_id).delete()
    db.query(models.FinancialEvent).filter(models.FinancialEvent.scenario_id == scenario_id).delete()
    db.query(models.Cost).filter(models.Cost.scenario_id == scenario_id).delete()
    db.query(models.AutomationRule).filter(models.AutomationRule.scenario_id == scenario_id).delete()
    db.query(models.TaxLimit).filter(models.TaxLimit.scenario_id == scenario_id).delete()
    db.query(models.ChartAnnotation).filter(models.ChartAnnotation.scenario_id == scenario_id).delete()
    db.query(models.DecumulationStrategy).filter(models.DecumulationStrategy.scenario_id == scenario_id).delete()
    db.query(models.ScenarioHistory).filter(models.ScenarioHistory.scenario_id == scenario_id).delete()
    
    # 3. Delete Income Sources (linked to Owners)
    db.query(models.IncomeSource).filter(models.IncomeSource.owner_id.in_(
        db.query(models.Owner.id).filter(models.Owner.scenario_id == scenario_id)
    )).delete(synchronize_session=False)

    db.commit()

    # 4. Now safe to delete Scenario (cascades to Owners/Accounts)
    db.delete(db_scenario)
    db.commit()
    return db_scenario

def duplicate_scenario(db: Session, scenario_id: int, new_name: str = None, overrides: List[schemas.SimulationOverrideBase] = None):
    original = get_scenario(db, scenario_id)
    if not original: return None

    def get_overridden_val(entity_type, entity_id, field_name, default_val):
        if not overrides: return default_val
        for o in overrides:
            if o.type == entity_type and o.id == entity_id and o.field == field_name:
                return o.value
        return default_val

    final_name = new_name if new_name else f"Copy of {original.name}"

    new_scenario = models.Scenario(
        name=final_name, description=original.description,
        start_date=original.start_date, gbp_to_usd_rate=original.gbp_to_usd_rate, notes=original.notes
    )
    db.add(new_scenario); db.flush()

    for lim in original.tax_limits:
        val = get_overridden_val('tax_limit', lim.id, 'amount', lim.amount)
        db.add(models.TaxLimit(scenario_id=new_scenario.id, name=lim.name, amount=val, wrappers=lim.wrappers, account_types=lim.account_types, start_date=lim.start_date, end_date=lim.end_date, frequency=lim.frequency))
    
    for strat in original.decumulation_strategies:
        db.add(models.DecumulationStrategy(scenario_id=new_scenario.id, name=strat.name, strategy_type=strat.strategy_type, start_date=strat.start_date, end_date=strat.end_date, enabled=strat.enabled))

    owner_map = {} 
    account_map = {}

    for owner in original.owners:
        new_owner = models.Owner(name=owner.name, scenario_id=new_scenario.id, notes=owner.notes, birth_date=owner.birth_date, retirement_age=owner.retirement_age)
        db.add(new_owner); db.flush(); owner_map[owner.id] = new_owner

    for acc in original.accounts:
        data = {c.name: getattr(acc, c.name) for c in acc.__table__.columns if c.name not in ['id', 'scenario_id', 'payment_from_account_id', 'rsu_target_account_id']}
        for field in ['starting_balance', 'interest_rate', 'original_loan_amount', 'fixed_interest_rate', 'min_balance', 'book_cost']:
             if field in data: data[field] = get_overridden_val('account', acc.id, field, data[field])
        new_acc = models.Account(scenario_id=new_scenario.id, **data)
        new_acc.owners = [owner_map[o.id] for o in acc.owners if o.id in owner_map]
        db.add(new_acc); db.flush(); account_map[acc.id] = new_acc

    for old_acc in original.accounts:
        if old_acc.payment_from_account_id and old_acc.payment_from_account_id in account_map:
            account_map[old_acc.id].payment_from_account_id = account_map[old_acc.payment_from_account_id].id
        if old_acc.rsu_target_account_id and old_acc.rsu_target_account_id in account_map:
            account_map[old_acc.id].rsu_target_account_id = account_map[old_acc.rsu_target_account_id].id
        
    for owner in original.owners:
        for inc in owner.income_sources:
            data = {c.name: getattr(inc, c.name) for c in inc.__table__.columns if c.name not in ['id', 'owner_id', 'account_id', 'salary_sacrifice_account_id']}
            for field in ['net_value', 'salary_sacrifice_value', 'employer_pension_contribution', 'taxable_benefit_value']:
                if field in data: data[field] = get_overridden_val('income', inc.id, field, data[field])
            if inc.account_id in account_map:
                new_inc = models.IncomeSource(owner_id=owner_map[owner.id].id, account_id=account_map[inc.account_id].id, **data)
                if inc.salary_sacrifice_account_id and inc.salary_sacrifice_account_id in account_map:
                    new_inc.salary_sacrifice_account_id = account_map[inc.salary_sacrifice_account_id].id
                db.add(new_inc)

    for cost in original.costs:
        data = {c.name: getattr(cost, c.name) for c in cost.__table__.columns if c.name not in ['id', 'scenario_id', 'account_id']}
        if 'value' in data: data['value'] = get_overridden_val('cost', cost.id, 'value', data['value'])
        if cost.account_id in account_map: db.add(models.Cost(scenario_id=new_scenario.id, account_id=account_map[cost.account_id].id, **data))

    for event in original.financial_events:
        data = {c.name: getattr(event, c.name) for c in event.__table__.columns if c.name not in ['id', 'scenario_id', 'from_account_id', 'to_account_id']}
        if 'value' in data: data['value'] = get_overridden_val('event', event.id, 'value', data['value'])
        new_event = models.FinancialEvent(scenario_id=new_scenario.id, **data)
        if event.from_account_id in account_map: new_event.from_account_id = account_map[event.from_account_id].id
        if event.to_account_id in account_map: new_event.to_account_id = account_map[event.to_account_id].id
        db.add(new_event)

    for trans in original.transfers:
        data = {c.name: getattr(trans, c.name) for c in trans.__table__.columns if c.name not in ['id', 'scenario_id', 'from_account_id', 'to_account_id']}
        if 'value' in data: data['value'] = get_overridden_val('transfer', trans.id, 'value', data['value'])
        if trans.from_account_id in account_map and trans.to_account_id in account_map:
            db.add(models.Transfer(scenario_id=new_scenario.id, from_account_id=account_map[trans.from_account_id].id, to_account_id=account_map[trans.to_account_id].id, **data))

    for rule in original.automation_rules:
        r_data = {c.name: getattr(rule, c.name) for c in rule.__table__.columns if c.name not in ['id', 'scenario_id', 'source_account_id', 'target_account_id']}
        for field in ['trigger_value', 'transfer_value', 'transfer_cap']:
             if field in r_data: r_data[field] = get_overridden_val('rule', rule.id, field, r_data[field])
        new_rule = models.AutomationRule(scenario_id=new_scenario.id, **r_data)
        if rule.source_account_id in account_map: new_rule.source_account_id = account_map[rule.source_account_id].id
        if rule.target_account_id in account_map: new_rule.target_account_id = account_map[rule.target_account_id].id
        db.add(new_rule)
    
    for ann in original.chart_annotations:
        db.add(models.ChartAnnotation(scenario_id=new_scenario.id, date=ann.date, label=ann.label, annotation_type=ann.annotation_type))

    db.commit()
    db.refresh(new_scenario)
    return new_scenario

    # RE-FETCH AGAIN to ensure final state is attached
    scenario = get_scenario(db, scenario_id)
    return scenario

from sqlalchemy import Date, DateTime

def _filter_data(model_cls, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns a new dictionary containing only keys that match columns in the model_cls.
    Also automatically converts string values to Python date objects if the target column is a Date type.
    """
    if not data: return {}
    
    result = {}
    valid_cols = {c.name: c for c in model_cls.__table__.columns}
    
    for key, value in data.items():
        if key in valid_cols:
            col = valid_cols[key]
            
            # Auto-convert strings to date objects if the column expects a Date
            if isinstance(value, str):
                # check if column type is Date or DateTime
                # We check isinstance against the class, but col.type is an instance usually
                if isinstance(col.type, (Date, DateTime)):
                    result[key] = _safe_parse_date(value)
                else:
                    result[key] = value
            else:
                result[key] = value
                
    return result

def import_scenario_data(db: Session, scenario_id: int, data: Dict[str, Any]):
    """
    Full-fidelity import of a scenario structure.
    Recursively creates Owners, Accounts, Rules, Costs, etc.
    Dependency Order: Owners -> Accounts -> Links -> [Income, Costs, Rules, etc.]
    """
    # 1. Fetch Scenario (initially)
    scenario = get_scenario(db, scenario_id)
    if not scenario: return None

    try:
        # Update Meta
        if "name" in data: scenario.name = data["name"]
        if "description" in data: scenario.description = data["description"]
        if "start_date" in data: scenario.start_date = _safe_parse_date(data["start_date"])
        if "gbp_to_usd_rate" in data: scenario.gbp_to_usd_rate = data["gbp_to_usd_rate"]
        
        # 2. CLEAR EXISTING CONTENT (Do NOT delete the scenario itself)
        
        # 2a. Nullify self-referential keys in Accounts to prevent locking
        db.query(models.Account).filter(models.Account.scenario_id == scenario_id).update(
            {models.Account.payment_from_account_id: None, models.Account.rsu_target_account_id: None},
            synchronize_session=False
        )
        # Flush here instead of commit to keep it in one transaction if possible, 
        # but the original code had commits. We will try to keep it transactional.
        db.flush() 

        # 2b. Delete simple dependents
        for model in [models.Transfer, models.FinancialEvent, models.Cost, models.AutomationRule, 
                    models.TaxLimit, models.ChartAnnotation, models.DecumulationStrategy]:
            db.query(model).filter(model.scenario_id == scenario_id).delete()
        
        # 2c. Delete Income Sources (linked to Owners)
        db.query(models.IncomeSource).filter(models.IncomeSource.owner_id.in_(
            db.query(models.Owner.id).filter(models.Owner.scenario_id == scenario_id)
        )).delete(synchronize_session=False)

        # 2d. Delete Owners and Accounts
        # Using ORM fetch + delete loop to ensure proper cascading of relationships (like secondary table)
        accounts = db.query(models.Account).filter(models.Account.scenario_id == scenario_id).all()
        for acc in accounts: db.delete(acc)
        
        owners = db.query(models.Owner).filter(models.Owner.scenario_id == scenario_id).all()
        for own in owners: db.delete(own)
        
        db.flush()
        
        # 3. Create Entities & Build Maps
        owner_map = {} # old_id -> new_id
        account_map = {} # old_id -> new_id
        
        # A. Owners (First pass - no income sources yet)
        owners_data = data.get("owners", [])
        deferred_income_sources = [] # (new_owner_id, source_data)

        for owner_d in owners_data:
            old_id = owner_d.get("id")
            od = owner_d.copy()
            # Explicitly remove relation keys not in column list
            for k in ["id", "income_sources", "accounts"]: 
                if k in od: del od[k]
            if "birth_date" in od: od["birth_date"] = _safe_parse_date(od["birth_date"])
            
            # Filter
            filtered_od = _filter_data(models.Owner, od)
            
            db_owner = models.Owner(scenario_id=scenario_id, **filtered_od)
            db.add(db_owner); db.flush()
            if old_id: owner_map[old_id] = db_owner.id
            
            if "income_sources" in owner_d:
                deferred_income_sources.append((db_owner.id, owner_d["income_sources"]))

        # B. Accounts
        accounts_data = data.get("accounts", [])
        deferred_account_links = [] # (db_acc, old_payment_id, old_rsu_id)
        deferred_owner_links = [] # (db_acc, list_of_old_owner_ids)

        for acc_d in accounts_data:
            old_id = acc_d.get("id")
            ad = acc_d.copy()
            
            # Extract special fields
            old_owners = ad.get("owners", []) # list of {name, id} or just ids
            old_payment_id = ad.pop("payment_from_account_id", None)
            old_rsu_id = ad.pop("rsu_target_account_id", None)
            
            for k in ["id", "owners"]: 
                if k in ad: del ad[k]

            # Filter
            filtered_ad = _filter_data(models.Account, ad)

            db_acc = models.Account(scenario_id=scenario_id, **filtered_ad)
            db.add(db_acc); db.flush()
            if old_id: account_map[old_id] = db_acc.id

            if old_payment_id or old_rsu_id:
                deferred_account_links.append((db_acc, old_payment_id, old_rsu_id))
            
            if old_owners:
                o_ids = []
                for item in old_owners:
                    if isinstance(item, dict): o_ids.append(item.get("id"))
                    else: o_ids.append(item)
                deferred_owner_links.append((db_acc, o_ids))

        # C. Link Accounts (Owners & Self-refs)
        for db_acc, o_ids in deferred_owner_links:
            for old_oid in o_ids:
                if old_oid in owner_map:
                    owner = db.get(models.Owner, owner_map[old_oid])
                    if owner: db_acc.owners.append(owner)
        
        for db_acc, pay_id, rsu_id in deferred_account_links:
            if pay_id and pay_id in account_map: db_acc.payment_from_account_id = account_map[pay_id]
            if rsu_id and rsu_id in account_map: db_acc.rsu_target_account_id = account_map[rsu_id]

        # D. Income Sources (Now we have owners and accounts)
        for new_owner_id, sources in deferred_income_sources:
            for src in sources:
                sd = src.copy()
                if "id" in sd: del sd["id"]
                if "owner_id" in sd: del sd["owner_id"] 
                
                old_acc_id = sd.pop("account_id", None)
                old_sac_id = sd.pop("salary_sacrifice_account_id", None)
                
                if "start_date" in sd: sd["start_date"] = _safe_parse_date(sd["start_date"])
                if "end_date" in sd: sd["end_date"] = _safe_parse_date(sd["end_date"])

                # Filter
                filtered_sd = _filter_data(models.IncomeSource, sd)

                db_inc = models.IncomeSource(owner_id=new_owner_id, **filtered_sd)
                if old_acc_id and old_acc_id in account_map: db_inc.account_id = account_map[old_acc_id]
                if old_sac_id and old_sac_id in account_map: db_inc.salary_sacrifice_account_id = account_map[old_sac_id]
                
                db.add(db_inc)

        # E. Costs
        for item in data.get("costs", []):
            d = item.copy()
            old_acc_id = d.pop("account_id", None)
            for k in ["id", "scenario_id"]: 
                if k in d: del d[k]
            
            if "start_date" in d: d["start_date"] = _safe_parse_date(d["start_date"])
            if "end_date" in d: d["end_date"] = _safe_parse_date(d["end_date"])
            
            # Filter
            filtered_d = _filter_data(models.Cost, d)

            obj = models.Cost(scenario_id=scenario_id, **filtered_d)
            if old_acc_id and old_acc_id in account_map: obj.account_id = account_map[old_acc_id]
            db.add(obj)

        # F. Financial Events
        for item in data.get("financial_events", []):
            d = item.copy()
            old_from = d.pop("from_account_id", None)
            old_to = d.pop("to_account_id", None)
            for k in ["id", "scenario_id"]: 
                if k in d: del d[k]
            
            if "event_date" in d: d["event_date"] = _safe_parse_date(d["event_date"])
            
            # Filter
            filtered_d = _filter_data(models.FinancialEvent, d)

            obj = models.FinancialEvent(scenario_id=scenario_id, **filtered_d)
            if old_from and old_from in account_map: obj.from_account_id = account_map[old_from]
            if old_to and old_to in account_map: obj.to_account_id = account_map[old_to]
            db.add(obj)

        # G. Transfers
        for item in data.get("transfers", []):
            d = item.copy()
            old_from = d.pop("from_account_id", None)
            old_to = d.pop("to_account_id", None)
            for k in ["id", "scenario_id"]: 
                if k in d: del d[k]
            
            if "start_date" in d: d["start_date"] = _safe_parse_date(d["start_date"])
            if "end_date" in d: d["end_date"] = _safe_parse_date(d["end_date"])
            
            # Filter
            filtered_d = _filter_data(models.Transfer, d)

            if old_from in account_map and old_to in account_map:
                obj = models.Transfer(scenario_id=scenario_id, **filtered_d)
                obj.from_account_id = account_map[old_from]
                obj.to_account_id = account_map[old_to]
                db.add(obj)

        # H. Automation Rules
        for item in data.get("automation_rules", []):
            d = item.copy()
            old_src = d.pop("source_account_id", None)
            old_tgt = d.pop("target_account_id", None)
            for k in ["id", "scenario_id"]: 
                if k in d: del d[k]
            
            if "start_date" in d: d["start_date"] = _safe_parse_date(d["start_date"])
            if "end_date" in d: d["end_date"] = _safe_parse_date(d["end_date"])
            
            # Filter
            filtered_d = _filter_data(models.AutomationRule, d)

            obj = models.AutomationRule(scenario_id=scenario_id, **filtered_d)
            if old_src and old_src in account_map: obj.source_account_id = account_map[old_src]
            if old_tgt and old_tgt in account_map: obj.target_account_id = account_map[old_tgt]
            db.add(obj)

        # I. Tax Limits
        for item in data.get("tax_limits", []):
            d = item.copy()
            for k in ["id", "scenario_id"]: 
                if k in d: del d[k]
            if "start_date" in d: d["start_date"] = _safe_parse_date(d["start_date"])
            if "end_date" in d: d["end_date"] = _safe_parse_date(d["end_date"])
            
            # Filter
            filtered_d = _filter_data(models.TaxLimit, d)
            
            db.add(models.TaxLimit(scenario_id=scenario_id, **filtered_d))

        # J. Decumulation Strategies
        for item in data.get("decumulation_strategies", []):
            d = item.copy()
            for k in ["id", "scenario_id"]: 
                if k in d: del d[k]
            if "start_date" in d: d["start_date"] = _safe_parse_date(d["start_date"])
            if "end_date" in d: d["end_date"] = _safe_parse_date(d["end_date"])
            
            # Filter
            filtered_d = _filter_data(models.DecumulationStrategy, d)
            
            db.add(models.DecumulationStrategy(scenario_id=scenario_id, **filtered_d))

        # K. Chart Annotations
        for item in data.get("chart_annotations", []):
            d = item.copy()
            for k in ["id", "scenario_id"]: 
                if k in d: del d[k]
            if "date" in d: d["date"] = _safe_parse_date(d["date"])
            
            # Filter
            filtered_d = _filter_data(models.ChartAnnotation, d)
            
            db.add(models.ChartAnnotation(scenario_id=scenario_id, **filtered_d))

        db.commit()
    except Exception as e:
        db.rollback()
        raise e
        
    # RE-FETCH AGAIN to ensure final state is attached
    scenario = get_scenario(db, scenario_id)
    return scenario

def create_scenario_snapshot(db: Session, scenario_id: int, action: str):
    scenario = get_scenario(db, scenario_id)
    if not scenario: return
    scenario_schema = schemas.Scenario.model_validate(scenario)
    snapshot_data = scenario_schema.model_dump(mode='json')
    db.add(models.ScenarioHistory(scenario_id=scenario_id, action_description=action, snapshot_data=snapshot_data, timestamp=date.today()))
    db.commit()

def get_scenario_history(db: Session, scenario_id: int):
    return db.query(models.ScenarioHistory).filter(models.ScenarioHistory.scenario_id == scenario_id).order_by(models.ScenarioHistory.id.desc()).all()

def get_history_item(db: Session, history_id: int):
    return db.query(models.ScenarioHistory).filter(models.ScenarioHistory.id == history_id).first()
