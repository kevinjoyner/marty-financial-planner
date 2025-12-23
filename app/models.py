from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, Boolean, JSON, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.enums import AccountType, Currency, TaxWrapper, Cadence, RuleType

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    start_date = Column(Date)
    gbp_to_usd_rate = Column(Float, default=1.25)
    
    owners = relationship("Owner", back_populates="scenario", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="scenario", cascade="all, delete-orphan")
    costs = relationship("Cost", back_populates="scenario", cascade="all, delete-orphan")
    transfers = relationship("Transfer", back_populates="scenario", cascade="all, delete-orphan")
    financial_events = relationship("FinancialEvent", back_populates="scenario", cascade="all, delete-orphan")
    tax_limits = relationship("TaxLimit", back_populates="scenario", cascade="all, delete-orphan")
    automation_rules = relationship("AutomationRule", back_populates="scenario", cascade="all, delete-orphan")
    chart_annotations = relationship("ChartAnnotation", back_populates="scenario", cascade="all, delete-orphan")
    decumulation_strategies = relationship("DecumulationStrategy", back_populates="scenario", cascade="all, delete-orphan")
    history_logs = relationship("ScenarioHistory", back_populates="scenario", cascade="all, delete-orphan")

class Owner(Base):
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    notes = Column(Text, nullable=True)
    birth_date = Column(Date, nullable=True)
    retirement_age = Column(Integer, nullable=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    
    scenario = relationship("Scenario", back_populates="owners")
    accounts = relationship("Account", secondary="account_owners", back_populates="owners")
    income_sources = relationship("IncomeSource", back_populates="owner", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    notes = Column(Text, nullable=True)
    account_type = Column(Enum(AccountType))
    tax_wrapper = Column(Enum(TaxWrapper), nullable=True)
    starting_balance = Column(Integer)
    currency = Column(Enum(Currency), default=Currency.GBP)
    interest_rate = Column(Float, default=0.0)
    min_balance = Column(Integer, default=0)
    book_cost = Column(Integer, nullable=True) 
    original_loan_amount = Column(Integer, nullable=True)
    amortisation_period_years = Column(Integer, nullable=True)
    mortgage_start_date = Column(Date, nullable=True)
    fixed_rate_period_years = Column(Integer, nullable=True)
    fixed_interest_rate = Column(Float, nullable=True)
    payment_from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    rsu_target_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    vesting_schedule = Column(JSON, nullable=True)
    grant_date = Column(Date, nullable=True)
    unit_price = Column(Integer, nullable=True)
    vesting_cadence = Column(String, default='monthly', nullable=True)
    is_primary_account = Column(Boolean, default=False)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    scenario = relationship("Scenario", back_populates="accounts")
    owners = relationship("Owner", secondary="account_owners", back_populates="accounts")

class AccountOwner(Base):
    __tablename__ = "account_owners"
    account_id = Column(Integer, ForeignKey("accounts.id"), primary_key=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), primary_key=True)

class IncomeSource(Base):
    __tablename__ = "income_sources"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    net_value = Column(Integer)
    cadence = Column(Enum(Cadence))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    growth_rate = Column(Float, default=0.0)
    
    # Currency Added
    currency = Column(Enum(Currency), default=Currency.GBP)
    
    is_pre_tax = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("owners.id"))
    owner = relationship("Owner", back_populates="income_sources")
    account_id = Column(Integer, ForeignKey("accounts.id"))
    salary_sacrifice_value = Column(Integer, default=0)
    salary_sacrifice_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    employer_pension_contribution = Column(Integer, default=0)
    taxable_benefit_value = Column(Integer, default=0)

class Cost(Base):
    __tablename__ = "costs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    value = Column(Integer)
    cadence = Column(Enum(Cadence))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    inflation_rate = Column(Float, default=0.0)
    is_recurring = Column(Boolean, default=True)
    currency = Column(Enum(Currency), default=Currency.GBP)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    scenario = relationship("Scenario", back_populates="costs")
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

class Transfer(Base):
    __tablename__ = "transfers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    value = Column(Integer)
    cadence = Column(Enum(Cadence))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    currency = Column(Enum(Currency), default=Currency.GBP)
    show_on_chart = Column(Boolean, default=False)
    from_account_id = Column(Integer, ForeignKey("accounts.id"))
    to_account_id = Column(Integer, ForeignKey("accounts.id"))
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    scenario = relationship("Scenario", back_populates="transfers")

class FinancialEvent(Base):
    __tablename__ = "financial_events"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    date = Column(Date)
    value = Column(Integer)
    type = Column(String)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    scenario = relationship("Scenario", back_populates="financial_events")
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

class AutomationRule(Base):
    __tablename__ = "automation_rules"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    notes = Column(Text, nullable=True)
    priority = Column(Integer, default=0)
    rule_type = Column(Enum(RuleType))
    source_account_id = Column(Integer, ForeignKey("accounts.id"))
    target_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    trigger_value = Column(Integer)
    transfer_value = Column(Integer, nullable=True)
    transfer_cap = Column(Integer, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    cadence = Column(Enum(Cadence), default=Cadence.MONTHLY)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    scenario = relationship("Scenario", back_populates="automation_rules")

class TaxLimit(Base):
    __tablename__ = "tax_limits"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    amount = Column(Integer)
    wrappers = Column(JSON)
    account_types = Column(JSON, nullable=True)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    frequency = Column(String, default="Annually")
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    scenario = relationship("Scenario", back_populates="tax_limits")

class ChartAnnotation(Base):
    __tablename__ = "chart_annotations"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date)
    label = Column(String)
    annotation_type = Column(String, default='info')
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    scenario = relationship("Scenario", back_populates="chart_annotations")

class DecumulationStrategy(Base):
    __tablename__ = "decumulation_strategies"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    strategy_type = Column(String)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    enabled = Column(Boolean, default=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    scenario = relationship("Scenario", back_populates="decumulation_strategies")

class ScenarioHistory(Base):
    __tablename__ = "scenario_history"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    timestamp = Column(DateTime)
    action_description = Column(String)
    snapshot_data = Column(JSON)
    scenario = relationship("Scenario", back_populates="history_logs")
