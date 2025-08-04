"""add_response_delay_ms_to_log_entries

Revision ID: a59e30267261
Revises: ca28fcc5c3c4
Create Date: 2025-07-31 19:54:05.317080

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a59e30267261'
down_revision: Union[str, None] = 'ca28fcc5c3c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add response_delay_ms column to log_entries table
    op.add_column('log_entries', sa.Column('response_delay_ms', sa.Float(), nullable=True))


def downgrade() -> None:
    # Remove response_delay_ms column from log_entries table
    op.drop_column('log_entries', 'response_delay_ms')
