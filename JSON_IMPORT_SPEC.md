# JSON Import Specification

This document defines the comprehensive syntax and schema for a valid JSON document used to import a financial scenario into the system via the `POST /scenarios/import_new` endpoint.

## Overview
- **Endpoint**: `POST /scenarios/import_new`
- **Content-Type**: `application/json`
- **Validation**: Strict validation against the schema defined below.
- **Reference Resolution**: IDs provided in the JSON are **local references**. They are used only to map relationships within the file (e.g., linking a Cost to an Account) and are not preserved as database IDs. Use any unique integer for IDs within your JSON file.
- **Currency Values**: All monetary values are integers representing **Pence/Cents** (e.g., `10000` = £100.00).

---

## Schema Reference

### Root Object (Scenario)
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | | Name of the scenario. |
| `start_date` | Date | **Yes** | | ISO 8601 format (`YYYY-MM-DD`). |
| `description` | String | No | `null` | Optional description. |
| `gbp_to_usd_rate` | Float | No | `1.25` | Exchange rate used for conversions. |
| `owners` | List[Owner] | No | `[]` | List of scenario owners. |
| `accounts` | List[Account] | No | `[]` | List of financial accounts. |
| `costs` | List[Cost] | No | `[]` | List of expenses. |
| `transfers` | List[Transfer] | No | `[]` | List of recurring transfers. |
| `financial_events` | List[Event] | No | `[]` | One-off financial events. |
| `tax_limits` | List[TaxLimit] | No | `[]` | Custom tax allowance overrides. |
| `automation_rules` | List[Rule] | No | `[]` | Automation logic (sweeps, top-ups). |
| `decumulation_strategies` | List[Strategy] | No | `[]` | Decumulation settings. |
| `chart_annotations` | List[Annotation] | No | `[]` | Manual markers on the projection chart. |

---

### Owner
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | **Yes*** | | Local ID used for linking. |
| `name` | String | **Yes** | | Owner name. |
| `birth_date` | Date | No | `null` | `"YYYY-MM-DD"`. |
| `retirement_age` | Integer | No | `65` | Target retirement age. |
| `notes` | String | No | `null` | |
| `income_sources` | List[Income] | No | `[]` | Income streams for this owner. |

---

### Income Source (Nested in Owner)
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | | Name of income source (e.g. "Salary"). |
| `net_value` | Integer | **Yes** | | **Amount in Pence**. |
| `cadence` | Enum | **Yes** | | `"monthly"`, `"annually"`, `"quarterly"`, `"weekly"`. |
| `start_date` | Date | **Yes** | | Start date. |
| `end_date` | Date | No | `null` | End date (optional). |
| `currency` | Enum | No | `"GBP"` | `"GBP"`, `"USD"`, `"EUR"`. |
| `growth_rate` | Float | No | `0.0` | Annual growth rate % (e.g. `2.5`). |
| `is_pre_tax` | Boolean | No | `False` | If `True`, treated as Gross income (tax calculated). If `False`, treated as Net. |
| `salary_sacrifice_value` | Integer | No | `0` | **Pence**. Pre-tax deduction into pension using Salary Sacrifice. |
| `taxable_benefit_value` | Integer | No | `0` | **Pence**. Taxable Benefit in Kind (e.g. Car, Medical). |
| `employer_pension_contribution`| Integer | No | `0` | **Pence**. Employer's contribution to pension. |
| `account_id` | Integer | No | `null` | Ref ID of standard target Account. |
| `salary_sacrifice_account_id` | Integer | No | `null` | Ref ID of Pension Account for salary sacrifice checks. |
| `notes` | String | No | `null` | |

---

### Account
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `id` | Integer | **Yes*** | | Local ID for linking. |
| `name` | String | **Yes** | | Account name. |
| `account_type` | Enum | **Yes** | | `Cash`, `Investment`, `Pension`, `Mortgage`, `Property`, `Loan`, `Main Residence`, `RSU Grant`. |
| `tax_wrapper` | Enum | No | `"None"` | `None`, `ISA`, `Pension`, `General Investment Account`, `Lifetime ISA`, `Junior ISA`. |
| `starting_balance` | Integer | **Yes** | | **Pence**. Negative for liabilities/mortgages. |
| `min_balance` | Integer | No | `null` | **Pence**. Minimum buffer. |
| `interest_rate` | Float | No | `0.0` | Annual interest/growth rate %. |
| `book_cost` | Integer | No | `null` | **Pence**. Original purchase cost (for Capital Gains). |
| `currency` | Enum | No | `"GBP"` | |
| `notes` | String | No | `null` | |
| `owners` | List[Int] | No | `[]` | List of Owner Ref IDs. |

