from datetime import date
from app import models, schemas, engine

def test_run_projection_empty_scenario_returns_data_points():
    """
    Regression Test:
    A completely empty scenario (no accounts, no owners) used to cause the engine
    to return an empty list of data_points. This caused the Frontend Chart to crash/hang.
    The engine should now return a valid timeline of 'zero' data points.
    """
    scenario = models.Scenario(
        id=999, 
        name="Empty Crash Test", 
        start_date=date(2025, 1, 1),
        gbp_to_usd_rate=1.25
    )
    # Explicitly ensure these are empty lists
    scenario.accounts = []
    scenario.owners = []
    scenario.costs = []
    scenario.transfers = []
    scenario.financial_events = []
    scenario.tax_limits = []
    scenario.automation_rules = []
    scenario.chart_annotations = []
    
    # Run for 12 months
    months_to_run = 12
    proj = engine.run_projection(None, scenario, months_to_run)
    
    # Expect 1 initial point + 12 monthly points = 13 total
    assert len(proj.data_points) == months_to_run + 1
    
    # Verify the first point is zero
    assert proj.data_points[0].balance == 0
    assert proj.data_points[0].account_balances == {}
    
    # Verify the last point is zero
    assert proj.data_points[-1].balance == 0

