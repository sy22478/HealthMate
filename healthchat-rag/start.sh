#!/bin/bash

# HealthMate Railway Startup Script

echo "🚀 Starting HealthMate application..."

# Activate virtual environment if it exists
if [ -d "/opt/venv" ]; then
    echo "📦 Activating virtual environment..."
    source /opt/venv/bin/activate
fi

# Set default port if not provided (Railway sets PORT environment variable)
export PORT=${PORT:-8000}

echo "🌐 Starting FastAPI server on port $PORT..."
echo "🔧 Environment: $ENVIRONMENT"
echo "🔧 Host: 0.0.0.0"
echo "🔧 Port: $PORT"

# Start the FastAPI application with Railway-specific settings
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port $PORT \
    --workers 1 \
    --log-level info \
    --timeout-keep-alive 75 \
    --access-log 