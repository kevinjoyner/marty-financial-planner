from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey, JSON
from sqlalchemy.orm import relationship
from .database import Base

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    
    name = Column(String, index=True)
    notes = Column(String, nullable=True) # Added missing field
    account_type = Column(String) 
    tax_wrapper = Column(String, default="None") 
    
    currency = Column(String, default="GBP")
    starting_balance = Column(Integer) 
    min_balance = Column(Integer, nullable=True) 
    interest_rate = Column(Float, default=0.0) 
    book_cost = Column(Integer, nullable=True) 
    
    # Mortgage
    original_loan_amount = Column(Integer, nullable=True)
    mortgage_start_date = Column(Date, nullable=True)
    amortisation_period_years = Column(Integer, nullable=True)
    fixed_interest_rate = Column(Float, nullable=True)
    fixed_rate_period_years = Column(Integer, nullable=True)
    payment_from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    is_primary_account = Column(Boolean, default=False)
    
    # RSU
    grant_date = Column(Date, nullable=True)
    vesting_schedule = Column(JSON, nullable=True)
    vesting_cadence = Column(String, default="monthly", nullable=True)
    unit_price = Column(Integer, nullable=True) 
    rsu_target_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)

    owners = relationship("Owner", secondary="account_owners", back_populates="accounts")

class Owner(Base):
    __tablename__ = "owners"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String, index=True)
    birth_date = Column(Date, nullable=True)
    retirement_age = Column(Integer, default=65)
    notes = Column(String, nullable=True)
    
    income_sources = relationship("IncomeSource", back_populates="owner", cascade="all, delete-orphan")
    accounts = relationship("Account", secondary="account_owners", back_populates="owners")

class AccountOwner(Base):
    __tablename__ = "account_owners"
    account_id = Column(Integer, ForeignKey("accounts.id"), primary_key=True)
    owner_id = Column(Integer, ForeignKey("owners.id"), primary_key=True)

class IncomeSource(Base):
    __tablename__ = "income_sources"
    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("owners.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    salary_sacrifice_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    
    name = Column(String)
    amount = Column(Integer, nullable=True)
    net_value = Column(Integer)
    cadence = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    currency = Column(String, default="GBP")
    growth_rate = Column(Float, default=0.0)
    
    is_pre_tax = Column(Boolean, default=False)
    salary_sacrifice_value = Column(Integer, default=0)
    taxable_benefit_value = Column(Integer, default=0)
    employer_pension_contribution = Column(Integer, default=0)
    notes = Column(String, nullable=True)
    
    owner = relationship("Owner", back_populates="income_sources")

class Cost(Base):
    __tablename__ = "costs"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    account_id = Column(Integer, ForeignKey("accounts.id"))
    
    name = Column(String)
    value = Column(Integer)
    cadence = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    currency = Column(String, default="GBP")
    growth_rate = Column(Float, default=0.0)
    is_recurring = Column(Boolean, default=True)
    notes = Column(String, nullable=True)

class Transfer(Base):
    __tablename__ = "transfers"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    from_account_id = Column(Integer, ForeignKey("accounts.id"))
    to_account_id = Column(Integer, ForeignKey("accounts.id"))
    
    name = Column(String)
    value = Column(Integer)
    cadence = Column(String)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    currency = Column(String, default="GBP")
    show_on_chart = Column(Boolean, default=False)
    notes = Column(String, nullable=True)

class FinancialEvent(Base):
    __tablename__ = "financial_events"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    from_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    to_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    
    name = Column(String)
    value = Column(Integer)
    event_date = Column(Date)
    event_type = Column(String)
    currency = Column(String, default="GBP")
    show_on_chart = Column(Boolean, default=False)
    notes = Column(String, nullable=True)

class TaxLimit(Base):
    __tablename__ = "tax_limits"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    amount = Column(Integer)
    wrappers = Column(JSON)
    account_types = Column(JSON, nullable=True)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    frequency = Column(String, default="Annually")

class DecumulationStrategy(Base):
    __tablename__ = "decumulation_strategies"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    strategy_type = Column(String, default="Standard")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    enabled = Column(Boolean, default=True)

class ChartAnnotation(Base):
    __tablename__ = "chart_annotations"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    date = Column(Date)
    label = Column(String)
    annotation_type = Column(String, default="manual")

class AutomationRule(Base):
    __tablename__ = "automation_rules"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    name = Column(String)
    rule_type = Column(String)
    source_account_id = Column(Integer, ForeignKey("accounts.id"))
    target_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True)
    
    trigger_value = Column(Integer)
    transfer_value = Column(Integer, nullable=True)
    transfer_cap = Column(Integer, nullable=True)
    
    cadence = Column(String, default="monthly")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    priority = Column(Integer, default=0)
    notes = Column(String, nullable=True)

class Scenario(Base):
    __tablename__ = "scenarios"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String, nullable=True)
    start_date = Column(Date)
    gbp_to_usd_rate = Column(Float, default=1.25)
    notes = Column(String, nullable=True)
    
    owners = relationship("Owner", backref="scenario", cascade="all, delete-orphan")
    accounts = relationship("Account", backref="scenario", cascade="all, delete-orphan")
    costs = relationship("Cost", backref="scenario", cascade="all, delete-orphan")
    transfers = relationship("Transfer", backref="scenario", cascade="all, delete-orphan")
    financial_events = relationship("FinancialEvent", backref="scenario", cascade="all, delete-orphan")
    tax_limits = relationship("TaxLimit", backref="scenario", cascade="all, delete-orphan")
    decumulation_strategies = relationship("DecumulationStrategy", backref="scenario", cascade="all, delete-orphan")
    chart_annotations = relationship("ChartAnnotation", backref="scenario", cascade="all, delete-orphan")
    automation_rules = relationship("AutomationRule", backref="scenario", cascade="all, delete-orphan")

class ScenarioHistory(Base):
    __tablename__ = "scenario_history"
    id = Column(Integer, primary_key=True, index=True)
    scenario_id = Column(Integer, ForeignKey("scenarios.id"))
    action_description = Column(String)
    snapshot_data = Column(JSON)
    timestamp = Column(Date)
