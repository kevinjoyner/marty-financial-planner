import math

class TaxService:
    """
    Service for calculating UK Income Tax, NI, and Capital Gains Tax.
    Based on 2024/2025 Tax Year Rules.
    """

    # --- Constants for 2024/25 ---
    PERSONAL_ALLOWANCE = 12570
    BASIC_RATE_LIMIT = 50270
    ADDITIONAL_RATE_LIMIT = 125140
    
    RATE_BASIC = 0.20
    RATE_HIGHER = 0.40
    RATE_ADDITIONAL = 0.45

    NI_PRIMARY_THRESHOLD = 12570
    NI_UPPER_EARNINGS_LIMIT = 50270
    NI_RATE_MAIN = 0.08
    NI_RATE_ADDITIONAL = 0.02
    
    PSA_BASIC = 1000
    PSA_HIGHER = 500
    PSA_ADDITIONAL = 0

    # CGT Constants (24/25)
    CGT_ALLOWANCE = 3000
    CGT_RATE_BASIC = 0.18  # Residential/Investment blended rate approximation (using higher rates for safety)
    CGT_RATE_HIGHER = 0.24 # Post-Oct 2024 Budget Rate

    @staticmethod
    def calculate_capital_gains_tax(marginal_gain_pence: int, ytd_gains_pence: int, total_income_pence: int) -> int:
        """
        Calculates CGT on a specific realized gain transaction.
        
        Args:
            marginal_gain_pence: The gain made in this specific transaction.
            ytd_gains_pence: Gains realized YTD *before* this transaction.
            total_income_pence: Total Taxable Income (Salary+Interest) to determine band.
        """
        gain_gbp = marginal_gain_pence / 100.0
        prior_gains_gbp = ytd_gains_pence / 100.0
        total_income_gbp = total_income_pence / 100.0
        
        # 1. Determine Rate based on Income Band
        # If Total Income < 50,270, gains *might* be taxed at 18%, but if gain pushes total > 50k, excess is 24%.
        # Simplified Logic: If you are already Higher Rate, pay 24%. 
        # If Basic, check if gain fits in band.
        
        # Calculate unused Basic Band
        unused_basic_band = max(0, TaxService.BASIC_RATE_LIMIT - total_income_gbp)
        
        # 2. Apply Allowance logic to the MARGINAL gain
        # We assume allowance is used up sequentially.
        
        # Total cumulative gain
        total_cum_gain = prior_gains_gbp + gain_gbp
        
        # Taxable part of total cumulative
        taxable_cum = max(0, total_cum_gain - TaxService.CGT_ALLOWANCE)
        
        # Taxable part of prior
        taxable_prior = max(0, prior_gains_gbp - TaxService.CGT_ALLOWANCE)
        
        # Taxable part of THIS transaction
        taxable_marginal = taxable_cum - taxable_prior
        
        if taxable_marginal <= 0:
            return 0
            
        # 3. Calculate Tax on the marginal amount
        # We need to know how much of this marginal gain falls into Basic vs Higher
        # Note: Gains sit "on top" of income.
        # We effectively need to treat 'prior gains' as filling the band too? 
        # UK Law: "Taxable gains are added to your taxable income".
        # So we add (Taxable Prior Gains) to Income to see where THIS gain sits.
        
        # Base for this calc = Total Income + Taxable Prior Gains
        # FIX: Ensure we don't count unused Personal Allowance as 'Basic Band' for CGT purposes.
        # Effectively, the band is consumed by Income (floored at PA) + Prior Gains.
        adjusted_income = max(total_income_gbp, TaxService.PERSONAL_ALLOWANCE)
        income_base = adjusted_income + taxable_prior
        
        # Band Logic
        amount_in_basic = 0
        amount_in_higher = 0
        
        remaining_band = max(0, TaxService.BASIC_RATE_LIMIT - income_base)
        
        if remaining_band > 0:
            amount_in_basic = min(taxable_marginal, remaining_band)
            amount_in_higher = taxable_marginal - amount_in_basic
        else:
            amount_in_higher = taxable_marginal
            
        tax = (amount_in_basic * TaxService.CGT_RATE_BASIC) + (amount_in_higher * TaxService.CGT_RATE_HIGHER)
        
        return int(tax * 100)

    @staticmethod
    def calculate_savings_tax(gross_interest_pence: int, ytd_total_income_pence: int, ytd_interest_pence: int) -> int:
        gross_interest = gross_interest_pence / 100.0
        total_income = ytd_total_income_pence / 100.0
        prior_interest = ytd_interest_pence / 100.0
        
        psa = TaxService.PSA_BASIC
        if total_income > TaxService.ADDITIONAL_RATE_LIMIT: psa = TaxService.PSA_ADDITIONAL
        elif total_income > TaxService.BASIC_RATE_LIMIT: psa = TaxService.PSA_HIGHER
            
        psa_used = min(prior_interest, psa)
        psa_remaining = max(0, psa - psa_used)
        
        taxable_interest = max(0, gross_interest - psa_remaining)
        
        if taxable_interest <= 0: return 0
            
        tax_rate = TaxService.RATE_BASIC
        if total_income > TaxService.ADDITIONAL_RATE_LIMIT: tax_rate = TaxService.RATE_ADDITIONAL
        elif total_income > TaxService.BASIC_RATE_LIMIT: tax_rate = TaxService.RATE_HIGHER
            
        return int(taxable_interest * tax_rate * 100)

    @staticmethod
    def calculate_payroll_deductions(amount_for_tax: int, amount_for_ni: int, ytd_taxable: int, ytd_niable: int) -> int:
        # Income Tax
        gross_tax_gbp = amount_for_tax / 100.0
        ytd_tax_gbp = ytd_taxable / 100.0
        total_tax_income = ytd_tax_gbp + gross_tax_gbp
        tax_total = TaxService._calculate_income_tax(total_tax_income)
        tax_prior = TaxService._calculate_income_tax(ytd_tax_gbp)
        income_tax_due = tax_total - tax_prior
        
        # NI
        gross_ni_gbp = amount_for_ni / 100.0
        ytd_ni_gbp = ytd_niable / 100.0
        total_ni_income = ytd_ni_gbp + gross_ni_gbp
        ni_total = TaxService._calculate_national_insurance(total_ni_income)
        ni_prior = TaxService._calculate_national_insurance(ytd_ni_gbp)
        ni_due = ni_total - ni_prior
        
        return int((income_tax_due + ni_due) * 100)

    @staticmethod
    def calculate_tax_on_vest(gross_amount: int, owner_id: int, ytd_earnings: int = 0) -> int:
        return TaxService.calculate_payroll_deductions(gross_amount, gross_amount, ytd_earnings, ytd_earnings)

    @staticmethod
    def _calculate_income_tax(annual_income: float) -> float:
        if annual_income <= 0: return 0.0
        allowance = TaxService.PERSONAL_ALLOWANCE
        if annual_income > 100000:
            reduction = (annual_income - 100000) / 2
            allowance = max(0, allowance - reduction)
        taxable_income = max(0, annual_income - allowance)
        if taxable_income == 0: return 0.0
        tax = 0.0
        BASIC_BAND_SIZE = 37700
        remaining_taxable = taxable_income
        in_basic = min(remaining_taxable, BASIC_BAND_SIZE)
        tax += in_basic * TaxService.RATE_BASIC
        remaining_taxable -= in_basic
        if remaining_taxable <= 0: return tax
        additional_threshold_taxable = TaxService.ADDITIONAL_RATE_LIMIT - allowance
        higher_band_limit = max(0, additional_threshold_taxable - BASIC_BAND_SIZE)
        in_higher = min(remaining_taxable, higher_band_limit)
        tax += in_higher * TaxService.RATE_HIGHER
        remaining_taxable -= in_higher
        if remaining_taxable <= 0: return tax
        tax += remaining_taxable * TaxService.RATE_ADDITIONAL
        return tax

    @staticmethod
    def _calculate_national_insurance(annual_income: float) -> float:
        if annual_income <= TaxService.NI_PRIMARY_THRESHOLD: return 0.0
        ni = 0.0
        band1_income = min(annual_income, TaxService.NI_UPPER_EARNINGS_LIMIT) - TaxService.NI_PRIMARY_THRESHOLD
        ni += max(0, band1_income * TaxService.NI_RATE_MAIN)
        if annual_income > TaxService.NI_UPPER_EARNINGS_LIMIT:
            band2_income = annual_income - TaxService.NI_UPPER_EARNINGS_LIMIT
            ni += band2_income * TaxService.NI_RATE_ADDITIONAL
        return ni
