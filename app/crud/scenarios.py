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
    
    # MANUAL CLEANUP
    db.query(models.Account).filter(models.Account.scenario_id == scenario_id).update(
        {models.Account.payment_from_account_id: None, models.Account.rsu_target_account_id: None},
        synchronize_session=False
    )
    db.commit() 

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
        name=final_name,
        description=original.description,
        start_date=original.start_date,
        gbp_to_usd_rate=original.gbp_to_usd_rate,
        notes=original.notes
    )
    db.add(new_scenario)
    db.flush()

    # Tax Limits
    for lim in original.tax_limits:
        val = get_overridden_val('tax_limit', lim.id, 'amount', lim.amount)
        db.add(models.TaxLimit(
            scenario_id=new_scenario.id,
            name=lim.name, amount=val, wrappers=lim.wrappers,
            account_types=lim.account_types, start_date=lim.start_date, end_date=lim.end_date, frequency=lim.frequency
        ))
    
    owner_map = {} 
    account_map = {}

    # Owners
    for owner in original.owners:
        new_owner = models.Owner(name=owner.name, scenario_id=new_scenario.id, notes=owner.notes, birth_date=owner.birth_date, retirement_age=owner.retirement_age)
        db.add(new_owner)
        db.flush()
        owner_map[owner.id] = new_owner

    # Accounts
    for acc in original.accounts:
        data = {c.name: getattr(acc, c.name) for c in acc.__table__.columns if c.name not in ['id', 'scenario_id', 'payment_from_account_id', 'rsu_target_account_id']}
        for field in ['starting_balance', 'interest_rate', 'original_loan_amount', 'fixed_interest_rate', 'min_balance', 'book_cost']:
             if field in data:
                 data[field] = get_overridden_val('account', acc.id, field, data[field])

        new_acc = models.Account(scenario_id=new_scenario.id, **data)
        new_acc.owners = [owner_map[o.id] for o in acc.owners if o.id in owner_map]
        db.add(new_acc)
        db.flush()
        account_map[acc.id] = new_acc

    # Relink
    for old_acc in original.accounts:
        if old_acc.payment_from_account_id and old_acc.payment_from_account_id in account_map:
            account_map[old_acc.id].payment_from_account_id = account_map[old_acc.payment_from_account_id].id
        if old_acc.rsu_target_account_id and old_acc.rsu_target_account_id in account_map:
            account_map[old_acc.id].rsu_target_account_id = account_map[old_acc.rsu_target_account_id].id
        
    # Income
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

    # Costs
    for cost in original.costs:
        data = {c.name: getattr(cost, c.name) for c in cost.__table__.columns if c.name not in ['id', 'scenario_id', 'account_id']}
        if 'value' in data: data['value'] = get_overridden_val('cost', cost.id, 'value', data['value'])
        if cost.account_id in account_map:
            db.add(models.Cost(scenario_id=new_scenario.id, account_id=account_map[cost.account_id].id, **data))

    # Events
    for event in original.financial_events:
        data = {c.name: getattr(event, c.name) for c in event.__table__.columns if c.name not in ['id', 'scenario_id', 'from_account_id', 'to_account_id']}
        if 'value' in data: data['value'] = get_overridden_val('event', event.id, 'value', data['value'])
        new_event = models.FinancialEvent(scenario_id=new_scenario.id, **data)
        if event.from_account_id in account_map: new_event.from_account_id = account_map[event.from_account_id].id
        if event.to_account_id in account_map: new_event.to_account_id = account_map[event.to_account_id].id
        db.add(new_event)

    # Transfers
    for trans in original.transfers:
        data = {c.name: getattr(trans, c.name) for c in trans.__table__.columns if c.name not in ['id', 'scenario_id', 'from_account_id', 'to_account_id']}
        if 'value' in data: data['value'] = get_overridden_val('transfer', trans.id, 'value', data['value'])
        if trans.from_account_id in account_map and trans.to_account_id in account_map:
            db.add(models.Transfer(scenario_id=new_scenario.id, from_account_id=account_map[trans.from_account_id].id, to_account_id=account_map[trans.to_account_id].id, **data))

    # Rules
    for rule in original.automation_rules:
        r_data = {c.name: getattr(rule, c.name) for c in rule.__table__.columns if c.name not in ['id', 'scenario_id', 'source_account_id', 'target_account_id']}
        for field in ['trigger_value', 'transfer_value', 'transfer_cap']:
             if field in r_data: r_data[field] = get_overridden_val('rule', rule.id, field, r_data[field])
        new_rule = models.AutomationRule(scenario_id=new_scenario.id, **r_data)
        if rule.source_account_id in account_map: new_rule.source_account_id = account_map[rule.source_account_id].id
        if rule.target_account_id in account_map: new_rule.target_account_id = account_map[rule.target_account_id].id
        db.add(new_rule)
    
    # Decumulation
    for strat in original.decumulation_strategies:
        s_data = {c.name: getattr(strat, c.name) for c in strat.__table__.columns if c.name not in ['id', 'scenario_id']}
        if hasattr(strat, 'enabled'):
             s_data['enabled'] = get_overridden_val('strategy', strat.id, 'enabled', s_data.get('enabled'))
        db.add(models.DecumulationStrategy(scenario_id=new_scenario.id, **s_data))

    # Annotations
    for ann in original.chart_annotations:
        db.add(models.ChartAnnotation(scenario_id=new_scenario.id, date=ann.date, label=ann.label, annotation_type=ann.annotation_type))

    db.commit()
    db.refresh(new_scenario)
    return new_scenario

