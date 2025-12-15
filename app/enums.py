import enum

class AccountType(str, enum.Enum):
    CASH = "Cash"
    INVESTMENT = "Investment"
    PENSION = "Pension"
    PROPERTY = "Property"
    MORTGAGE = "Mortgage"
    LOAN = "Loan"
    RSU_GRANT = "RSU Grant"

class TaxWrapper(str, enum.Enum):
    NONE = "None"
    ISA = "ISA"
    LISA = "Lifetime ISA"
    PENSION = "Pension"
    GIA = "GIA"

class Currency(str, enum.Enum):
    GBP = "GBP"
    USD = "USD"
    EUR = "EUR"

class Cadence(str, enum.Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"
    ONCE = "once"

class FinancialEventType(str, enum.Enum):
    INCOME_EXPENSE = "income_expense"
    TRANSFER = "transfer"

class RuleType(str, enum.Enum):
    SWEEP = "sweep"
    TOP_UP = "top_up"
    SMART_TRANSFER = "transfer"
    MORTGAGE_SMART = "mortgage_smart"
