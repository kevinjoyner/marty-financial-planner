from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Boolean, JSON, Enum as SQLEnum
from sqlalchemy.orm import relationship
from .database import Base
from . import enums

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    start_date = Column(Date)
    gbp_to_usd_rate = Column(Float, default=1.25)
    notes = Column(String, nullable=True)
    
    owners = relationship("Owner", back_populates="scenario", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="scenario", cascade="all, delete-orphan")
    costs = relationship("Cost", back_populates="scenario", cascade="all, delete-orphan")
    transfers = relationship("Transfer", back_populates="scenario", cascade="all, delete-orphan")
    financial_events = relationship("FinancialEvent", back_populates="scenario", cascade="all, delete-orphan")
    tax_limits = relationship("TaxLimit", back_populates="scenario", cascade="all, delete-orphan")
    automation_rules = relationship("AutomationRule", back_populates="scenario", cascade="all, delete-orphan")
    chart_annotations = relationship("ChartAnnotation", back_populates="scenario", cascade="all, delete-orphan")
    history = relationship("ScenarioHistory", back_populates="scenario", cascade="all, delete-orphan")

class Owner(Base):
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    birth_date = Column(Date, nullable=True)
    retirement_age = Column(Integer, default=65)
    notes = Column(String, nullable=True)
    
    scenario = relationship("Scenario", back_populates="owners")
    income_sources = relationship("IncomeSource", back_populates="owner", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    notes = Column(String, nullable=True)
    account_type = Column(SQLEnum(enums.AccountType))
    tax_wrapper = Column(SQLEnum(enums.TaxWrapper), default=enums.TaxWrapper.NONE)
    starting_balance = Column(Integer) # Pence
    interest_rate = Column(Float, default=0.0)
    currency = Column(SQLEnum(enums.Currency), default=enums.Currency.GBP)
    
    book_cost = Column(Integer, nullable=True)
    min_balance = Column(Integer, default=0)
    
    original_loan_amount = Column(Integer, nullable=True)
    mortgage_start_date = Column(Date, nullable=True)
    amortisation_period_years = Column(Integer, nullable=True)
    fixed_interest_rate = Column(Float, nullable=True)
    fixed_rate_period_years = Column(Integer, nullable=True)
    payment_from_account_id = Column(Integer, nullable=True)
    
    grant_date = Column(Date, nullable=True)
    vesting_schedule = Column(JSON, nullable=True)
    unit_price = Column(Float, nullable=True)
    rsu_target_account_id = Column(Integer, nullable=True)
    is_primary_account = Column(Boolean, default=False)

    scenario = relationship("Scenario", back_populates="accounts")
    owners = relationship("Owner", secondary="account_owners", backref="accounts")

from sqlalchemy import Table
account_owners = Table('account_owners', Base.metadata,
    Column('account_id', Integer, ForeignKey('accounts.id')),
    Column('owner_id', Integer, ForeignKey('owners.id'))
)

class IncomeSource(Base):
    __tablename__ = "income_sources"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"))
    name = Column(String)
    notes = Column(String, nullable=True)
    net_value = Column(Integer) 
    cadence = Column(SQLEnum(enums.Cadence))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    growth_rate = Column(Float, default=0.0)
    currency = Column(SQLEnum(enums.Currency), default=enums.Currency.GBP)
    account_id = Column(Integer, nullable=True)
    is_pre_tax = Column(Boolean, default=False)
    salary_sacrifice_value = Column(Integer, default=0)
    salary_sacrifice_account_id = Column(Integer, nullable=True)
    taxable_benefit_value = Column(Integer, default=0)
    employer_pension_contribution = Column(Integer, default=0)
    owner = relationship("Owner", back_populates="income_sources")

class Cost(Base):
    __tablename__ = "costs"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    notes = Column(String, nullable=True)
    value = Column(Integer) 
    cadence = Column(SQLEnum(enums.Cadence))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    growth_rate = Column(Float, default=0.0)
    currency = Column(SQLEnum(enums.Currency), default=enums.Currency.GBP)
    account_id = Column(Integer)
    is_recurring = Column(Boolean, default=True)
    scenario = relationship("Scenario", back_populates="costs")

class Transfer(Base):
    __tablename__ = "transfers"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    notes = Column(String, nullable=True)
    value = Column(Integer) 
    cadence = Column(SQLEnum(enums.Cadence))
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    currency = Column(SQLEnum(enums.Currency), default=enums.Currency.GBP)
    from_account_id = Column(Integer)
    to_account_id = Column(Integer)
    show_on_chart = Column(Boolean, default=False)
    scenario = relationship("Scenario", back_populates="transfers")

class FinancialEvent(Base):
    __tablename__ = "financial_events"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    notes = Column(String, nullable=True)
    event_date = Column(Date)
    event_type = Column(SQLEnum(enums.FinancialEventType))
    value = Column(Integer) 
    from_account_id = Column(Integer, nullable=True)
    to_account_id = Column(Integer, nullable=True)
    currency = Column(SQLEnum(enums.Currency), default=enums.Currency.GBP)
    show_on_chart = Column(Boolean, default=False)
    scenario = relationship("Scenario", back_populates="financial_events")

class TaxLimit(Base):
    __tablename__ = "tax_limits"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    amount = Column(Integer) 
    wrappers = Column(JSON) 
    frequency = Column(String, default="Annually")
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    account_types = Column(JSON, nullable=True)
    scenario = relationship("Scenario", back_populates="tax_limits")

class AutomationRule(Base):
    __tablename__ = "automation_rules"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    notes = Column(String, nullable=True)
    rule_type = Column(SQLEnum(enums.RuleType))
    source_account_id = Column(Integer)
    target_account_id = Column(Integer, nullable=True)
    trigger_value = Column(Integer) 
    transfer_value = Column(Float, nullable=True) 
    transfer_cap = Column(Integer, nullable=True)
    cadence = Column(SQLEnum(enums.Cadence), default=enums.Cadence.MONTHLY)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    priority = Column(Integer, default=0)
    scenario = relationship("Scenario", back_populates="automation_rules")

class ChartAnnotation(Base):
    __tablename__ = "chart_annotations"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"))
    date = Column(Date)
    label = Column(String)
    annotation_type = Column(String, default="manual")
    scenario = relationship("Scenario", back_populates="chart_annotations")

class ScenarioHistory(Base):
    __tablename__ = "scenario_history"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id", ondelete="CASCADE"))
    timestamp = Column(Date)
    action_description = Column(String)
    snapshot_data = Column(JSON)
    scenario = relationship("Scenario", back_populates="history")
