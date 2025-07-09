# Rubberduck Setup Guide

This guide ensures you have all the necessary tables and data created properly for Rubberduck.

## Quick Setup (Recommended)

For a fresh installation, run the automated setup script:

```bash
# Make sure you're in the project root
cd /path/to/rubberduck

# Run the fresh installation script
./scripts/fresh_install.sh
```

This script will:
- Remove any existing database (for clean start)
- Run all database migrations
- Verify all tables are created properly
- Set up the default admin user

## Manual Setup

If you prefer to set up manually or troubleshoot issues:

### 1. Set up Python Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Database Migration

```bash
# Run all migrations to create tables
alembic upgrade head

# Verify setup
python scripts/setup_database.py
```

### 3. Start the Services

```bash
# Backend (Terminal 1)
source venv/bin/activate
python -m rubberduck.main

# Frontend (Terminal 2)
cd frontend
npm install
npm run dev
```

## Required Tables

The database setup creates these essential tables:

- **users** - User accounts and authentication
- **proxies** - Proxy configurations and settings
- **log_entries** - Request logs and analytics
- **cache_entries** - Response caching data
- **alembic_version** - Migration tracking

## Default User

A default admin user is automatically created:
- **Email**: admin@example.com
- **Password**: admin

## Troubleshooting

### Missing Tables Error

If you see errors like "no such table: cache_entries":

1. Run the setup verification:
   ```bash
   python scripts/setup_database.py
   ```

2. For fresh start:
   ```bash
   rm rubberduck.db  # Remove existing database
   alembic upgrade head  # Recreate all tables
   ```

### Migration Issues

Check migration status:
```bash
alembic current    # Show current migration
alembic history    # Show all migrations
```

### Permission Issues

Ensure the database file is writable:
```bash
chmod 664 rubberduck.db
```

## Verification

After setup, verify everything works:

1. **Backend** should start without errors on http://localhost:9000
2. **Frontend** should be accessible at http://localhost:5173
3. **Login** with admin@example.com / admin should work
4. **Create a proxy** to test basic functionality

## Getting Help

If you encounter issues:
1. Check the backend logs for specific error messages
2. Verify all required tables exist with the setup script
3. Ensure you're using the correct Python virtual environment
4. Check that all dependencies are installed correctly