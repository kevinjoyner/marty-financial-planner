from app.services.tax import TaxService
import pytest

def test_cgt_low_income_personal_allowance_leakage():
    """
    Verifies that unused Personal Allowance does NOT extend the Basic Rate Band for CGT.

    Scenario:
    - Total Income: £10,000 (Below Personal Allowance of £12,570)
    - Capital Gain: £45,000
    - CGT Allowance: £3,000
    - Taxable Gain: £42,000

    Correct Logic:
    - Taxable Income is 0.
    - Used Basic Rate Band is 0.
    - Available Basic Rate Band for CGT is £37,700 (Full Band).
    - Gain in Basic Band (18%): £37,700
    - Gain in Higher Band (24%): £42,000 - £37,700 = £4,300

    Total Tax:
    (37,700 * 0.18) + (4,300 * 0.24)
    = 6,786 + 1,032
    = 7,818
    """

    income_pence = 10000 * 100
    gain_pence = 45000 * 100
    ytd_gains_pence = 0 # First gain of the year

    expected_tax_pence = 7818 * 100

    calculated_tax_pence = TaxService.calculate_capital_gains_tax(gain_pence, ytd_gains_pence, income_pence)

    # We allow a small margin for rounding differences, though integers should be exact here.
    assert abs(calculated_tax_pence - expected_tax_pence) < 100, \
        f"Expected {expected_tax_pence} pence, got {calculated_tax_pence} pence. \
        The system may be incorrectly using Personal Allowance to expand the Basic Rate Band."

def test_cgt_standard_basic_payer():
    """
    Scenario:
    - Income: £20,000 (Taxable: £7,430)
    - Remaining Basic Band: £30,270
    - Gain: £10,000
    - Taxable Gain: £7,000 (after £3k allowance)
    - All fits in Basic Band (18%).
    """
    income_pence = 20000 * 100
    gain_pence = 10000 * 100
    expected_tax_pence = 7000 * 0.18 * 100

    calculated = TaxService.calculate_capital_gains_tax(gain_pence, 0, income_pence)
    assert abs(calculated - expected_tax_pence) < 50

def test_cgt_higher_rate_payer():
    """
    Scenario:
    - Income: £60,000 (Higher Rate)
    - Gain: £10,000
    - Taxable Gain: £7,000
    - All at 24%.
    """
    income_pence = 60000 * 100
    gain_pence = 10000 * 100
    expected_tax_pence = 7000 * 0.24 * 100

    calculated = TaxService.calculate_capital_gains_tax(gain_pence, 0, income_pence)
    assert abs(calculated - expected_tax_pence) < 50
