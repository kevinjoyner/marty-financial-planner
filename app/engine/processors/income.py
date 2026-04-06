from app import models, enums, schemas
from app.engine.context import ProjectionContext
from app.services.tax import TaxService
from app.engine.helpers import track_contribution, get_contribution_headroom
from app.engine.tax_logic import calculate_tapered_annual_allowance


def _cadence_annual_factor(cadence_str: str) -> int:
    if cadence_str == 'annually': return 1
    if cadence_str == 'quarterly': return 4
    return 12


def process_income(scenario: models.Scenario, context: ProjectionContext):
    seen_ids = set()
    all_income_sources = []
    for owner in scenario.owners:
        for inc in owner.income_sources:
            if inc.id not in seen_ids:
                all_income_sources.append(inc)
                seen_ids.add(inc.id)

    for inc in all_income_sources:
        if inc.account_id not in context.account_balances: continue

        if inc.start_date is None: continue

        start_valid = inc.start_date.replace(day=1) <= context.month_start
        end_valid = (inc.end_date is None or inc.end_date >= context.month_start)
        if not (start_valid and end_valid): continue

        cadence_str = inc.cadence.value if hasattr(inc.cadence, 'value') else str(inc.cadence)

        should = False
        if cadence_str == 'once':
            if context.month_start.year == inc.start_date.year and context.month_start.month == inc.start_date.month: should = True
        elif cadence_str == 'monthly': should = True
        elif cadence_str == 'quarterly' and context.month_start.month in [1, 4, 7, 10]: should = True
        elif cadence_str == 'annually' and context.month_start.month == inc.start_date.month: should = True

        if should:
            if inc.owner_id not in context.ytd_earnings: context.ytd_earnings[inc.owner_id] = {'taxable': 0, 'ni': 0}

            gross_input = int(inc.net_value)
            net_to_pay = gross_input
            tax_deducted = 0

            # --- Resolve effective sacrifice and employer amounts ---
            # % mode takes precedence over fixed-pence fields when set.
            sac_percent = getattr(inc, 'salary_sacrifice_percent', None)
            emp_match_percent = getattr(inc, 'employer_match_percent', None)
            ni_supplement_enabled = getattr(inc, 'employer_ni_supplement', False) or False
            ni_rate_pct = getattr(inc, 'employer_ni_rate', None)

            if sac_percent is not None:
                effective_sacrifice = int(round(gross_input * sac_percent / 100))
            else:
                effective_sacrifice = int(inc.salary_sacrifice_value or 0)

            if emp_match_percent is not None:
                matched_pct = min(sac_percent or 0, emp_match_percent)
                effective_employer_match = int(round(gross_input * matched_pct / 100))
            else:
                effective_employer_match = int(inc.employer_pension_contribution or 0)

            ni_supplement = 0
            if ni_supplement_enabled:
                # employer_ni_rate stored as percentage (e.g. 15 for 15%); default 15
                ni_rate = (ni_rate_pct if ni_rate_pct is not None else 15.0) / 100.0
                ni_supplement = int(round(effective_sacrifice * ni_rate))

            total_employer = effective_employer_match + ni_supplement

            # --- Employer contribution (match + NI supplement) → pension account ---
            if total_employer > 0 and inc.salary_sacrifice_account_id:
                sac_target = inc.salary_sacrifice_account_id
                if sac_target in context.account_balances:
                    context.account_balances[sac_target] += total_employer
                    context.account_book_costs[sac_target] += total_employer
                    if sac_target not in context.flows: context.flows[sac_target] = {}
                    if "employer_contribution" not in context.flows[sac_target]: context.flows[sac_target]["employer_contribution"] = 0
                    context.flows[sac_target]["employer_contribution"] += total_employer
                    track_contribution(context, sac_target, total_employer)

            # --- Salary sacrifice and payroll tax ---
            if inc.is_pre_tax:
                sac_target = inc.salary_sacrifice_account_id
                adjusted_gross = max(0, gross_input - effective_sacrifice)

                if effective_sacrifice > 0 and sac_target and sac_target in context.account_balances:
                    context.account_balances[sac_target] += effective_sacrifice
                    context.account_book_costs[sac_target] += effective_sacrifice
                    track_contribution(context, sac_target, effective_sacrifice)

                bik_amount = inc.taxable_benefit_value or 0
                amount_for_tax = adjusted_gross + bik_amount
                amount_for_ni = adjusted_gross

                current_ytd_tax = context.ytd_earnings[inc.owner_id]['taxable']
                current_ytd_ni = context.ytd_earnings[inc.owner_id]['ni']
                tax_deducted = TaxService.calculate_payroll_deductions(amount_for_tax, amount_for_ni, current_ytd_tax, current_ytd_ni)

                context.ytd_earnings[inc.owner_id]['taxable'] += amount_for_tax
                context.ytd_earnings[inc.owner_id]['ni'] += amount_for_ni
                net_to_pay = adjusted_gross - tax_deducted

                # --- Annual pension and tax insights (emit once per income source per projection) ---
                insight_key = f"pension_insight_{inc.id}"
                if insight_key not in context.emitted_annual_insights and (effective_sacrifice > 0 or total_employer > 0):
                    context.emitted_annual_insights.add(insight_key)
                    af = _cadence_annual_factor(cadence_str)
                    annual_gross = gross_input * af
                    annual_sacrifice = effective_sacrifice * af
                    annual_employer = total_employer * af
                    annual_emp_match = effective_employer_match * af
                    annual_ni_supp = ni_supplement * af
                    annual_total_contrib = annual_sacrifice + annual_employer
                    annual_post_sacrifice = annual_gross - annual_sacrifice

                    gross_gbp = annual_gross / 100.0
                    post_sac_gbp = annual_post_sacrifice / 100.0
                    total_contrib_gbp = annual_total_contrib / 100.0
                    employer_gbp = annual_employer / 100.0
                    sac_gbp = annual_sacrifice / 100.0

                    # Tapered Annual Allowance check
                    adjusted_income_gbp = post_sac_gbp + employer_gbp
                    tapered_aa_gbp = calculate_tapered_annual_allowance(post_sac_gbp, adjusted_income_gbp)

                    if total_contrib_gbp > tapered_aa_gbp:
                        excess_gbp = total_contrib_gbp - tapered_aa_gbp
                        ni_supp_gbp = annual_ni_supp / 100.0
                        match_gbp = annual_emp_match / 100.0
                        breakdown = f"sacrifice £{sac_gbp:,.0f} + employer match £{match_gbp:,.0f}"
                        if ni_supp_gbp > 0:
                            breakdown += f" + NI supplement £{ni_supp_gbp:,.0f}"
                        context.warnings.append(schemas.ProjectionWarning(
                            date=context.month_start,
                            account_id=inc.account_id,
                            message=(
                                f"Pension AA: '{inc.name}' total contributions £{total_contrib_gbp:,.0f}/yr "
                                f"({breakdown}) exceed Annual Allowance of £{tapered_aa_gbp:,.0f}. "
                                f"Excess: £{excess_gbp:,.0f}. Consider carry-forward from prior years."
                            ),
                            source_type="income",
                            source_id=inc.id
                        ))
                    elif post_sac_gbp > 200_000:
                        # Taper applies but contributions are within the reduced AA
                        context.warnings.append(schemas.ProjectionWarning(
                            date=context.month_start,
                            account_id=inc.account_id,
                            message=(
                                f"Pension AA Taper: '{inc.name}' post-sacrifice income £{post_sac_gbp:,.0f} "
                                f"triggers high-earner taper. Effective Annual Allowance: £{tapered_aa_gbp:,.0f}."
                            ),
                            source_type="income",
                            source_id=inc.id
                        ))

                    # Personal Allowance recovery insight
                    if gross_gbp > 100_000:
                        if post_sac_gbp < 100_000:
                            pa_restored = min(12_570.0, (125_140.0 - post_sac_gbp) / 2.0)
                            saving = round(pa_restored * 0.40)
                            context.warnings.append(schemas.ProjectionWarning(
                                date=context.month_start,
                                account_id=inc.account_id,
                                message=(
                                    f"PA Restored: '{inc.name}' sacrifice brings income below £100k, "
                                    f"recovering full Personal Allowance (~£{saving:,}/yr saved vs no sacrifice)."
                                ),
                                source_type="income",
                                source_id=inc.id
                            ))
                        elif post_sac_gbp < 125_140:
                            pa_restored = min(12_570.0, (gross_gbp - post_sac_gbp) / 2.0)
                            saving = round(pa_restored * 0.40)
                            context.warnings.append(schemas.ProjectionWarning(
                                date=context.month_start,
                                account_id=inc.account_id,
                                message=(
                                    f"PA Partial: '{inc.name}' sacrifice recovers ~£{pa_restored:,.0f} of Personal Allowance "
                                    f"(~£{saving:,}/yr saved). Sacrifice more to escape the 60% zone entirely."
                                ),
                                source_type="income",
                                source_id=inc.id
                            ))

            else:
                context.ytd_earnings[inc.owner_id]['taxable'] += gross_input
                context.ytd_earnings[inc.owner_id]['ni'] += gross_input
                net_to_pay = gross_input

            target_account = next((acc for acc in context.all_accounts if acc.id == inc.account_id), None)
            final_credit = net_to_pay
            if target_account and inc.currency != target_account.currency:
                if inc.currency == enums.Currency.USD and target_account.currency == enums.Currency.GBP:
                    final_credit = round(net_to_pay / scenario.gbp_to_usd_rate)
                elif inc.currency == enums.Currency.GBP and target_account.currency == enums.Currency.USD:
                    final_credit = round(net_to_pay * scenario.gbp_to_usd_rate)

            headroom = get_contribution_headroom(context, inc.account_id, scenario.tax_limits)
            if headroom < final_credit:
                context.warnings.append(schemas.ProjectionWarning(
                    date=context.month_start,
                    account_id=inc.account_id,
                    message=f"Tax Limit: Income '{inc.name}' exceeds allowance.",
                    source_type="income",
                    source_id=inc.id
                ))

            context.account_balances[inc.account_id] += final_credit
            context.account_book_costs[inc.account_id] += final_credit
            context.flows[inc.account_id]["income"] += gross_input
            context.flows[inc.account_id]["tax"] += tax_deducted
            track_contribution(context, inc.account_id, final_credit)
