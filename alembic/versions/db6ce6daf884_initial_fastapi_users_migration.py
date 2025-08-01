"""Initial FastAPI-Users migration

Revision ID: db6ce6daf884
Revises: 
Create Date: 2025-06-05 17:08:09.113955

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'src'))

from rubberduck.models import GUID


# revision identifiers, used by Alembic.
revision: str = 'db6ce6daf884'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('users',
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('id', GUID(), nullable=False),
    sa.Column('email', sa.String(length=320), nullable=False),
    sa.Column('hashed_password', sa.String(length=1024), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('is_superuser', sa.Boolean(), nullable=False),
    sa.Column('is_verified', sa.Boolean(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('proxies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('port', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(), nullable=True),
    sa.Column('user_id', GUID(), nullable=False),
    sa.Column('provider', sa.String(), nullable=False),
    sa.Column('model_name', sa.String(), nullable=False),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('failure_config', sa.String(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('port')
    )
    op.create_index(op.f('ix_proxies_id'), 'proxies', ['id'], unique=False)
    op.create_table('log_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('proxy_id', sa.Integer(), nullable=False),
    sa.Column('ip_address', sa.String(), nullable=False),
    sa.Column('status_code', sa.Integer(), nullable=False),
    sa.Column('latency', sa.Float(), nullable=False),
    sa.Column('cache_hit', sa.Boolean(), nullable=True),
    sa.Column('prompt_hash', sa.String(), nullable=True),
    sa.Column('failure_type', sa.String(), nullable=True),
    sa.Column('token_usage', sa.Integer(), nullable=True),
    sa.Column('cost', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['proxy_id'], ['proxies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_log_entries_id'), 'log_entries', ['id'], unique=False)
    op.create_table('cache_entries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('proxy_id', sa.Integer(), nullable=False),
    sa.Column('cache_key', sa.String(), nullable=False),
    sa.Column('request_data', sa.String(), nullable=False),
    sa.Column('response_data', sa.String(), nullable=False),
    sa.Column('response_headers', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['proxy_id'], ['proxies.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_cache_entries_cache_key'), 'cache_entries', ['cache_key'], unique=False)
    op.create_index(op.f('ix_cache_entries_id'), 'cache_entries', ['id'], unique=False)
    op.create_index('ix_cache_proxy_key', 'cache_entries', ['proxy_id', 'cache_key'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('ix_cache_proxy_key', table_name='cache_entries')
    op.drop_index(op.f('ix_cache_entries_id'), table_name='cache_entries')
    op.drop_index(op.f('ix_cache_entries_cache_key'), table_name='cache_entries')
    op.drop_table('cache_entries')
    op.drop_index(op.f('ix_log_entries_id'), table_name='log_entries')
    op.drop_table('log_entries')
    op.drop_index(op.f('ix_proxies_id'), table_name='proxies')
    op.drop_table('proxies')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    # ### end Alembic commands ###