#### Specific: Mortgage / Liability
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `original_loan_amount` | Integer | No | `null` | **Pence**. Original principal. |
| `mortgage_start_date` | Date | No | `null` | |
| `amortisation_period_years` | Integer | No | `null` | Total term length. |
| `fixed_interest_rate` | Float | No | `null` | Fixed rate %. |
| `fixed_rate_period_years` | Integer | No | `null` | Duration of fixed rate. |
| `payment_from_account_id` | Integer | No | `null` | Ref ID of account paying the mortgage. |
| `is_primary_account` | Boolean | No | `False` | For multi-currency logic simplifications. |

#### Specific: RSU Grant
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `grant_date` | Date | No | `null` | |
| `unit_price` | Integer | No | `null` | **Pence**. Grant price per unit. |
| `vesting_cadence` | String | No | `"monthly"`| Frequency of vesting events. |
| `rsu_target_account_id` | Integer | No | `null` | Ref ID of Investment account where vested shares go. |
| `vesting_schedule` | List[Obj]| No | `null` | E.g. `[{"year": 1, "percent": 25}, ...]`. |

---

### Cost
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | | Cost name. |
| `value` | Integer | **Yes** | | **Pence**. |
| `account_id` | Integer | **Yes** | | Ref ID of valid Account. |
| `cadence` | Enum | **Yes** | | `"monthly"`, `"annually"`, etc. |
| `start_date` | Date | **Yes** | | |
| `end_date` | Date | No | `null` | |
| `is_recurring` | Boolean | No | `True` | |
| `growth_rate` | Float | No | `0.0` | Inflation/growth %. |
| `currency` | Enum | No | `"GBP"` | |
| `notes` | String | No | `null` | |

---

### Transfer
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | | |
| `from_account_id` | Integer | **Yes** | | Ref ID. |
| `to_account_id` | Integer | **Yes** | | Ref ID. |
| `value` | Integer | **Yes** | | **Pence**. |
| `cadence` | Enum | **Yes** | | |
| `start_date` | Date | **Yes** | | |
| `end_date` | Date | No | `null` | |
| `currency` | Enum | No | `"GBP"` | |
| `show_on_chart` | Boolean | No | `False` | |
| `notes` | String | No | `null` | |

---

### Financial Event
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | | |
| `value` | Integer | **Yes** | | **Pence**. Positive (Inflow) or Negative (Outflow). |
| `event_date` | Date | **Yes** | | |
| `event_type` | String | **Yes** | | `"income_expense"`, `"transfer"`. |
| `from_account_id` | Integer | No | `null` | Ref ID (if transfer/outflow). |
| `to_account_id` | Integer | No | `null` | Ref ID (if transfer/inflow). |
| `currency` | Enum | No | `"GBP"` | |
| `show_on_chart` | Boolean | No | `False` | |
| `notes` | String | No | `null` | |

---

### Automation Rule
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | | |
| `rule_type` | String | **Yes** | | `"sweep"`, `"top_up"`, `"transfer"`, `"mortgage_smart"`. |
| `source_account_id` | Integer | **Yes** | | Ref ID. |
| `target_account_id` | Integer | No | `null` | Ref ID (Required for most types). |
| `trigger_value` | Integer | **Yes** | | **Pence**. Threshold to trigger rule. |
| `transfer_value` | Integer | No | `null` | **Pence**. Fixed amount (if not sweep). |
| `transfer_cap` | Integer | No | `null` | **Pence**. Max transfer per execution. |
| `cadence` | String | No | `"monthly"`| |
| `start_date` | Date | No | `null` | |
| `end_date` | Date | No | `null` | |
| `priority` | Integer | No | `0` | Higher runs later (overrides lower). |
| `notes` | String | No | `null` | |

---

### Tax Limit
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | | |
| `amount` | Integer | **Yes** | | **Pence**. Limit amount. |
| `wrappers` | List[Str] | **Yes** | | E.g. `["ISA", "Lifetime ISA"]`. |
| `account_types` | List[Str]| No | `null` | Filter by account type. |
| `start_date` | Date | **Yes** | | |
| `end_date` | Date | No | `null` | |
| `frequency` | String | No | `"Annually"` | |

---

### Decumulation Strategy
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `name` | String | **Yes** | | |
| `strategy_type` | String | No | `"Standard"` | |
| `enabled` | Boolean | No | `True` | |
| `start_date` | Date | No | `null` | |
| `end_date` | Date | No | `null` | |

---

### Chart Annotation
| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `date` | Date | **Yes** | | |
| `label` | String | **Yes** | | Text label. |
| `annotation_type` | String | No | `"manual"` | |

