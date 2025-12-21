"""baseline schema

Revision ID: 20251221_01_baseline
Revises: 
Create Date: 2025-12-21 17:05:02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '20251221_01_baseline'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # --- SCENARIOS ---
    if 'scenarios' not in tables:
        op.create_table('scenarios',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('description', sa.String(), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('gbp_to_usd_rate', sa.Float(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )

    # --- OWNERS ---
    if 'owners' not in tables:
        op.create_table('owners',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('birth_date', sa.Date(), nullable=True),
            sa.Column('retirement_age', sa.Integer(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # --- ACCOUNTS ---
    if 'accounts' not in tables:
        op.create_table('accounts',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('account_type', sa.Enum('CASH', 'INVESTMENT', 'PENSION', 'PROPERTY', 'MORTGAGE', 'LOAN', 'RSU_GRANT', 'CRYPTO', 'OTHER', name='accounttype'), nullable=True),
            sa.Column('tax_wrapper', sa.Enum('NONE', 'ISA', 'LISA', 'PENSION', 'GIA', 'OFFSHORE_BOND', 'VCT', 'EIS', 'OTHER', name='taxwrapper'), nullable=True),
            sa.Column('starting_balance', sa.Integer(), nullable=True),
            sa.Column('interest_rate', sa.Float(), nullable=True),
            sa.Column('currency', sa.Enum('GBP', 'USD', 'EUR', name='currency'), nullable=True),
            sa.Column('book_cost', sa.Integer(), nullable=True),
            sa.Column('min_balance', sa.Integer(), nullable=True),
            sa.Column('original_loan_amount', sa.Integer(), nullable=True),
            sa.Column('mortgage_start_date', sa.Date(), nullable=True),
            sa.Column('amortisation_period_years', sa.Integer(), nullable=True),
            sa.Column('fixed_interest_rate', sa.Float(), nullable=True),
            sa.Column('fixed_rate_period_years', sa.Integer(), nullable=True),
            sa.Column('payment_from_account_id', sa.Integer(), nullable=True),
            sa.Column('grant_date', sa.Date(), nullable=True),
            sa.Column('vesting_schedule', sa.JSON(), nullable=True),
            sa.Column('unit_price', sa.Float(), nullable=True),
            sa.Column('rsu_target_account_id', sa.Integer(), nullable=True),
            sa.Column('is_primary_account', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # --- INCOME SOURCES ---
    if 'income_sources' not in tables:
        op.create_table('income_sources',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('net_value', sa.Integer(), nullable=True),
            sa.Column('cadence', sa.Enum('MONTHLY', 'ANNUALLY', 'ONCE', name='cadence'), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('growth_rate', sa.Float(), nullable=True),
            sa.Column('currency', sa.Enum('GBP', 'USD', 'EUR', name='currency'), nullable=True),
            sa.Column('account_id', sa.Integer(), nullable=True),
            sa.Column('is_pre_tax', sa.Boolean(), nullable=True),
            sa.Column('salary_sacrifice_value', sa.Integer(), nullable=True),
            sa.Column('salary_sacrifice_account_id', sa.Integer(), nullable=True),
            sa.Column('taxable_benefit_value', sa.Integer(), nullable=True),
            sa.Column('employer_pension_contribution', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['owner_id'], ['owners.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # --- COSTS ---
    if 'costs' not in tables:
        op.create_table('costs',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('value', sa.Integer(), nullable=True),
            sa.Column('cadence', sa.Enum('MONTHLY', 'ANNUALLY', 'ONCE', name='cadence'), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('growth_rate', sa.Float(), nullable=True),
            sa.Column('currency', sa.Enum('GBP', 'USD', 'EUR', name='currency'), nullable=True),
            sa.Column('account_id', sa.Integer(), nullable=True),
            sa.Column('is_recurring', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # --- TRANSFERS ---
    if 'transfers' not in tables:
        op.create_table('transfers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('value', sa.Integer(), nullable=True),
            sa.Column('cadence', sa.Enum('MONTHLY', 'ANNUALLY', 'ONCE', name='cadence'), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('currency', sa.Enum('GBP', 'USD', 'EUR', name='currency'), nullable=True),
            sa.Column('from_account_id', sa.Integer(), nullable=True),
            sa.Column('to_account_id', sa.Integer(), nullable=True),
            sa.Column('show_on_chart', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # --- FINANCIAL EVENTS ---
    if 'financial_events' not in tables:
        op.create_table('financial_events',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('event_date', sa.Date(), nullable=True),
            sa.Column('event_type', sa.Enum('INCOME_EXPENSE', 'ASSET_PURCHASE', 'ASSET_SALE', 'LIABILITY_NEW', 'LIABILITY_PAYOFF', name='financialeventtype'), nullable=True),
            sa.Column('value', sa.Integer(), nullable=True),
            sa.Column('from_account_id', sa.Integer(), nullable=True),
            sa.Column('to_account_id', sa.Integer(), nullable=True),
            sa.Column('currency', sa.Enum('GBP', 'USD', 'EUR', name='currency'), nullable=True),
            sa.Column('show_on_chart', sa.Boolean(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # --- AUTOMATION RULES ---
    if 'automation_rules' not in tables:
        op.create_table('automation_rules',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('notes', sa.String(), nullable=True),
            sa.Column('rule_type', sa.Enum('SWEEP', 'TOP_UP', 'SMART_TRANSFER', 'MORTGAGE_SMART', name='ruletype'), nullable=True),
            sa.Column('source_account_id', sa.Integer(), nullable=True),
            sa.Column('target_account_id', sa.Integer(), nullable=True),
            sa.Column('trigger_value', sa.Integer(), nullable=True),
            sa.Column('transfer_value', sa.Float(), nullable=True),
            sa.Column('transfer_cap', sa.Integer(), nullable=True),
            sa.Column('cadence', sa.Enum('MONTHLY', 'ANNUALLY', 'ONCE', name='cadence'), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('priority', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # --- TAX LIMITS ---
    if 'tax_limits' not in tables:
        op.create_table('tax_limits',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('amount', sa.Integer(), nullable=True),
            sa.Column('wrappers', sa.JSON(), nullable=True),
            sa.Column('frequency', sa.String(), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            sa.Column('account_types', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # --- CHART ANNOTATIONS ---
    if 'chart_annotations' not in tables:
        op.create_table('chart_annotations',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('date', sa.Date(), nullable=True),
            sa.Column('label', sa.String(), nullable=True),
            sa.Column('annotation_type', sa.String(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )

    # --- HISTORY ---
    if 'scenario_history' not in tables:
        op.create_table('scenario_history',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('timestamp', sa.Date(), nullable=True),
            sa.Column('action_description', sa.String(), nullable=True),
            sa.Column('snapshot_data', sa.JSON(), nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
        
    # --- M2M TABLE ---
    if 'account_owners' not in tables:
        op.create_table('account_owners',
            sa.Column('account_id', sa.Integer(), nullable=True),
            sa.Column('owner_id', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['account_id'], ['accounts.id'], ),
            sa.ForeignKeyConstraint(['owner_id'], ['owners.id'], )
        )

def downgrade():
    # Only drop if they exist (Reverse order)
    op.drop_table('account_owners')
    op.drop_table('scenario_history')
    op.drop_table('chart_annotations')
    op.drop_table('tax_limits')
    op.drop_table('automation_rules')
    op.drop_table('financial_events')
    op.drop_table('transfers')
    op.drop_table('costs')
    op.drop_table('income_sources')
    op.drop_table('accounts')
    op.drop_table('owners')
    op.drop_table('scenarios')
