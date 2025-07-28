#!/bin/bash

echo "🚀 Starting HealthMate Minimal..."

export PORT=${PORT:-8000}

echo "🌐 Starting FastAPI server on port $PORT..."

exec uvicorn app.main_minimal:app --host 0.0.0.0 --port $PORT --log-level info 