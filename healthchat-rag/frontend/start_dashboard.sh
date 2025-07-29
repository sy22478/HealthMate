#!/bin/bash

# HealthMate Frontend Dashboard Startup Script

echo "🎨 Starting HealthMate Frontend Dashboard..."

# Check if we're in the right directory
if [ ! -f "health_dashboard.py" ]; then
    echo "❌ Error: Please run this script from the frontend directory"
    exit 1
fi

echo "✅ Current directory: $(pwd)"

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "📦 Installing streamlit and dependencies..."
    pip install -r requirements.txt
fi

# Set environment variables
export HEALTHMATE_API_URL=${HEALTHMATE_API_URL:-"https://healthmate-production.up.railway.app"}
export STREAMLIT_SERVER_PORT=${STREAMLIT_SERVER_PORT:-8501}
export STREAMLIT_SERVER_ADDRESS=${STREAMLIT_SERVER_ADDRESS:-"0.0.0.0"}

echo "🌐 API URL: $HEALTHMATE_API_URL"
echo "🔧 Port: $STREAMLIT_SERVER_PORT"
echo "🔧 Address: $STREAMLIT_SERVER_ADDRESS"

# Start the dashboard
echo "🚀 Starting Streamlit dashboard..."
streamlit run health_dashboard.py \
    --server.port $STREAMLIT_SERVER_PORT \
    --server.address $STREAMLIT_SERVER_ADDRESS \
    --server.headless true \
    --browser.gatherUsageStats false 