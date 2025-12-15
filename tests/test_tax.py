from app.services.tax import TaxService
import pytest

def test_income_tax_bands():
    # 1. Below Personal Allowance (£12,570)
    assert TaxService._calculate_income_tax(10000) == 0
    
    # 2. Basic Rate (£20,000)
    # Taxable: 20,000 - 12,570 = 7,430
    # Tax: 7,430 * 0.20 = 1,486
    assert abs(TaxService._calculate_income_tax(20000) - 1486) < 1

    # 3. Higher Rate (£60,000)
    # Allowance: 12,570
    # Taxable: 47,430
    # Basic Band (37,700 * 0.20) = 7,540
    # Higher Band (9,730 * 0.40) = 3,892
    # Total: 11,432
    assert abs(TaxService._calculate_income_tax(60000) - 11432) < 1

    # 4. Taper Zone (£110,000)
    # Income > 100k by 10k. Allowance reduced by 5k.
    # New Allowance: 12,570 - 5,000 = 7,570
    # Taxable: 102,430
    # Basic Band (37,700 * 0.20) = 7,540
    # Higher Band (Remaining up to 125,140):
    # Additional Threshold Taxable = 125,140 - 7,570 = 117,570
    # Remaining for Higher: 102,430 - 37,700 = 64,730. (All within Higher)
    # Higher Tax: 64,730 * 0.40 = 25,892
    # Total: 33,432
    assert abs(TaxService._calculate_income_tax(110000) - 33432) < 1

    # 5. Additional Rate (£150,000)
    # Allowance: 0 (Fully tapered)
    # Taxable: 150,000
    # Basic Band (37,700 * 0.20) = 7,540
    # Higher Band (up to 125,140 total income)
    # The Higher band fills the gap between 37,700 taxable and 125,140 taxable.
    # Gap: 125,140 - 37,700 = 87,440.
    # Higher Tax: 87,440 * 0.40 = 34,976
    # Additional Band (150,000 - 125,140) = 24,860
    # Additional Tax: 24,860 * 0.45 = 11,187
    # Total: 7,540 + 34,976 + 11,187 = 53,703
    assert abs(TaxService._calculate_income_tax(150000) - 53703) < 1

def test_national_insurance():
    # 1. Below Threshold (£10,000)
    assert TaxService._calculate_national_insurance(10000) == 0
    
    # 2. Standard Rate (£30,000)
    # 30,000 - 12,570 = 17,430
    # 17,430 * 0.08 = 1,394.4
    assert abs(TaxService._calculate_national_insurance(30000) - 1394.4) < 1
    
    # 3. Upper Earnings (£60,000)
    # Band 1: (50,270 - 12,570) = 37,700 * 0.08 = 3,016
    # Band 2: (60,000 - 50,270) = 9,730 * 0.02 = 194.6
    # Total: 3,210.6
    assert abs(TaxService._calculate_national_insurance(60000) - 3210.6) < 1

def test_marginal_calculation():
    # Test adding a £10k bonus on top of £50k salary
    # £50k Salary Tax: (37,430 * 0.2) = 7,486 (Approx)
    # £60k Total Tax: 11,432 (from above)
    # Marginal Tax on Bonus: 3,946 (Approx 40%)
    
    # Input in Pence
    bonus = 10000 * 100
    salary_ytd = 50000 * 100
    
    tax_pence = TaxService.calculate_tax_on_vest(bonus, 1, salary_ytd)
    tax_gbp = tax_pence / 100.0
    
    # NI on 50k is all at 8%. NI on next 10k is mainly at 2% (above 50,270).
    # This checks combined logic.
    assert tax_gbp > 3000 # Should be roughly 40% income + 2% NI
