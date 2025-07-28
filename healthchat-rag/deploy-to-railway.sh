#!/bin/bash

# HealthMate Railway Deployment Script
# This script helps you deploy HealthMate to Railway.app

echo "🚀 HealthMate Railway Deployment Script"
echo "========================================"

# Check if Railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Installing..."
    npm install -g @railway/cli
fi

# Check if user is logged in to Railway
if ! railway whoami &> /dev/null; then
    echo "🔐 Please log in to Railway..."
    railway login
fi

echo "📋 Deployment Steps:"
echo "1. Create a new Railway project"
echo "2. Connect your GitHub repository"
echo "3. Configure environment variables"
echo "4. Deploy the application"
echo ""

echo "🔧 Step 1: Create Railway Project"
echo "Go to https://railway.app and:"
echo "  - Click 'New Project'"
echo "  - Select 'Deploy from GitHub repo'"
echo "  - Choose your HealthMate repository"
echo ""

echo "🔧 Step 2: Configure Services"
echo "In Railway dashboard:"
echo "  - Add PostgreSQL database service"
echo "  - Add Redis cache service"
echo "  - Configure backend service"
echo ""

echo "🔧 Step 3: Set Environment Variables"
echo "Add these environment variables in Railway:"
echo ""
echo "Required Variables:"
echo "  OPENAI_API_KEY=your_openai_api_key"
echo "  PINECONE_API_KEY=your_pinecone_api_key"
echo "  PINECONE_ENVIRONMENT=your_pinecone_environment"
echo "  PINECONE_INDEX_NAME=healthmate-index"
echo "  SECRET_KEY=your_generated_secret_key"
echo "  ENVIRONMENT=production"
echo ""

echo "Optional Variables:"
echo "  CORS_ALLOW_ORIGINS=https://your-app.railway.app"
echo "  RATE_LIMIT_ENABLED=true"
echo "  RATE_LIMIT_REQUESTS_PER_MINUTE=60"
echo "  RATE_LIMIT_REQUESTS_PER_HOUR=1000"
echo ""

echo "🔧 Step 4: Deploy"
echo "Railway will automatically deploy when you push to GitHub."
echo "Or click 'Deploy' in the Railway dashboard."
echo ""

echo "🔧 Step 5: Database Setup"
echo "After deployment, run database migrations:"
echo "  railway connect"
echo "  alembic upgrade head"
echo ""

echo "🔧 Step 6: Custom Domain"
echo "In Railway dashboard:"
echo "  - Go to your service → Settings → Domains"
echo "  - Click 'Generate Domain' or add custom domain"
echo "  - Update CORS_ALLOW_ORIGINS with your domain"
echo ""

echo "✅ Deployment Complete!"
echo "Your app will be available at: https://your-app.railway.app"
echo ""

echo "📊 Monitor your deployment:"
echo "  - Railway dashboard: https://railway.app"
echo "  - Check logs: railway logs"
echo "  - Monitor usage: railway usage"
echo ""

echo "💰 Cost Management:"
echo "  - Free tier: $5 credit/month"
echo "  - Monitor usage in Railway dashboard"
echo "  - Upgrade to Hobby ($5/month) when needed"
echo ""

echo "🎉 HealthMate is now deployed on Railway!" 