from app import models
from app.engine.context import ProjectionContext
import logging

logger = logging.getLogger(__name__)

def process_tax_year_end(scenario: models.Scenario, context: ProjectionContext):
    """
    Finalize the tax year and reset YTD counters for the new year.
    Should typically run at the end of Month 3 (March) for UK Tax years,
    so that Month 4 (April) starts with clean 0.00 counters.
    """
    # 1. Reset Earnings (Income Tax / NI)
    context.ytd_earnings = {}
    
    # 2. Reset Contributions (ISA/Pension Limits)
    context.ytd_contributions = {}
    
    # 3. Reset Savings Interest & Capital Gains
    context.ytd_interest = {}
    context.ytd_gains = {}
    
    # Optional: We could log a "Tax Year End" event here if we wanted to audit it.
    # logger.info(f"Tax Year Reset performed at {context.month_start}")
