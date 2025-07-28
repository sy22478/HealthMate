#!/bin/bash

# HealthMate PostgreSQL Setup Script
# This script helps set up PostgreSQL for the HealthMate application

echo "🗄️  HealthMate PostgreSQL Setup"
echo "=================================="

# Check if we're in the right directory
if [ ! -f "app/main.py" ]; then
    echo "❌ Error: Please run this script from the healthchat-rag directory"
    exit 1
fi

echo "✅ Current directory: $(pwd)"

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo "📦 Installing alembic..."
    pip install alembic
fi

# Check if alembic.ini exists
if [ ! -f "alembic.ini" ]; then
    echo "❌ Error: alembic.ini not found. Please ensure it's copied to this directory."
    exit 1
fi

echo "✅ Alembic configuration found"

# Check if env.py exists
if [ ! -f "alembic/env.py" ]; then
    echo "❌ Error: alembic/env.py not found. Please ensure it's copied to the alembic directory."
    exit 1
fi

echo "✅ Alembic environment configuration found"

# Check if DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  Warning: DATABASE_URL environment variable not set"
    echo "   Please set it to your PostgreSQL connection string"
    echo "   Example: export DATABASE_URL='postgresql://your_user:your_pass@your_host:your_port/your_db'"  # pragma: allowlist secret
    echo ""
    echo "📋 Manual Setup Required:"
    echo "1. Go to Railway Dashboard: https://railway.app/dashboard"
    echo "2. Add PostgreSQL service to your project"
    echo "3. Copy the connection string"
    echo "4. Set DATABASE_URL environment variable"
    echo "5. Run this script again"
    exit 1
fi

echo "✅ DATABASE_URL is set"

# Test database connection
echo "🔍 Testing database connection..."
python -c "
import os
from sqlalchemy import create_engine
try:
    engine = create_engine(os.getenv('DATABASE_URL'))
    with engine.connect() as conn:
        result = conn.execute('SELECT 1')
        print('✅ Database connection successful')
except Exception as e:
    print(f'❌ Database connection failed: {e}')
    exit(1)
"

if [ $? -ne 0 ]; then
    echo "❌ Database connection test failed"
    exit 1
fi

# Create new migration
echo "📝 Creating database migration..."
alembic revision --autogenerate -m "Initial database setup"

if [ $? -ne 0 ]; then
    echo "❌ Failed to create migration"
    exit 1
fi

echo "✅ Migration created successfully"

# Run migration
echo "🚀 Running database migration..."
alembic upgrade head

if [ $? -ne 0 ]; then
    echo "❌ Failed to run migration"
    exit 1
fi

echo "✅ Migration completed successfully"

# Show current migration status
echo "📊 Current migration status:"
alembic current

echo ""
echo "🎉 PostgreSQL setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Test user registration endpoint"
echo "2. Test health data storage"
echo "3. Test AI chat functionality"
echo "4. Monitor database performance"
echo ""
echo "🔗 Useful commands:"
echo "  - Check migration status: alembic current"
echo "  - List all migrations: alembic history"
echo "  - Downgrade migration: alembic downgrade -1"
echo "  - Upgrade migration: alembic upgrade head" 