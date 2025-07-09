#!/usr/bin/env python3
"""
Database setup script for Rubberduck.
This script ensures all necessary tables and data are created properly.
"""

import os
import sys
from pathlib import Path

# Add the src directory to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from sqlalchemy import create_engine, inspect
from alembic.config import Config
from alembic import command
from rubberduck.database import Base, engine
from rubberduck.models import User, Proxy, LogEntry, CacheEntry


def check_tables_exist():
    """Check if all required tables exist."""
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    
    required_tables = {
        'users',
        'proxies', 
        'log_entries',
        'cache_entries',
        'alembic_version'
    }
    
    missing_tables = required_tables - existing_tables
    return missing_tables


def setup_alembic():
    """Run alembic migrations to create all tables."""
    print("Running database migrations...")
    
    # Configure alembic
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    
    try:
        # Run migrations to head
        command.upgrade(alembic_cfg, "head")
        print("✓ Database migrations completed successfully")
        return True
    except Exception as e:
        print(f"✗ Error running migrations: {e}")
        return False


def verify_database():
    """Verify that all tables and data are properly set up."""
    print("\nVerifying database setup...")
    
    # Check tables
    missing_tables = check_tables_exist()
    if missing_tables:
        print(f"✗ Missing tables: {missing_tables}")
        return False
    
    print("✓ All required tables exist")
    
    # Test basic functionality
    try:
        from rubberduck.database import SessionLocal
        session = SessionLocal()
        
        # Test each table
        user_count = session.query(User).count()
        proxy_count = session.query(Proxy).count()
        log_count = session.query(LogEntry).count()
        cache_count = session.query(CacheEntry).count()
        
        print(f"✓ Database accessible - Users: {user_count}, Proxies: {proxy_count}, Logs: {log_count}, Cache: {cache_count}")
        
        session.close()
        return True
        
    except Exception as e:
        print(f"✗ Database verification failed: {e}")
        return False


def main():
    """Main setup function."""
    print("Rubberduck Database Setup")
    print("=" * 40)
    
    print(f"Project root: {project_root}")
    print(f"Database location: {project_root / 'rubberduck.db'}")
    
    # Check current state
    missing_tables = check_tables_exist()
    if missing_tables:
        print(f"Missing tables detected: {missing_tables}")
    else:
        print("All tables appear to exist")
    
    # Run migrations
    if not setup_alembic():
        print("\n❌ Database setup failed!")
        return 1
    
    # Verify setup
    if not verify_database():
        print("\n❌ Database verification failed!")
        return 1
    
    print("\n✅ Database setup completed successfully!")
    print("\nYou can now start the Rubberduck server.")
    return 0


if __name__ == "__main__":
    sys.exit(main())