#!/bin/bash

# HealthMate Railway Startup Script

echo "🚀 Starting HealthMate application..."

# Activate virtual environment if it exists
if [ -d "/opt/venv" ]; then
    echo "📦 Activating virtual environment..."
    source /opt/venv/bin/activate
fi

# Set default port if not provided
export PORT=${PORT:-8000}

echo "🌐 Starting FastAPI server on port $PORT..."

# Start the FastAPI application
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1 --log-level info 