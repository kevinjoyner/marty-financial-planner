from dateutil.relativedelta import relativedelta
from app import models, enums
from app.services.tax import TaxService
from app.engine.context import ProjectionContext

def process_interest(scenario: models.Scenario, context: ProjectionContext):
    for acc in context.all_accounts:
        if acc.account_type == enums.AccountType.MORTGAGE and context.account_balances[acc.id] < 0:
            safe_interest_rate = acc.interest_rate or 0.0
            if acc.mortgage_start_date and acc.fixed_rate_period_years and acc.fixed_interest_rate is not None:
                fixed_end_date = acc.mortgage_start_date + relativedelta(years=acc.fixed_rate_period_years)
                if context.month_start < fixed_end_date: safe_interest_rate = acc.fixed_interest_rate
            monthly_rate = safe_interest_rate / 100 / 12; interest_charged = abs(context.account_balances[acc.id]) * monthly_rate
            context.account_balances[acc.id] -= round(interest_charged); context.flows[acc.id]["interest"] -= round(interest_charged) / 100.0
        elif acc.account_type == enums.AccountType.RSU_GRANT: pass
        elif acc.account_type != enums.AccountType.MORTGAGE:
            safe_interest_rate = acc.interest_rate or 0.0
            if safe_interest_rate != 0:
                monthly_rate = safe_interest_rate / 100 / 12; interest_gross = context.account_balances[acc.id] * monthly_rate; interest_gross_int = round(interest_gross)
                tax_deducted = 0
                
                is_taxable = (not acc.tax_wrapper or acc.tax_wrapper == enums.TaxWrapper.NONE)
                is_real_property = (acc.account_type in [enums.AccountType.PROPERTY, enums.AccountType.MAIN_RESIDENCE])

                if interest_gross_int > 0 and is_taxable and not is_real_property:
                    # SPLIT INTEREST LOGIC
                    owners = acc.owners if acc.owners else []
                    if owners:
                        num_owners = len(owners)
                        interest_per_owner = int(interest_gross_int / num_owners)
                        total_tax = 0
                        for owner in owners:
                            earnings = context.ytd_earnings.get(owner.id, {}).get('taxable', 0)
                            prior_interest = context.ytd_interest.get(owner.id, 0)
                            # Each owner gets their own PSA calculation
                            tax = TaxService.calculate_savings_tax(interest_per_owner, earnings + prior_interest, prior_interest)
                            
                            if owner.id not in context.ytd_interest: context.ytd_interest[owner.id] = 0
                            context.ytd_interest[owner.id] += interest_per_owner
                            total_tax += tax
                        tax_deducted = total_tax
                    else:
                        # Fallback for ownerless accounts (shouldn't happen, but safe default)
                        tax_deducted = 0
                
                interest_net_int = interest_gross_int - tax_deducted
                context.account_balances[acc.id] += interest_net_int; context.flows[acc.id]["interest"] += interest_gross_int / 100.0; context.flows[acc.id]["tax"] += tax_deducted / 100.0