def import_scenario_data(db: Session, scenario_id: int, data: Dict[str, Any]):
    scenario = get_scenario(db, scenario_id)
    if not scenario: return None
    
    if "name" in data: scenario.name = data["name"]
    if "description" in data: scenario.description = data.get("description")
    if "start_date" in data: scenario.start_date = _safe_parse_date(data["start_date"])
    if "gbp_to_usd_rate" in data: scenario.gbp_to_usd_rate = data.get("gbp_to_usd_rate", 1.25)
    db.add(scenario)
    db.commit()

    # Use String Keys for mapping to be safe against JSON type parsing
    owner_map = {}
    for owner_data in data.get("owners", []):
        db_owner = models.Owner(
            scenario_id=scenario.id, 
            name=owner_data["name"], 
            birth_date=_safe_parse_date(owner_data.get("birth_date")), 
            retirement_age=owner_data.get("retirement_age")
        )
        db.add(db_owner); db.commit(); db.refresh(db_owner)
        owner_map[str(owner_data.get("id"))] = db_owner.id

    account_map = {}
    for acc in data.get("accounts", []):
        db_acc = models.Account(
            scenario_id=scenario.id,
            name=acc["name"],
            account_type=acc["account_type"],
            tax_wrapper=acc.get("tax_wrapper", "None"),
            starting_balance=acc["starting_balance"],
            interest_rate=acc.get("interest_rate", 0),
            currency=acc.get("currency", "GBP"),
            min_balance=acc.get("min_balance", 0),
            book_cost=acc.get("book_cost"),
            original_loan_amount=acc.get("original_loan_amount"),
            mortgage_start_date=_safe_parse_date(acc.get("mortgage_start_date")),
            amortisation_period_years=acc.get("amortisation_period_years"),
            fixed_interest_rate=acc.get("fixed_interest_rate"),
            fixed_rate_period_years=acc.get("fixed_rate_period_years"),
            grant_date=_safe_parse_date(acc.get("grant_date")),
            vesting_schedule=acc.get("vesting_schedule"),
            unit_price=acc.get("unit_price")
        )
        if db_acc.book_cost is None: db_acc.book_cost = db_acc.starting_balance

        if "owners" in acc:
            owners_list = []
            for o in acc["owners"]:
                # Match by Name if ID linking is ambiguous in JSON
                # But here we rely on name matching as a fallback or existing logic?
                # Actually, in the demo JSON, owners inside accounts only have 'name', not 'id'.
                # So we must lookup by Name if ID is missing.
                found = None
                if o.get("id") and str(o["id"]) in owner_map:
                    found = db.get(models.Owner, owner_map[str(o["id"])])
                elif o.get("name"):
                    # Fallback: Find owner by name in the CURRENT import set
                    # We can't query DB easily, but we can look at the owner_map values
                    # This is inefficient but safe for small sets.
                    for oid in owner_map.values():
                        candidate = db.get(models.Owner, oid)
                        if candidate.name == o["name"]:
                            found = candidate
                            break
                if found: owners_list.append(found)
            db_acc.owners = owners_list
            
        db.add(db_acc); db.commit(); db.refresh(db_acc)
        account_map[str(acc.get("id"))] = db_acc.id

    for owner_data in data.get("owners", []):
        new_owner_id = owner_map.get(str(owner_data.get("id")))
        for inc in owner_data.get("income_sources", []):
            mapped_acc_id = account_map.get(str(inc.get("account_id")))
            mapped_sac_id = account_map.get(str(inc.get("salary_sacrifice_account_id")))
            db_inc = models.IncomeSource(
                owner_id=new_owner_id,
                account_id=mapped_acc_id,
                salary_sacrifice_account_id=mapped_sac_id,
                name=inc["name"],
                net_value=inc.get("net_value", 0),
                cadence=inc["cadence"],
                start_date=_safe_parse_date(inc["start_date"]),
                end_date=_safe_parse_date(inc.get("end_date")),
                currency=inc.get("currency", "GBP"),
                is_pre_tax=inc.get("is_pre_tax", False),
                salary_sacrifice_value=inc.get("salary_sacrifice_value", 0),
                taxable_benefit_value=inc.get("taxable_benefit_value", 0),
                employer_pension_contribution=inc.get("employer_pension_contribution", 0)
            )
            db.add(db_inc)

    if "tax_limits" in data:
        for t in data["tax_limits"]:
            db.add(models.TaxLimit(
                scenario_id=scenario.id,
                name=t["name"],
                amount=t["amount"],
                wrappers=t["wrappers"],
                frequency=t.get("frequency", "Annually"),
                start_date=_safe_parse_date(t.get("start_date", scenario.start_date)),
                end_date=_safe_parse_date(t.get("end_date")),
                account_types=t.get("account_types")
            ))

    if "costs" in data:
        for c in data["costs"]:
            acc = account_map.get(str(c.get("account_id")))
            if acc:
                db.add(models.Cost(scenario_id=scenario.id, account_id=acc, name=c["name"], value=c["value"], cadence=c["cadence"], start_date=_safe_parse_date(c["start_date"]), end_date=_safe_parse_date(c.get("end_date")), is_recurring=c.get("is_recurring", True)))

    if "automation_rules" in data:
        for r in data["automation_rules"]:
            src_id = account_map.get(str(r.get("source_account_id")))
            tgt_id = account_map.get(str(r.get("target_account_id")))
            if src_id:
                db.add(models.AutomationRule(scenario_id=scenario.id, name=r["name"], rule_type=r["rule_type"], source_account_id=src_id, target_account_id=tgt_id, trigger_value=r["trigger_value"], transfer_value=r.get("transfer_value"), cadence=r["cadence"], start_date=_safe_parse_date(r.get("start_date")), end_date=_safe_parse_date(r.get("end_date")), priority=r.get("priority", 0)))

    if "financial_events" in data:
        for e in data["financial_events"]:
            from_acc = account_map.get(str(e.get("from_account_id")))
            to_acc = account_map.get(str(e.get("to_account_id")))
            db.add(models.FinancialEvent(scenario_id=scenario.id, from_account_id=from_acc, to_account_id=to_acc, name=e["name"], value=e["value"], event_date=_safe_parse_date(e["event_date"]), event_type=e["event_type"], show_on_chart=e.get("show_on_chart", False)))

    if "transfers" in data:
        for t in data["transfers"]:
            from_acc = account_map.get(str(t.get("from_account_id")))
            to_acc = account_map.get(str(t.get("to_account_id")))
            if from_acc and to_acc:
                db.add(models.Transfer(scenario_id=scenario.id, from_account_id=from_acc, to_account_id=to_acc, name=t["name"], value=t["value"], cadence=t["cadence"], start_date=_safe_parse_date(t["start_date"]), end_date=_safe_parse_date(t.get("end_date")), show_on_chart=t.get("show_on_chart", False)))

    if "decumulation_strategies" in data:
        for s in data["decumulation_strategies"]:
            db.add(models.DecumulationStrategy(
                scenario_id=scenario.id,
                name=s["name"],
                strategy_type=s.get("strategy_type", "Standard"),
                start_date=_safe_parse_date(s.get("start_date")),
                end_date=_safe_parse_date(s.get("end_date")),
                enabled=s.get("enabled", True)
            ))

    if "chart_annotations" in data:
        for ann in data["chart_annotations"]:
            db.add(models.ChartAnnotation(scenario_id=scenario.id, date=_safe_parse_date(ann["date"]), label=ann["label"], annotation_type=ann.get("annotation_type", "manual")))

    db.commit()
    
    # Linking Accounts (Payment From / RSU Target)
    for acc_data in data.get("accounts", []):
        db_id = account_map.get(str(acc_data["id"]))
        pay_from = account_map.get(str(acc_data.get("payment_from_account_id")))
        rsu_target = account_map.get(str(acc_data.get("rsu_target_account_id")))
        if db_id and (pay_from or rsu_target):
            acc = db.get(models.Account, db_id)
            if pay_from: acc.payment_from_account_id = pay_from
            if rsu_target: acc.rsu_target_account_id = rsu_target
            db.add(acc)
    db.commit()
    db.refresh(scenario)
    return scenario

def create_scenario_snapshot(db: Session, scenario_id: int, action: str):
    scenario = get_scenario(db, scenario_id)
    if not scenario: return
    scenario_schema = schemas.Scenario.model_validate(scenario)
    snapshot_data = scenario_schema.model_dump(mode='json')
    db.add(models.ScenarioHistory(
        scenario_id=scenario_id,
        action_description=action,
        snapshot_data=snapshot_data,
        timestamp=date.today()
    ))
    db.commit()

def get_scenario_history(db: Session, scenario_id: int):
    return db.query(models.ScenarioHistory).filter(models.ScenarioHistory.scenario_id == scenario_id).order_by(models.ScenarioHistory.id.desc()).all()

def get_history_item(db: Session, history_id: int):
    return db.query(models.ScenarioHistory).filter(models.ScenarioHistory.id == history_id).first()
