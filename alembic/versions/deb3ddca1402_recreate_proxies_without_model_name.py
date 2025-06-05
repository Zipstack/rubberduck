"""recreate_proxies_without_model_name

Revision ID: deb3ddca1402
Revises: 727f87f2b674
Create Date: 2025-06-05 20:03:32.264486

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'deb3ddca1402'
down_revision: Union[str, None] = '727f87f2b674'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
    
    # Create new table without model_name
    op.create_table('proxies_new',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('port', sa.Integer(), unique=True, nullable=True),
        sa.Column('status', sa.String(), default='stopped'),
        sa.Column('user_id', sa.String(32), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('failure_config', sa.String(), nullable=True),
    )
    
    # Copy data from old table (excluding model_name)
    op.execute("""
        INSERT INTO proxies_new (id, name, port, status, user_id, provider, description, created_at, failure_config)
        SELECT id, name, port, status, user_id, provider, description, created_at, failure_config
        FROM proxies
    """)
    
    # Drop old table and rename new one
    op.drop_table('proxies')
    op.rename_table('proxies_new', 'proxies')
    
    # Recreate indexes
    op.create_index('ix_proxies_id', 'proxies', ['id'])


def downgrade() -> None:
    # This would recreate the table with model_name, but since we don't have that data anymore,
    # we'll just raise an error
    raise NotImplementedError("Cannot downgrade this migration - model_name data would be lost")
