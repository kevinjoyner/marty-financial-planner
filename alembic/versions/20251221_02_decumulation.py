"""add decumulation

Revision ID: 20251221_02_decumulation
Revises: 20251221_01_baseline
Create Date: 2025-12-21 17:05:02

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = '20251221_02_decumulation'
down_revision = '20251221_01_baseline'
branch_labels = None
depends_on = None

def upgrade():
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)
    tables = inspector.get_table_names()

    # 1. Create the table if missing
    if 'decumulation_strategies' not in tables:
        op.create_table('decumulation_strategies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('scenario_id', sa.Integer(), nullable=True),
            sa.Column('name', sa.String(), nullable=True),
            sa.Column('strategy_type', sa.String(), nullable=True),
            sa.Column('start_date', sa.Date(), nullable=True),
            sa.Column('end_date', sa.Date(), nullable=True),
            # Add enabled directly if creating fresh
            sa.Column('enabled', sa.Boolean(), server_default='1', nullable=True),
            sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id')
        )
    else:
        # 2. If table exists, ensure 'enabled' column exists (Safety check)
        columns = [c['name'] for c in inspector.get_columns('decumulation_strategies')]
        if 'enabled' not in columns:
            op.add_column('decumulation_strategies', sa.Column('enabled', sa.Boolean(), server_default='1', nullable=True))

def downgrade():
    # Drop table
    op.drop_table('decumulation_strategies')
