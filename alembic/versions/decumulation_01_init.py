"""Add Decumulation Strategies Table

Revision ID: decumulation_01_init
Revises: visual_intel_01
Create Date: 2025-12-22 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'decumulation_01_init'
down_revision = 'visual_intel_01'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('decumulation_strategies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('strategy_type', sa.String(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('enabled', sa.Boolean(), server_default='1', nullable=True),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('decumulation_strategies', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_decumulation_strategies_id'), ['id'], unique=False)

def downgrade():
    op.drop_table('decumulation_strategies')
