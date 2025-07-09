"""add_default_user

Revision ID: e9946bd0e7b7
Revises: deb3ddca1402
Create Date: 2025-06-26 14:56:00.390046

"""
from typing import Sequence, Union
import uuid
from datetime import datetime

from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext


# revision identifiers, used by Alembic.
revision: str = 'e9946bd0e7b7'
down_revision: Union[str, None] = 'deb3ddca1402'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create password hash context
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto", bcrypt__rounds=12)
    
    # Get database connection
    conn = op.get_bind()
    
    # Check if any users exist
    result = conn.execute(sa.text("SELECT COUNT(*) FROM users")).fetchone()
    user_count = result[0] if result else 0
    
    # Only create default user if no users exist
    if user_count == 0:
        # Generate UUID and hash password
        user_id = str(uuid.uuid4())
        hashed_password = pwd_context.hash("admin")
        created_at = datetime.utcnow()
        
        # Insert default user
        conn.execute(sa.text("""
            INSERT INTO users (id, email, hashed_password, is_active, is_superuser, is_verified, created_at)
            VALUES (:id, :email, :hashed_password, :is_active, :is_superuser, :is_verified, :created_at)
        """), {
            'id': user_id,
            'email': 'admin@example.com',
            'hashed_password': hashed_password,
            'is_active': True,
            'is_superuser': False,
            'is_verified': True,
            'created_at': created_at
        })


def downgrade() -> None:
    # Remove the default user if it exists
    conn = op.get_bind()
    conn.execute(sa.text("DELETE FROM users WHERE email = 'admin@example.com'"))
