#!/bin/bash

echo "🚀 Starting HealthMate Simple Test..."

export PORT=${PORT:-8000}

echo "🌐 Starting FastAPI server on port $PORT..."

exec uvicorn app.main_simple:app --host 0.0.0.0 --port $PORT --log-level info 