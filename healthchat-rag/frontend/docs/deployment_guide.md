# HealthChat RAG Dashboard - Deployment Guide

## Overview
This guide provides comprehensive instructions for deploying the HealthChat RAG Dashboard to production environments. It covers build configuration, environment setup, deployment scripts, and post-deployment verification.

## Table of Contents
1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Build Configuration](#build-configuration)
4. [Deployment Scripts](#deployment-scripts)
5. [Production Deployment](#production-deployment)
6. [Environment-Specific Configs](#environment-specific-configs)
7. [Deployment Checklist](#deployment-checklist)
8. [Monitoring & Maintenance](#monitoring--maintenance)
9. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements
- **Python**: 3.8 or higher
- **Node.js**: 14 or higher (for build tools)
- **Git**: Latest version
- **Docker**: 20.10 or higher (optional)
- **Database**: PostgreSQL 12 or higher

### Required Software
```bash
# Python packages
pip install streamlit
pip install streamlit-option-menu
pip install plotly
pip install streamlit-aggrid
pip install streamlit-card
pip install streamlit-elements
pip install pandas
pip install numpy
pip install pytest

# Node.js packages (if using build tools)
npm install -g yarn
npm install -g webpack
```

### Environment Variables
Create a `.env` file with the following variables:
```bash
# Application
APP_NAME=HealthChat RAG Dashboard
APP_VERSION=1.0.0
DEBUG=False
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/healthchat  # pragma: allowlist secret
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20

# Authentication
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION=3600

# External APIs
OPENAI_API_KEY=your-openai-api-key
VECTOR_DB_URL=your-vector-database-url

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# File Storage
STORAGE_BUCKET=your-storage-bucket
STORAGE_REGION=us-east-1
STORAGE_ACCESS_KEY=your-access-key
STORAGE_SECRET_KEY=your-secret-key
```

---

## Environment Configuration

### Development Environment
```bash
# development.env
DEBUG=True
LOG_LEVEL=DEBUG
DATABASE_URL=postgresql://localhost:5432/healthchat_dev
CACHE_URL=redis://localhost:6379/0
```

### Staging Environment
```bash
# staging.env
DEBUG=False
LOG_LEVEL=INFO
DATABASE_URL=postgresql://staging-db:5432/healthchat_staging
CACHE_URL=redis://staging-cache:6379/0
```

### Production Environment
```bash
# production.env
DEBUG=False
LOG_LEVEL=WARNING
DATABASE_URL=postgresql://prod-db:5432/healthchat_prod
CACHE_URL=redis://prod-cache:6379/0
```

### Environment Loading
```python
# config/environment.py
import os
from dotenv import load_dotenv

def load_environment():
    """Load environment variables based on current environment"""
    env = os.getenv('ENVIRONMENT', 'development')
    env_file = f"{env}.env"
    
    if os.path.exists(env_file):
        load_dotenv(env_file)
    
    return {
        'DEBUG': os.getenv('DEBUG', 'False').lower() == 'true',
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'DATABASE_URL': os.getenv('DATABASE_URL'),
        'CACHE_URL': os.getenv('CACHE_URL'),
        'SECRET_KEY': os.getenv('SECRET_KEY'),
        'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'VECTOR_DB_URL': os.getenv('VECTOR_DB_URL'),
        'SMTP_HOST': os.getenv('SMTP_HOST'),
        'SMTP_PORT': os.getenv('SMTP_PORT'),
        'SMTP_USER': os.getenv('SMTP_USER'),
        'SMTP_PASSWORD': os.getenv('SMTP_PASSWORD'),
        'STORAGE_BUCKET': os.getenv('STORAGE_BUCKET'),
        'STORAGE_REGION': os.getenv('STORAGE_REGION'),
        'STORAGE_ACCESS_KEY': os.getenv('STORAGE_ACCESS_KEY'),
        'STORAGE_SECRET_KEY': os.getenv('STORAGE_SECRET_KEY'),
    }
```

---

## Build Configuration

### Streamlit Configuration
```toml
# .streamlit/config.toml
[global]
developmentMode = false

[server]
headless = true
port = 8501
enableCORS = false
enableXsrfProtection = true

[browser]
gatherUsageStats = false

[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
```

### Production Build Script
```bash
#!/bin/bash
# scripts/build.sh

set -e

echo "Starting production build..."

# Set environment
export ENVIRONMENT=production

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run tests
echo "Running tests..."
pytest tests/ -v --tb=short

# Build static assets
echo "Building static assets..."
python -m streamlit build frontend/

# Optimize images
echo "Optimizing images..."
find frontend/assets/images -name "*.png" -exec optipng {} \;
find frontend/assets/images -name "*.jpg" -exec jpegoptim {} \;

# Create deployment package
echo "Creating deployment package..."
tar -czf healthchat-dashboard-$(date +%Y%m%d-%H%M%S).tar.gz \
    frontend/ \
    requirements.txt \
    .streamlit/ \
    scripts/ \
    docs/ \
    --exclude=*.pyc \
    --exclude=__pycache__ \
    --exclude=.git \
    --exclude=node_modules

echo "Build completed successfully!"
```

### Docker Configuration
```dockerfile
# Dockerfile
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        curl \
        git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Create non-root user
RUN useradd -m -u 1000 streamlit
RUN chown -R streamlit:streamlit /app
USER streamlit

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health

# Run application
CMD ["streamlit", "run", "frontend/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Docker Compose
```yaml
# docker-compose.yml
version: '3.8'

services:
  dashboard:
    build: .
    ports:
      - "8501:8501"
    environment:
      - ENVIRONMENT=production
      - DATABASE_URL=postgresql://postgres:password@db:5432/healthchat  # pragma: allowlist secret
      - CACHE_URL=redis://cache:6379/0
    depends_on:
      - db
      - cache
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=healthchat
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password  # pragma: allowlist secret
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  cache:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - dashboard
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
```

---

## Deployment Scripts

### Automated Deployment Script
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

# Configuration
APP_NAME="healthchat-dashboard"
DEPLOY_PATH="/opt/healthchat"
BACKUP_PATH="/opt/backups"
LOG_FILE="/var/log/healthchat/deploy.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}" | tee -a $LOG_FILE
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a $LOG_FILE
    exit 1
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}" | tee -a $LOG_FILE
}

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root"
fi

# Create log directory
sudo mkdir -p /var/log/healthchat
sudo chown $USER:$USER /var/log/healthchat

log "Starting deployment of $APP_NAME"

# Backup current version
if [ -d "$DEPLOY_PATH" ]; then
    log "Creating backup of current version"
    sudo tar -czf "$BACKUP_PATH/backup-$(date +%Y%m%d-%H%M%S).tar.gz" -C "$DEPLOY_PATH" .
fi

# Stop application
log "Stopping application"
sudo systemctl stop healthchat-dashboard || warning "Service not running"

# Deploy new version
log "Deploying new version"
sudo rm -rf "$DEPLOY_PATH"
sudo mkdir -p "$DEPLOY_PATH"
sudo tar -xzf "healthchat-dashboard-*.tar.gz" -C "$DEPLOY_PATH"

# Set permissions
log "Setting permissions"
sudo chown -R $USER:$USER "$DEPLOY_PATH"
sudo chmod -R 755 "$DEPLOY_PATH"

# Install dependencies
log "Installing dependencies"
cd "$DEPLOY_PATH"
pip install -r requirements.txt

# Run database migrations
log "Running database migrations"
python -m alembic upgrade head

# Start application
log "Starting application"
sudo systemctl start healthchat-dashboard

# Wait for application to start
log "Waiting for application to start"
sleep 10

# Health check
log "Performing health check"
if curl -f http://localhost:8501/_stcore/health; then
    log "Health check passed"
else
    error "Health check failed"
fi

# Cleanup old backups (keep last 5)
log "Cleaning up old backups"
cd "$BACKUP_PATH"
ls -t | tail -n +6 | xargs -r rm

log "Deployment completed successfully!"
```

### Systemd Service Configuration
```ini
# /etc/systemd/system/healthchat-dashboard.service
[Unit]
Description=HealthChat RAG Dashboard
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=healthchat
Group=healthchat
WorkingDirectory=/opt/healthchat
Environment=ENVIRONMENT=production
Environment=PATH=/opt/healthchat/venv/bin
ExecStart=/opt/healthchat/venv/bin/streamlit run frontend/streamlit_app.py --server.port=8501 --server.address=0.0.0.0
ExecReload=/bin/kill -HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Nginx Configuration
```nginx
# nginx.conf
events {
    worker_connections 1024;
}

http {
    upstream streamlit {
        server 127.0.0.1:8501;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;

    server {
        listen 80;
        server_name healthchat.example.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name healthchat.example.com;

        # SSL configuration
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        ssl_protocols TLSv1.2 TLSv1.3;
        ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
        ssl_prefer_server_ciphers off;

        # Security headers
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        add_header X-XSS-Protection "1; mode=block";
        add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        limit_req zone=login burst=5 nodelay;

        # Proxy settings
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;

        # Static files
        location /static/ {
            alias /opt/healthchat/frontend/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
        }

        # Main application
        location / {
            proxy_pass http://streamlit;
            proxy_read_timeout 300s;
            proxy_connect_timeout 75s;
        }

        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
    }
}
```

---

## Production Deployment

### Deployment Steps
1. **Prepare Environment**
   ```bash
   # Create deployment user
   sudo useradd -m -s /bin/bash healthchat
   sudo usermod -aG sudo healthchat
   
   # Create directories
   sudo mkdir -p /opt/healthchat
   sudo mkdir -p /opt/backups
   sudo mkdir -p /var/log/healthchat
   sudo chown healthchat:healthchat /opt/healthchat /opt/backups /var/log/healthchat
   ```

2. **Build Application**
   ```bash
   # Run build script
   ./scripts/build.sh
   ```

3. **Deploy Application**
   ```bash
   # Run deployment script
   ./scripts/deploy.sh
   ```

4. **Configure Services**
   ```bash
   # Enable and start services
   sudo systemctl enable healthchat-dashboard
   sudo systemctl start healthchat-dashboard
   sudo systemctl enable nginx
   sudo systemctl start nginx
   ```

5. **Verify Deployment**
   ```bash
   # Check service status
   sudo systemctl status healthchat-dashboard
   sudo systemctl status nginx
   
   # Test application
   curl -f http://localhost:8501/_stcore/health
   ```

---

## Environment-Specific Configs

### Development
```python
# config/development.py
DEBUG = True
LOG_LEVEL = 'DEBUG'
DATABASE_URL = 'postgresql://localhost:5432/healthchat_dev'
CACHE_URL = 'redis://localhost:6379/0'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']
```

### Staging
```python
# config/staging.py
DEBUG = False
LOG_LEVEL = 'INFO'
DATABASE_URL = 'postgresql://staging-db:5432/healthchat_staging'
CACHE_URL = 'redis://staging-cache:6379/0'
ALLOWED_HOSTS = ['staging.healthchat.com']
```

### Production
```python
# config/production.py
DEBUG = False
LOG_LEVEL = 'WARNING'
DATABASE_URL = 'postgresql://prod-db:5432/healthchat_prod'
CACHE_URL = 'redis://prod-cache:6379/0'
ALLOWED_HOSTS = ['healthchat.com', 'www.healthchat.com']
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] All tests passing
- [ ] Code review completed
- [ ] Environment variables configured
- [ ] Database migrations ready
- [ ] SSL certificates installed
- [ ] Backup strategy in place
- [ ] Monitoring configured
- [ ] Rollback plan prepared

### Deployment
- [ ] Backup current version
- [ ] Deploy new version
- [ ] Run database migrations
- [ ] Update static files
- [ ] Restart services
- [ ] Verify health checks
- [ ] Test critical functionality
- [ ] Monitor error logs

### Post-Deployment
- [ ] Verify all features work
- [ ] Check performance metrics
- [ ] Monitor error rates
- [ ] Test user flows
- [ ] Update documentation
- [ ] Notify stakeholders
- [ ] Clean up old files
- [ ] Update deployment log

### Rollback Plan
```bash
#!/bin/bash
# scripts/rollback.sh

set -e

log "Starting rollback..."

# Stop application
sudo systemctl stop healthchat-dashboard

# Restore from backup
BACKUP_FILE=$(ls -t /opt/backups/backup-*.tar.gz | head -1)
if [ -n "$BACKUP_FILE" ]; then
    sudo rm -rf /opt/healthchat/*
    sudo tar -xzf "$BACKUP_FILE" -C /opt/healthchat
    log "Restored from backup: $BACKUP_FILE"
else
    error "No backup found for rollback"
fi

# Start application
sudo systemctl start healthchat-dashboard

# Verify rollback
sleep 10
if curl -f http://localhost:8501/_stcore/health; then
    log "Rollback completed successfully"
else
    error "Rollback failed - health check failed"
fi
```

---

## Monitoring & Maintenance

### Logging Configuration
```python
# config/logging.py
import logging
import logging.handlers
import os

def setup_logging():
    """Configure logging for the application"""
    
    # Create logs directory
    os.makedirs('/var/log/healthchat', exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.handlers.RotatingFileHandler(
                '/var/log/healthchat/app.log',
                maxBytes=10485760,  # 10MB
                backupCount=5
            ),
            logging.StreamHandler()
        ]
    )
    
    # Set specific loggers
    logging.getLogger('streamlit').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)
```

### Monitoring Script
```bash
#!/bin/bash
# scripts/monitor.sh

# Check application health
check_health() {
    if curl -f http://localhost:8501/_stcore/health > /dev/null 2>&1; then
        echo "OK"
    else
        echo "FAIL"
    fi
}

# Check disk space
check_disk() {
    DISK_USAGE=$(df /opt/healthchat | tail -1 | awk '{print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 90 ]; then
        echo "WARNING: Disk usage is ${DISK_USAGE}%"
    else
        echo "OK"
    fi
}

# Check memory usage
check_memory() {
    MEMORY_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ $MEMORY_USAGE -gt 90 ]; then
        echo "WARNING: Memory usage is ${MEMORY_USAGE}%"
    else
        echo "OK"
    fi
}

# Main monitoring
echo "Health Check: $(check_health)"
echo "Disk Usage: $(check_disk)"
echo "Memory Usage: $(check_memory)"
```

### Maintenance Tasks
```bash
#!/bin/bash
# scripts/maintenance.sh

# Daily maintenance tasks
daily_maintenance() {
    # Clean old logs
    find /var/log/healthchat -name "*.log.*" -mtime +7 -delete
    
    # Clean old backups
    find /opt/backups -name "backup-*.tar.gz" -mtime +30 -delete
    
    # Update system packages
    sudo apt-get update && sudo apt-get upgrade -y
    
    # Restart services if needed
    sudo systemctl restart healthchat-dashboard
}

# Weekly maintenance tasks
weekly_maintenance() {
    # Database maintenance
    psql $DATABASE_URL -c "VACUUM ANALYZE;"
    
    # Check for security updates
    sudo unattended-upgrades --dry-run
    
    # Backup database
    pg_dump $DATABASE_URL > /opt/backups/db-$(date +%Y%m%d).sql
}

# Run maintenance based on argument
case $1 in
    daily)
        daily_maintenance
        ;;
    weekly)
        weekly_maintenance
        ;;
    *)
        echo "Usage: $0 {daily|weekly}"
        exit 1
        ;;
esac
```

---

## Troubleshooting

### Common Issues

**Application won't start**
```bash
# Check logs
sudo journalctl -u healthchat-dashboard -f

# Check permissions
ls -la /opt/healthchat/

# Check dependencies
pip list | grep streamlit
```

**Database connection issues**
```bash
# Test database connection
psql $DATABASE_URL -c "SELECT 1;"

# Check database status
sudo systemctl status postgresql

# Check database logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

**Performance issues**
```bash
# Check resource usage
htop
df -h
free -h

# Check application logs
tail -f /var/log/healthchat/app.log

# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Emergency Procedures

**Emergency rollback**
```bash
# Immediate rollback
sudo systemctl stop healthchat-dashboard
sudo tar -xzf /opt/backups/backup-$(ls -t /opt/backups/backup-*.tar.gz | head -1 | xargs basename -s .tar.gz) -C /opt/healthchat
sudo systemctl start healthchat-dashboard
```

**Database recovery**
```bash
# Restore from backup
sudo systemctl stop healthchat-dashboard
psql $DATABASE_URL < /opt/backups/db-$(date +%Y%m%d).sql
sudo systemctl start healthchat-dashboard
```

**Service recovery**
```bash
# Restart all services
sudo systemctl restart healthchat-dashboard
sudo systemctl restart nginx
sudo systemctl restart postgresql
sudo systemctl restart redis
```

---

## Version History

### v1.0.0 (Current)
- Initial deployment guide
- Production build configuration
- Docker deployment
- Systemd service configuration
- Nginx reverse proxy
- Monitoring and maintenance scripts
- Troubleshooting guide

### Future Enhancements
- Kubernetes deployment
- CI/CD pipeline integration
- Advanced monitoring with Prometheus
- Automated scaling
- Blue-green deployment
- Canary releases 