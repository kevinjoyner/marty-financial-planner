"""Add pension contribution percent fields to income_sources

Revision ID: d4e5f6a7b8c9
Revises: b2c3d4e5f6a7
Create Date: 2026-04-06 13:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('income_sources', sa.Column('salary_sacrifice_percent', sa.Float(), nullable=True))
    op.add_column('income_sources', sa.Column('employer_match_percent', sa.Float(), nullable=True))
    op.add_column('income_sources', sa.Column('employer_ni_supplement', sa.Boolean(), nullable=False, server_default=sa.false()))
    op.add_column('income_sources', sa.Column('employer_ni_rate', sa.Float(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('income_sources', schema=None) as batch_op:
        batch_op.drop_column('employer_ni_rate')
        batch_op.drop_column('employer_ni_supplement')
        batch_op.drop_column('employer_match_percent')
        batch_op.drop_column('salary_sacrifice_percent')
