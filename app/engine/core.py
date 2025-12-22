from sqlalchemy.orm import Session
from typing import List, Any, Optional, Dict
from app import models, schemas, enums, utils
from .context import ProjectionContext
from .processors import income, costs, transfers, mortgage, tax, rsu, growth, rules, decumulation, events
from .helpers import calculate_gbp_balances, _get_enum_value
from dateutil.relativedelta import relativedelta
from datetime import date
import logging

logger = logging.getLogger(__name__)

def apply_simulation_overrides(scenario: models.Scenario, overrides: List[schemas.SimulationOverride]):
    for override in overrides:
        if override.type == 'account':
            acc = next((a for a in scenario.accounts if a.id == override.id), None)
            if acc and hasattr(acc, override.field): setattr(acc, override.field, override.value)
        elif override.type == 'income':
            for owner in scenario.owners:
                inc = next((i for i in owner.income_sources if i.id == override.id), None)
                if inc and hasattr(inc, override.field): setattr(inc, override.field, override.value)
        elif override.type == 'cost':
            cost = next((c for c in scenario.costs if c.id == override.id), None)
            if cost and hasattr(cost, override.field): setattr(cost, override.field, override.value)
        elif override.type == 'transfer':
            trans = next((t for t in scenario.transfers if t.id == override.id), None)
            if trans and hasattr(trans, override.field): setattr(trans, override.field, override.value)
        elif override.type == 'event':
            evt = next((e for e in scenario.financial_events if e.id == override.id), None)
            if evt and hasattr(evt, override.field): setattr(evt, override.field, override.value)
        elif override.type == 'tax_limit':
            limit = next((t for t in scenario.tax_limits if t.id == override.id), None)
            if limit and hasattr(limit, override.field): setattr(limit, override.field, override.value)
        elif override.type == 'rule':
            rule = next((r for r in scenario.automation_rules if r.id == override.id), None)
            if rule and hasattr(rule, override.field): setattr(rule, override.field, override.value)

