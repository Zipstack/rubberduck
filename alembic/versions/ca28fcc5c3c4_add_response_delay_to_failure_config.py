"""add_response_delay_to_failure_config

Revision ID: ca28fcc5c3c4
Revises: e9946bd0e7b7
Create Date: 2025-07-31 19:10:22.448585

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision: str = 'ca28fcc5c3c4'
down_revision: Union[str, None] = 'e9946bd0e7b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Update existing failure_config JSON to include response delay fields."""
    # Get connection
    conn = op.get_bind()
    
    # Query all proxies with failure_config
    result = conn.execute(sa.text("SELECT id, failure_config FROM proxies WHERE failure_config IS NOT NULL"))
    
    # Update each proxy's failure_config
    for row in result:
        proxy_id = row[0]
        config_json = row[1]
        
        if config_json:
            try:
                # Parse existing config
                config = json.loads(config_json)
                
                # Add new fields if they don't exist
                if 'response_delay_enabled' not in config:
                    config['response_delay_enabled'] = False
                if 'response_delay_min_seconds' not in config:
                    config['response_delay_min_seconds'] = 0.5
                if 'response_delay_max_seconds' not in config:
                    config['response_delay_max_seconds'] = 2.0
                if 'response_delay_cache_only' not in config:
                    config['response_delay_cache_only'] = True
                
                # Update the row
                updated_json = json.dumps(config)
                conn.execute(
                    sa.text("UPDATE proxies SET failure_config = :config WHERE id = :id"),
                    {"config": updated_json, "id": proxy_id}
                )
            except json.JSONDecodeError:
                # Skip invalid JSON
                print(f"Warning: Invalid JSON in proxy {proxy_id}, skipping")
                continue


def downgrade() -> None:
    """Remove response delay fields from failure_config JSON."""
    # Get connection
    conn = op.get_bind()
    
    # Query all proxies with failure_config
    result = conn.execute(sa.text("SELECT id, failure_config FROM proxies WHERE failure_config IS NOT NULL"))
    
    # Update each proxy's failure_config
    for row in result:
        proxy_id = row[0]
        config_json = row[1]
        
        if config_json:
            try:
                # Parse existing config
                config = json.loads(config_json)
                
                # Remove response delay fields
                config.pop('response_delay_enabled', None)
                config.pop('response_delay_min_seconds', None)
                config.pop('response_delay_max_seconds', None)
                config.pop('response_delay_cache_only', None)
                
                # Update the row
                updated_json = json.dumps(config)
                conn.execute(
                    sa.text("UPDATE proxies SET failure_config = :config WHERE id = :id"),
                    {"config": updated_json, "id": proxy_id}
                )
            except json.JSONDecodeError:
                # Skip invalid JSON
                print(f"Warning: Invalid JSON in proxy {proxy_id}, skipping")
                continue
