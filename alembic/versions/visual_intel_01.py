"""Visual Intelligence Schema

Revision ID: visual_intel_01
Revises: 8fe4dcd0cc61
Create Date: 2025-12-15 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'visual_intel_01'
down_revision: Union[str, None] = '8fe4dcd0cc61'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add show_on_chart to financial_events and transfers
    with op.batch_alter_table('financial_events', schema=None) as batch_op:
        batch_op.add_column(sa.Column('show_on_chart', sa.Boolean(), server_default='0', nullable=True))
    
    with op.batch_alter_table('transfers', schema=None) as batch_op:
        batch_op.add_column(sa.Column('show_on_chart', sa.Boolean(), server_default='0', nullable=True))

    # Create ChartAnnotations table
    op.create_table('chart_annotations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scenario_id', sa.Integer(), nullable=True),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('label', sa.String(), nullable=True),
        sa.Column('annotation_type', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['scenario_id'], ['scenarios.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('chart_annotations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_chart_annotations_id'), ['id'], unique=False)

def downgrade() -> None:
    with op.batch_alter_table('financial_events', schema=None) as batch_op:
        batch_op.drop_column('show_on_chart')
    
    with op.batch_alter_table('transfers', schema=None) as batch_op:
        batch_op.drop_column('show_on_chart')
    
    op.drop_table('chart_annotations')
