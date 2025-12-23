import pytest
from datetime import date
from app import models, enums
from app.engine.context import ProjectionContext
from app.engine.processors.decumulation import process_decumulation, solve_gross_withdrawal

# Mock classes
class MockScenario:
    def __init__(self):
        self.decumulation_strategies = []
        self.tax_limits = []
        self.gbp_to_usd_rate = 1.25

class MockStrategy:
    def __init__(self):
        self.enabled = True
        self.start_date = date(2025, 1, 1)
        self.end_date = None

def test_simple_isa_withdrawal():
    """
    Test that ISA withdrawals are 1:1 (No Tax)
    """
    scen = MockScenario()
    scen.decumulation_strategies = [MockStrategy()]
    
    # Setup: 1 Cash Account (Deficit -1000), 1 ISA Account (+5000)
    acc_cash = models.Account(id=1, name="Cash", account_type=enums.AccountType.CASH, min_balance=0)
    acc_isa = models.Account(id=2, name="ISA", account_type=enums.AccountType.INVESTMENT, tax_wrapper=enums.TaxWrapper.ISA)
    
    context = ProjectionContext(
        month_start=date(2025, 6, 1),
        account_balances={1: -100000, 2: 500000}, # -£1000, +£5000
        account_book_costs={1: 0, 2: 500000},
        flows={1: {"transfers_in": 0, "transfers_out": 0}, 2: {"transfers_in": 0, "transfers_out": 0, "tax": 0, "cgt": 0}},
        all_accounts=[acc_cash, acc_isa],
        prev_balances={}
    )
    
    process_decumulation(scen, context)
    
    # Check Cash is zero'd
    assert context.account_balances[1] == 0
    # Check ISA is reduced by exactly 100000 (1000 pounds)
    assert context.account_balances[2] == 400000 
    # Check Flows
    assert context.flows[2]["transfers_out"] == 100000

def test_pension_withdrawal_tax():
    """
    Test that Pension withdrawals Gross Up correctly.
    Assume 25% Tax Free, 20% Tax on remainder (Basic Rate).
    Effective Tax Rate = 0.75 * 0.20 = 15%.
    To get £850 Net, we need to sell £1000 Gross.
    """
    scen = MockScenario()
    scen.decumulation_strategies = [MockStrategy()]
    
    owner = models.Owner(id=1, name="Retiree", birth_date=date(1950, 1, 1))
    
    acc_cash = models.Account(id=1, name="Cash", account_type=enums.AccountType.CASH)
    acc_pension = models.Account(id=2, name="Pension", account_type=enums.AccountType.INVESTMENT, tax_wrapper=enums.TaxWrapper.PENSION)
    acc_pension.owners = [owner]
    
    # Deficit of £850 (85000p)
    # Pension has £10,000 (1000000p)
    context = ProjectionContext(
        month_start=date(2025, 6, 1),
        account_balances={1: -85000, 2: 1000000}, 
        account_book_costs={1: 0, 2: 1000000},
        flows={1: {"transfers_in": 0}, 2: {"transfers_out": 0, "tax": 0, "cgt": 0}},
        all_accounts=[acc_cash, acc_pension],
        prev_balances={},
        ytd_earnings={1: {'taxable': 2000000, 'ni': 0}} # Already earned £20k (Basic Rate)
    )
    
    process_decumulation(scen, context)
    
    # Expected: 
    # Sell £1000 Gross.
    # Taxable = £750.
    # Tax @ 20% = £150.
    # Net = £850.
    # Cash Balance = 0.
    
    assert context.account_balances[1] == 0
    # Pension should decrease by approx £1000 (allow rounding diff)
    loss = 1000000 - context.account_balances[2]
    assert 99990 <= loss <= 100010
    
    # Check Tax Flow
    assert 14900 <= context.flows[2]["tax"] <= 15100
