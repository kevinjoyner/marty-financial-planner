from datetime import date
from dateutil.relativedelta import relativedelta
from sqlalchemy.orm import Session
from typing import List, Optional

from app import models, schemas, utils, enums
from app.engine.context import ProjectionContext
from app.engine.reporting import calculate_gbp_balances
from app.engine.analyzers import detect_milestones

# Processors
from app.engine.processors.income import process_income
from app.engine.processors.costs import process_costs
from app.engine.processors.transfers import process_transfers
from app.engine.processors.events import process_events
from app.engine.processors.rsu import process_rsu_vesting
from app.engine.processors.rules import process_rules
from app.engine.processors.mortgage import process_standard_mortgage_payments
from app.engine.processors.assets import process_interest
from app.engine.processors.decumulation import process_decumulation

def apply_simulation_overrides(scenario: models.Scenario, overrides: List[schemas.SimulationOverride]):
    if not overrides: return
    
    # Pre-fetch maps for performance
    strategy_map = {s.id: s for s in scenario.decumulation_strategies}
    account_map = {a.id: a for a in scenario.accounts}
    
    for o in overrides:
        try:
            val = o.value
            # Explicit boolean conversion for string payloads
            if isinstance(val, str) and val.lower() in ('true', 'false'):
                val = val.lower() == 'true'

            if o.type == 'decumulation_strategy':
                if o.id in strategy_map:
                    strat = strategy_map[o.id]
                    if hasattr(strat, o.field):
                        setattr(strat, o.field, val)
            elif o.type == 'account':
                if o.id in account_map:
                    acc = account_map[o.id]
                    if hasattr(acc, o.field):
                        setattr(acc, o.field, val)
            elif o.type == 'income' or o.type == 'income_source':
                # Linear search for income sources
                found = False
                for owner in scenario.owners:
                    for inc in owner.income_sources:
                        if inc.id == o.id:
                            if hasattr(inc, o.field):
                                setattr(inc, o.field, val)
                            found = True
                            break
                    if found: break
        except Exception as e:
            print(f"Override Application Error: {e}")

def run_projection(db: Session, scenario: models.Scenario, months: int, overrides: List[schemas.SimulationOverride] = None) -> schemas.Projection:
    # 1. Apply Overrides (In-Memory Modification)
    if overrides:
        apply_simulation_overrides(scenario, overrides)

    all_accounts = scenario.accounts
    
    start_date: date = scenario.start_date
    initial_balances = {acc.id: acc.starting_balance for acc in all_accounts}
    initial_costs = {acc.id: (acc.book_cost if acc.book_cost is not None else acc.starting_balance) for acc in all_accounts}
    
    context = ProjectionContext(month_start=start_date, account_balances=initial_balances, account_book_costs=initial_costs, flows={}, all_accounts=all_accounts)
    
    # Load annotations
    for ann in scenario.chart_annotations:
        context.annotations.append(schemas.ProjectionAnnotation(date=ann.date, label=ann.label, type=ann.annotation_type))

    initial_breakdown, initial_total = calculate_gbp_balances(context.account_balances, all_accounts, scenario.gbp_to_usd_rate, start_date)
    
    data_points = []
    data_points.append(schemas.ProjectionDataPoint(date=start_date, balance=initial_total, account_balances=initial_breakdown, flows={}))
    
    projection_anchor = start_date.replace(day=1)
    current_fy = utils.get_uk_fiscal_year(start_date)
    
    for i in range(months):
        context.prev_balances = context.account_balances.copy()
        projection_month_start = projection_anchor + relativedelta(months=i)
        context.month_start = projection_month_start
        
        new_fy = utils.get_uk_fiscal_year(projection_month_start)
        if new_fy != current_fy: 
            context.ytd_contributions = {}
            context.ytd_earnings = {}
            context.ytd_interest = {}
            context.ytd_gains = {}
            current_fy = new_fy
            
        context.flows = {acc.id: {"income": 0, "costs": 0, "transfers_in": 0, "transfers_out": 0, "mortgage_payments_out": 0, "mortgage_repayments_in": 0, "interest": 0, "events": 0, "tax": 0, "cgt": 0, "employer_contribution": 0} for acc in all_accounts}
        
        # --- PROCESSOR LOOP ---
        process_income(scenario, context)
        process_costs(scenario, context)
        process_transfers(scenario, context)
        process_events(scenario, context)
        process_rsu_vesting(scenario, context)
        process_standard_mortgage_payments(scenario, context)
        process_rules(scenario, context)
        process_interest(scenario, context)
        
        # FEATURE: Decumulation
        process_decumulation(scenario, context)
        # ----------------------
        
        detect_milestones(context)

        current_breakdown, current_total = calculate_gbp_balances(context.account_balances, all_accounts, scenario.gbp_to_usd_rate, projection_month_start)
        end_of_month = projection_month_start + relativedelta(months=1, days=-1)
        
        flows_for_schema = {acc_id: schemas.ProjectionFlows(**flow_data) for acc_id, flow_data in context.flows.items()}
        
        data_points.append(schemas.ProjectionDataPoint(date=end_of_month, balance=current_total, account_balances=current_breakdown, flows=flows_for_schema))
        
        # Warnings check
        for acc in all_accounts:
            if acc.account_type == enums.AccountType.CASH or acc.account_type == enums.AccountType.INVESTMENT:
                current_bal = context.account_balances[acc.id]
                min_bal = acc.min_balance or 0
                if current_bal < min_bal:
                    context.warnings.append(schemas.ProjectionWarning(date=context.month_start, account_id=acc.id, message=f"Negative Balance: {acc.name} is overdrawn ({utils.format_currency(current_bal)}).", source_type="balance", source_id=acc.id))

    # Deduplicate warnings
    unique_warnings = []
    seen_warnings = set() 
    for w in context.warnings:
        year = w.date.year
        if w.source_type == "balance": key = (year, w.account_id, "balance")
        elif w.source_type in ["income", "transfer", "event", "rsu_vest"]: key = (year, w.source_type, w.source_id, w.account_id)
        else: key = (w.account_id, w.message)
        if key not in seen_warnings: 
            unique_warnings.append(w)
            seen_warnings.add(key)
            
    return schemas.Projection(
        data_points=data_points, 
        warnings=unique_warnings, 
        rule_logs=context.rule_logs, 
        mortgage_stats=context.mortgage_stats, 
        annotations=context.annotations
    )