def run_projection(db: Session, scenario: models.Scenario, months: int, overrides: list = None) -> schemas.ProjectionResult:
    if overrides is None: overrides = []
    
    all_accounts = scenario.accounts
    start_date = scenario.start_date
    initial_balances = {acc.id: acc.starting_balance for acc in all_accounts}
    initial_costs = {acc.id: (acc.book_cost if acc.book_cost is not None else acc.starting_balance) for acc in all_accounts}
    
    context = ProjectionContext(
        month_start=start_date,
        account_balances=initial_balances,
        account_book_costs=initial_costs,
        flows={},
        all_accounts=all_accounts
    )
    
    for ann in scenario.chart_annotations:
        context.annotations.append(schemas.ProjectionAnnotation(date=ann.date, label=ann.label, type=ann.annotation_type))

    # Initial Data Point
    initial_breakdown, initial_total = calculate_gbp_balances(context.account_balances, all_accounts, scenario.gbp_to_usd_rate, start_date)
    context.data_points.append(schemas.ProjectionDataPoint(
        date=start_date,
        balance=initial_total,
        liquid_assets=0,
        account_balances=initial_breakdown,
        flows={}
    ))

    projection_anchor = start_date.replace(day=1)
    current_fy = utils.get_uk_fiscal_year(start_date)
    
    prev_metrics = {'liquid': 0, 'liability': 999999999999} 

    for i in range(months):
        context.prev_balances = context.account_balances.copy()
        projection_month_start = projection_anchor + relativedelta(months=i)
        context.month_start = projection_month_start
        
        # FY Reset
        new_fy = utils.get_uk_fiscal_year(projection_month_start)
        if new_fy != current_fy:
             context.ytd_contributions = {}
             context.ytd_earnings = {}
             context.ytd_interest = {}
             context.ytd_gains = {}
             current_fy = new_fy
             
        # Reset Flows
        context.flows = {acc.id: {
            "income": 0, "costs": 0, "transfers_in": 0, "transfers_out": 0, 
            "mortgage_payments_out": 0, "mortgage_repayments_in": 0, 
            "interest": 0, "events": 0, "tax": 0, "cgt": 0, "employer_contribution": 0, "growth": 0
        } for acc in all_accounts}

        # --- PROCESSORS ---
        income.process_income(scenario, context)
        costs.process_costs(scenario, context)
        transfers.process_transfers(scenario, context)
        events.process_events(scenario, context)
        rsu.process_rsu_vesting(scenario, context)
        mortgage.process_mortgages(scenario, context)
        rules.process_rules(scenario, context)
        decumulation.process_decumulation(scenario, context)
        growth.process_growth(scenario, context)
        
        # --- MILESTONE & RETIREMENT CHECKS ---
        for owner in scenario.owners:
            if owner.birth_date and owner.retirement_age:
                ret_date = owner.birth_date + relativedelta(years=owner.retirement_age)
                if ret_date.year == projection_month_start.year and ret_date.month == projection_month_start.month:
                    context.annotations.append(schemas.ProjectionAnnotation(
                        date=projection_month_start,
                        label=f"{owner.name} Retires",
                        type="milestone"
                    ))

        # Snapshot
        current_breakdown, current_total = calculate_gbp_balances(context.account_balances, all_accounts, scenario.gbp_to_usd_rate, projection_month_start)
        end_of_month = projection_month_start + relativedelta(months=1, days=-1)
        
        # Calculate Metrics & Detect Cleared Mortgages
        liquid_val = 0
        liability_val = 0
        
        for acc in all_accounts:
            bal_pence = context.account_balances.get(acc.id, 0)
            type_val = _get_enum_value(acc.account_type)
            wrapper_val = _get_enum_value(acc.tax_wrapper)
            
            # --- Detect Individual Mortgage Clearance ---
            # Transition from <0 (Debt) to >=0 (Cleared)
            if type_val in ["Mortgage", "Loan"]:
                prev_bal = context.prev_balances.get(acc.id, 0)
                if prev_bal < 0 and bal_pence >= 0:
                    context.annotations.append(schemas.ProjectionAnnotation(
                        date=projection_month_start,
                        label=f"{acc.name} Cleared",
                        type="success"
                    ))

            # --- Liquid Assets Logic ---
            # Convert USD to GBP for apples-to-apples comparison
            val_gbp = bal_pence
            if _get_enum_value(acc.currency) == "USD":
                val_gbp = round(bal_pence / scenario.gbp_to_usd_rate)

            is_liquid = True
            if type_val in ["Mortgage", "Loan", "Property", "Main Residence", "RSU Grant"]:
                is_liquid = False
            if wrapper_val in ["Pension", "Lifetime ISA"]:
                is_liquid = False
            
            if is_liquid:
                liquid_val += val_gbp
            
            if type_val in ["Mortgage", "Loan"] and bal_pence < 0:
                liability_val += abs(val_gbp)

        # Skip milestone checks for the very first month to avoid "Start State" triggers
        if i > 0:
            if prev_metrics['liquid'] < prev_metrics['liability'] and liquid_val >= liability_val:
                 context.annotations.append(schemas.ProjectionAnnotation(
                     date=projection_month_start,
                     label="Liquid Assets > Liabilities",
                     type="success"
                 ))
            
            if prev_metrics['liability'] > 0 and liability_val == 0:
                 context.annotations.append(schemas.ProjectionAnnotation(
                     date=projection_month_start,
                     label="Debt Free", 
                     type="success"
                 ))

        prev_metrics = {'liquid': liquid_val, 'liability': liability_val}

        flows_for_schema = {acc_id: schemas.ProjectionFlows(**flow_data) for acc_id, flow_data in context.flows.items()}
        
        context.data_points.append(schemas.ProjectionDataPoint(
            date=end_of_month,
            balance=current_total,
            liquid_assets=liquid_val / 100.0, 
            account_balances=current_breakdown,
            flows=flows_for_schema
        ))
        
        context.advance_month()

    return schemas.ProjectionResult(
        data_points=context.data_points,
        warnings=context.warnings,
        rule_logs=context.rule_logs,
        mortgage_stats=context.mortgage_stats,
        annotations=context.annotations,
        metadata={"currency": "GBP"}
    )
