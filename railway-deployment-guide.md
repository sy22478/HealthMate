# HealthMate Free Deployment Guide - Railway.app

## Overview
This guide will help you deploy HealthMate to Railway.app completely free for development and small-scale production use.

## Prerequisites
- GitHub account
- Railway.app account (free)
- OpenAI API key
- Pinecone API key

## Step 1: Prepare Your Application

### 1.1 Create Railway Configuration
Create a `railway.toml` file in your project root:

```toml
[build]
builder = "nixpacks"

[deploy]
startCommand = "uvicorn app.main:app --host 0.0.0.0 --port $PORT"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "on_failure"

[[services]]
name = "healthmate-backend"
```

### 1.2 Update Dockerfile for Railway
Create a `Dockerfile.railway` optimized for Railway:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd -m -u 1000 healthmate && chown -R healthmate:healthmate /app
USER healthmate

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 1.3 Create Railway Environment Variables
Create a `.env.railway` file:

```env
# Railway will automatically set PORT
PORT=8000

# Database (Railway PostgreSQL)
DATABASE_URL=${DATABASE_URL}

# Redis (Railway Redis)
REDIS_URL=${REDIS_URL}

# OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Pinecone
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=your_pinecone_environment
PINECONE_INDEX_NAME=healthmate-index

# Security
SECRET_KEY=your_secret_key_here
ENVIRONMENT=production

# CORS
CORS_ALLOW_ORIGINS=https://your-domain.railway.app

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS_PER_MINUTE=60
RATE_LIMIT_REQUESTS_PER_HOUR=1000
```

## Step 2: Deploy to Railway

### 2.1 Connect GitHub Repository
1. Go to [Railway.app](https://railway.app)
2. Sign up with your GitHub account
3. Click "New Project"
4. Select "Deploy from GitHub repo"
5. Choose your HealthMate repository

### 2.2 Configure Services
Railway will automatically detect your services. Configure them:

#### Backend Service
- **Name**: healthmate-backend
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

#### PostgreSQL Database
1. Click "New Service" → "Database" → "PostgreSQL"
2. Railway will automatically set `DATABASE_URL` environment variable

#### Redis Cache
1. Click "New Service" → "Database" → "Redis"
2. Railway will automatically set `REDIS_URL` environment variable

### 2.3 Set Environment Variables
In Railway dashboard, go to your backend service → Variables:

```env
# Add these environment variables
OPENAI_API_KEY=your_actual_openai_key
PINECONE_API_KEY=your_actual_pinecone_key
PINECONE_ENVIRONMENT=us-west1-gcp
PINECONE_INDEX_NAME=healthmate-index
SECRET_KEY=your_generated_secret_key
ENVIRONMENT=production
CORS_ALLOW_ORIGINS=https://your-app.railway.app
```

### 2.4 Deploy
1. Railway will automatically deploy when you push to GitHub
2. Or click "Deploy" in the Railway dashboard
3. Wait for build and deployment to complete

## Step 3: Configure Custom Domain

### 3.1 Add Custom Domain
1. Go to your backend service → Settings → Domains
2. Click "Generate Domain" or add your custom domain
3. Railway will automatically provision SSL certificate

### 3.2 Update CORS Settings
Update your `CORS_ALLOW_ORIGINS` environment variable with your new domain.

## Step 4: Database Setup

### 4.1 Run Migrations
Connect to your Railway PostgreSQL database and run migrations:

```bash
# Get database connection string from Railway dashboard
railway connect

# Run migrations
alembic upgrade head
```

### 4.2 Initialize Database
```bash
# Create initial data
python -c "from app.database import init_db; init_db()"
```

## Step 5: Monitor and Scale

### 5.1 Monitor Usage
- Railway dashboard shows resource usage
- Monitor your $5 monthly credit usage
- Set up alerts for approaching limits

### 5.2 Scale When Needed
When you approach free tier limits:
1. **Upgrade to Hobby Plan**: $5/month
   - 1GB RAM
   - No sleep
   - Custom domains
   - 100GB bandwidth

2. **Upgrade to Pro Plan**: $20/month
   - 2GB RAM
   - Dedicated resources
   - Priority support

## Free Tier Limitations & Workarounds

### Limitations:
- ⚠️ **512MB RAM**: May be insufficient for heavy AI processing
- ⚠️ **Shared CPU**: Slower response times during peak usage
- ⚠️ **1GB Storage**: Limited for large datasets
- ⚠️ **$5 Credit**: May run out with heavy usage

### Workarounds:
1. **Optimize Memory Usage**:
   - Use streaming responses for large AI responses
   - Implement pagination for database queries
   - Cache frequently accessed data

2. **Reduce API Calls**:
   - Cache OpenAI responses
   - Batch Pinecone operations
   - Implement rate limiting

3. **Monitor Usage**:
   - Set up Railway usage alerts
   - Monitor OpenAI API costs
   - Track Pinecone usage

## Cost Optimization Tips

### 1. Minimize External API Costs
```python
# Cache OpenAI responses
import redis
import json

def get_cached_response(prompt, cache_ttl=3600):
    cache_key = f"openai:{hash(prompt)}"
    cached = redis_client.get(cache_key)
    if cached:
        return json.loads(cached)
    
    response = openai_client.chat.completions.create(...)
    redis_client.setex(cache_key, cache_ttl, json.dumps(response))
    return response
```

### 2. Optimize Database Queries
```python
# Use connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True
)
```

### 3. Implement Efficient Caching
```python
# Redis caching strategy
CACHE_TTL = {
    'user_profile': 3600,      # 1 hour
    'health_metrics': 1800,    # 30 minutes
    'ai_responses': 7200,      # 2 hours
    'analytics': 86400,        # 24 hours
}
```

## Troubleshooting

### Common Issues:

1. **Build Failures**:
   - Check requirements.txt for compatibility
   - Ensure all dependencies are listed
   - Verify Python version compatibility

2. **Database Connection Issues**:
   - Verify DATABASE_URL environment variable
   - Check PostgreSQL service is running
   - Ensure proper SSL configuration

3. **Memory Issues**:
   - Monitor memory usage in Railway dashboard
   - Optimize application memory usage
   - Consider upgrading to paid plan

4. **API Rate Limits**:
   - Implement proper rate limiting
   - Cache external API responses
   - Monitor API usage costs

## Next Steps

### When to Upgrade:
- **User Growth**: >100 active users
- **Performance Issues**: Slow response times
- **Memory Constraints**: Frequent out-of-memory errors
- **Cost Concerns**: Approaching $5 monthly limit

### Migration Path:
1. **Start with Railway Free**: $0/month
2. **Upgrade to Railway Hobby**: $5/month
3. **Consider GCP/AWS**: $50-200/month (for production scale)

## Support Resources

- [Railway Documentation](https://docs.railway.app)
- [Railway Discord Community](https://discord.gg/railway)
- [HealthMate GitHub Issues](your-repo-url/issues)

---

**Total Free Deployment Cost: $0/month**
**Upgrade Path: $5-20/month when needed** 