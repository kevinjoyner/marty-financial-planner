"""add decumulation

Revision ID: 202512211746
Revises: visual_intel_01
Create Date: 2025-12-21 17:46:39

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = '202512211746'
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

def downgrade():
    op.drop_table('decumulation_strategies')
