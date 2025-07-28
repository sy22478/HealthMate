# HealthMate System Architecture Documentation

## 🏗️ Complete System Architecture Guide

This document provides comprehensive system architecture documentation for the HealthMate application, including deployment guides, infrastructure setup, and developer onboarding.

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagrams](#architecture-diagrams)
3. [Technology Stack](#technology-stack)
4. [Infrastructure Setup](#infrastructure-setup)
5. [Deployment Guide](#deployment-guide)
6. [Database Architecture](#database-architecture)
7. [Security Architecture](#security-architecture)
8. [Monitoring & Observability](#monitoring--observability)
9. [Scaling Strategy](#scaling-strategy)
10. [Developer Onboarding](#developer-onboarding)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Maintenance Procedures](#maintenance-procedures)

## 🎯 System Overview

### High-Level Architecture

HealthMate is a microservices-based healthcare application built with modern cloud-native technologies. The system is designed for high availability, scalability, and compliance with healthcare regulations.

### Core Components

1. **API Gateway**: FastAPI-based REST API with versioning
2. **Authentication Service**: JWT-based authentication with RBAC
3. **Health Data Service**: Health data management and processing
4. **AI Chat Service**: OpenAI-powered health assistant
5. **Compliance Service**: HIPAA and GDPR compliance management
6. **Analytics Service**: Health analytics and insights
7. **Notification Service**: Multi-channel notifications
8. **WebSocket Service**: Real-time communication

### System Characteristics

- **Availability**: 99.9% uptime target
- **Scalability**: Horizontal scaling with auto-scaling
- **Security**: End-to-end encryption and compliance
- **Performance**: <200ms API response time
- **Reliability**: Fault-tolerant with redundancy

## 🏛️ Architecture Diagrams

### System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Load Balancer                           │
│                    (NGINX/ALB/Cloud Load Balancer)             │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                        API Gateway                              │
│                    (FastAPI + Middleware)                      │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                    Microservices Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   Auth      │ │   Health    │ │     AI      │ │ Compliance  │ │
│  │  Service    │ │   Data      │ │   Chat      │ │  Service    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ Analytics   │ │Notification │ │ WebSocket   │ │ User Mgmt   │ │
│  │  Service    │ │  Service    │ │  Service    │ │  Service    │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                    Data Layer                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ PostgreSQL  │ │   Redis     │ │  Pinecone   │ │   MinIO     │ │
│  │  (Primary)  │ │  (Cache)    │ │ (Vector DB) │ │ (File Store)│ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                    Monitoring & Observability                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │ Prometheus  │ │   Grafana   │ │   Sentry    │ │   ELK       │ │
│  │ (Metrics)   │ │(Dashboards) │ │ (Errors)    │ │ (Logging)   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow Architecture

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Client    │───▶│  API Gateway│───▶│  Auth       │
│  (Web/Mobile)│    │             │    │  Service    │
└─────────────┘    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐    ┌─────────────┐
                    │  Rate       │    │  JWT        │
                    │  Limiting   │    │  Validation │
                    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐    ┌─────────────┐
                    │  Request    │    │  RBAC       │
                    │  Routing    │    │  Check      │
                    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐    ┌─────────────┐
                    │  Microservice│   │  Database   │
                    │  Processing │    │  Access     │
                    └─────────────┘    └─────────────┘
                           │                   │
                           ▼                   ▼
                    ┌─────────────┐    ┌─────────────┐
                    │  Response   │    │  Audit      │
                    │  Processing │    │  Logging    │
                    └─────────────┘    └─────────────┘
```

### Security Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Security Layer                           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   WAF       │ │   DDoS      │ │   SSL/TLS   │ │   API       │ │
│  │ Protection  │ │ Protection  │ │ Termination │ │ Gateway     │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                    Application Security                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   JWT       │ │   RBAC      │ │   Input     │ │   Audit     │ │
│  │   Auth      │ │   Access    │ │ Validation  │ │   Logging   │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────────────────────────────┐
│                    Data Security                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ │
│  │   Field     │ │   Database  │ │   Network   │ │   Backup    │ │
│  │ Encryption  │ │ Encryption  │ │ Encryption  │ │ Encryption  │ │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## 🛠️ Technology Stack

### Backend Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **API Framework** | FastAPI | 0.104.1 | High-performance API framework |
| **Language** | Python | 3.11+ | Main programming language |
| **Database** | PostgreSQL | 15+ | Primary relational database |
| **Cache** | Redis | 7.0+ | Session and data caching |
| **Vector DB** | Pinecone | Latest | Vector embeddings storage |
| **Message Queue** | Celery | 5.3+ | Asynchronous task processing |
| **WebSocket** | FastAPI WebSocket | 0.104.1 | Real-time communication |

### Frontend Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Web Framework** | Streamlit | 1.28+ | Web application interface |
| **UI Components** | Custom Components | - | Reusable UI components |
| **State Management** | Session State | - | Application state management |
| **Styling** | CSS3 + Custom | - | Application styling |

### AI/ML Technologies

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **LLM** | OpenAI GPT-4 | Latest | Natural language processing |
| **Embeddings** | OpenAI Embeddings | Latest | Text vectorization |
| **RAG Framework** | LangChain | 0.1+ | Retrieval-augmented generation |
| **Vector Search** | Pinecone | Latest | Similarity search |

### Infrastructure & DevOps

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Containerization** | Docker | 24.0+ | Application containerization |
| **Orchestration** | Kubernetes | 1.28+ | Container orchestration |
| **CI/CD** | GitHub Actions | Latest | Continuous integration |
| **Monitoring** | Prometheus | 2.47+ | Metrics collection |
| **Visualization** | Grafana | 10.0+ | Metrics visualization |
| **Error Tracking** | Sentry | Latest | Error monitoring |
| **Logging** | ELK Stack | 8.0+ | Centralized logging |

### Security & Compliance

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| **Authentication** | JWT | Latest | Token-based authentication |
| **Encryption** | AES-256 | - | Data encryption |
| **SSL/TLS** | Let's Encrypt | Latest | Transport security |
| **WAF** | Cloudflare | Latest | Web application firewall |
| **Compliance** | Custom | - | HIPAA/GDPR compliance |

## 🏗️ Infrastructure Setup

### Development Environment

#### Prerequisites

```bash
# System requirements
- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7.0+
- Node.js 18+ (for frontend tools)

# Development tools
- Git
- VS Code or PyCharm
- Postman or Insomnia
- pgAdmin or DBeaver
```

#### Local Development Setup

```bash
# 1. Clone repository
git clone https://github.com/healthmate/healthmate-backend.git
cd healthmate-backend

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 5. Start services with Docker Compose
docker-compose -f docker-compose.dev.yml up -d

# 6. Run database migrations
alembic upgrade head

# 7. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Environment Configuration

```bash
# .env file structure
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/healthmate
REDIS_URL=redis://localhost:6379

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key
ENCRYPTION_KEY=your-encryption-key

# External APIs
OPENAI_API_KEY=your-openai-api-key
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment

# Monitoring
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true

# Compliance
HIPAA_COMPLIANCE_ENABLED=true
GDPR_COMPLIANCE_ENABLED=true
```

### Production Environment

#### Cloud Infrastructure (AWS)

```yaml
# AWS Infrastructure Components
VPC:
  - Public Subnets (for load balancers)
  - Private Subnets (for application servers)
  - Database Subnets (for RDS)

Compute:
  - EKS Cluster (Kubernetes)
  - Auto Scaling Groups
  - Load Balancers (ALB/NLB)

Storage:
  - RDS PostgreSQL (Multi-AZ)
  - ElastiCache Redis (Cluster)
  - S3 (for file storage)
  - EBS (for persistent volumes)

Security:
  - Security Groups
  - IAM Roles
  - WAF
  - CloudTrail
  - GuardDuty

Monitoring:
  - CloudWatch
  - X-Ray
  - CloudWatch Logs
```

#### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthmate-api
  namespace: healthmate
spec:
  replicas: 3
  selector:
    matchLabels:
      app: healthmate-api
  template:
    metadata:
      labels:
        app: healthmate-api
    spec:
      containers:
      - name: healthmate-api
        image: healthmate/api:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: healthmate-secrets
              key: database-url
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: healthmate-secrets
              key: redis-url
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
```

## 🚀 Deployment Guide

### Deployment Environments

#### 1. Development Environment

```bash
# Deploy to development
kubectl apply -f k8s/dev/
kubectl set image deployment/healthmate-api healthmate-api=healthmate/api:dev
```

#### 2. Staging Environment

```bash
# Deploy to staging
kubectl apply -f k8s/staging/
kubectl set image deployment/healthmate-api healthmate-api=healthmate/api:staging
```

#### 3. Production Environment

```bash
# Deploy to production
kubectl apply -f k8s/prod/
kubectl set image deployment/healthmate-api healthmate-api=healthmate/api:latest
```

### CI/CD Pipeline

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest pytest-cov
    - name: Run tests
      run: |
        pytest --cov=app --cov-report=xml
    - name: Upload coverage
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Build Docker image
      run: |
        docker build -t healthmate/api:${{ github.sha }} .
        docker push healthmate/api:${{ github.sha }}

  deploy:
    needs: build
    runs-on: ubuntu-latest
    steps:
    - name: Deploy to production
      run: |
        kubectl set image deployment/healthmate-api healthmate-api=healthmate/api:${{ github.sha }}
        kubectl rollout status deployment/healthmate-api
```

### Database Migrations

```bash
# Run migrations
alembic upgrade head

# Rollback migrations
alembic downgrade -1

# Generate new migration
alembic revision --autogenerate -m "Description of changes"
```

## 🗄️ Database Architecture

### Database Schema Overview

```sql
-- Core tables
users                    -- User accounts and profiles
health_data             -- Health metrics and measurements
symptom_logs            -- Symptom tracking
medication_logs         -- Medication tracking
conversation_history    -- Chat conversations
audit_logs              -- Security audit trail

-- Enhanced health models
user_health_profiles    -- Comprehensive health profiles
enhanced_medications    -- Detailed medication information
enhanced_symptom_logs   -- Detailed symptom tracking
health_metrics_aggregation -- Aggregated health metrics

-- AI and analytics
user_preferences        -- User preferences and settings
user_feedback           -- User feedback on AI responses
ai_processing_logs      -- AI processing audit trail
```

### Database Optimization

#### Indexes

```sql
-- Performance indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_health_data_user_timestamp ON health_data(user_id, timestamp);
CREATE INDEX idx_conversation_user_id ON conversation_history(user_id);
CREATE INDEX idx_audit_logs_timestamp ON audit_logs(timestamp);

-- Composite indexes for common queries
CREATE INDEX idx_health_data_type_user ON health_data(data_type, user_id);
CREATE INDEX idx_symptom_logs_user_severity ON symptom_logs(user_id, severity);
```

#### Partitioning

```sql
-- Partition health_data by date
CREATE TABLE health_data_2024_01 PARTITION OF health_data
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- Partition audit_logs by date
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');
```

### Data Retention Policies

```sql
-- Automatic cleanup procedures
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Clean up old health data (keep 7 years)
    DELETE FROM health_data 
    WHERE timestamp < NOW() - INTERVAL '7 years';
    
    -- Clean up old conversation data (keep 1 year)
    DELETE FROM conversation_history 
    WHERE created_at < NOW() - INTERVAL '1 year';
    
    -- Clean up old audit logs (keep 7 years)
    DELETE FROM audit_logs 
    WHERE timestamp < NOW() - INTERVAL '7 years';
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup
SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT cleanup_old_data();');
```

## 🔒 Security Architecture

### Authentication & Authorization

#### JWT Token Security

```python
# JWT Configuration
JWT_CONFIG = {
    "algorithm": "HS256",
    "access_token_expiry": 1800,  # 30 minutes
    "refresh_token_expiry": 604800,  # 7 days
    "reset_token_expiry": 3600,  # 1 hour
    "fingerprint_enabled": True,
    "blacklist_enabled": True,
    "rate_limiting": {
        "max_attempts": 5,
        "window_seconds": 300
    }
}
```

#### Role-Based Access Control (RBAC)

```python
# RBAC Configuration
ROLES = {
    "patient": {
        "permissions": ["read_own_data", "write_own_data", "chat_access"],
        "data_access": "own_only"
    },
    "doctor": {
        "permissions": ["read_patient_data", "write_patient_data", "chat_access", "analytics"],
        "data_access": "assigned_patients"
    },
    "admin": {
        "permissions": ["all"],
        "data_access": "all"
    }
}
```

### Data Encryption

#### Field-Level Encryption

```python
# Encryption configuration
ENCRYPTION_CONFIG = {
    "algorithm": "AES-256-GCM",
    "key_rotation_days": 90,
    "encrypted_fields": [
        "users.full_name",
        "users.phone",
        "users.address",
        "health_data.value",
        "health_data.notes",
        "conversation_history.content"
    ]
}
```

#### Database Encryption

```sql
-- Enable database encryption
ALTER DATABASE healthmate SET encryption = 'on';

-- Encrypt sensitive columns
ALTER TABLE users ALTER COLUMN full_name SET ENCRYPTED;
ALTER TABLE health_data ALTER COLUMN value SET ENCRYPTED;
```

### Network Security

#### Security Groups

```yaml
# AWS Security Group Configuration
SecurityGroups:
  - LoadBalancerSG:
      Inbound:
        - Port: 443, Source: 0.0.0.0/0, Protocol: HTTPS
        - Port: 80, Source: 0.0.0.0/0, Protocol: HTTP
      Outbound:
        - Port: 8000, Destination: ApplicationSG, Protocol: TCP

  - ApplicationSG:
      Inbound:
        - Port: 8000, Source: LoadBalancerSG, Protocol: TCP
      Outbound:
        - Port: 5432, Destination: DatabaseSG, Protocol: TCP
        - Port: 6379, Destination: CacheSG, Protocol: TCP

  - DatabaseSG:
      Inbound:
        - Port: 5432, Source: ApplicationSG, Protocol: TCP
      Outbound:
        - Port: 0-65535, Source: 0.0.0.0/0, Protocol: All
```

## 📊 Monitoring & Observability

### Metrics Collection

#### Prometheus Configuration

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "healthmate_rules.yml"

scrape_configs:
  - job_name: 'healthmate-api'
    static_configs:
      - targets: ['healthmate-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'healthmate-database'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'healthmate-redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### Custom Metrics

```python
# Custom business metrics
from prometheus_client import Counter, Histogram, Gauge

# API metrics
api_requests_total = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
api_request_duration = Histogram('api_request_duration_seconds', 'API request duration')

# Business metrics
health_data_points_total = Counter('health_data_points_total', 'Total health data points', ['data_type'])
chat_messages_total = Counter('chat_messages_total', 'Total chat messages')
active_users = Gauge('active_users', 'Number of active users')
compliance_score = Gauge('compliance_score', 'Overall compliance score')
```

### Logging Strategy

#### Structured Logging

```python
# Logging configuration
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            "format": "%(timestamp)s %(level)s %(name)s %(message)s %(correlation_id)s"
        }
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json"
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/healthmate.log",
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
            "formatter": "json"
        }
    },
    "loggers": {
        "app": {
            "handlers": ["console", "file"],
            "level": "INFO"
        },
        "audit": {
            "handlers": ["file"],
            "level": "INFO"
        }
    }
}
```

### Alerting Rules

```yaml
# healthmate_rules.yml
groups:
  - name: healthmate
    rules:
      - alert: HighErrorRate
        expr: rate(api_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, api_request_duration_seconds) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }} seconds"

      - alert: LowComplianceScore
        expr: compliance_score < 95
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Low compliance score detected"
          description: "Compliance score is {{ $value }}%"
```

## 📈 Scaling Strategy

### Horizontal Scaling

#### Auto Scaling Configuration

```yaml
# Kubernetes HPA
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: healthmate-api-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: healthmate-api
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

#### Database Scaling

```yaml
# Database read replicas
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres-replica
spec:
  replicas: 3
  serviceName: postgres-replica
  template:
    spec:
      containers:
      - name: postgres
        image: postgres:15
        env:
        - name: POSTGRES_DB
          value: healthmate
        - name: POSTGRES_REPLICATION_MODE
          value: replica
        - name: POSTGRES_MASTER_HOST
          value: postgres-master
```

### Caching Strategy

#### Redis Configuration

```yaml
# Redis cluster configuration
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
spec:
  replicas: 6
  serviceName: redis-cluster
  template:
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "/etc/redis/redis.conf"]
        ports:
        - containerPort: 6379
        volumeMounts:
        - name: redis-config
          mountPath: /etc/redis
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "200m"
```

## 👨‍💻 Developer Onboarding

### Development Environment Setup

#### Step-by-Step Guide

```bash
# 1. Prerequisites installation
# Install Python 3.11+
# Install Docker and Docker Compose
# Install Git

# 2. Repository setup
git clone https://github.com/healthmate/healthmate-backend.git
cd healthmate-backend

# 3. Environment setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Database setup
docker-compose -f docker-compose.dev.yml up -d postgres redis
alembic upgrade head

# 5. Configuration
cp .env.example .env
# Edit .env with your local configuration

# 6. Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Development Tools

```yaml
# VS Code extensions
extensions:
  - ms-python.python
  - ms-python.black-formatter
  - ms-python.flake8
  - ms-python.pylint
  - ms-python.pytest
  - ms-python.vscode-pylance
  - redhat.vscode-yaml
  - ms-kubernetes-tools.vscode-kubernetes-tools
  - ms-azuretools.vscode-docker
```

### Code Standards

#### Python Code Style

```python
# .flake8 configuration
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude = .git,__pycache__,build,dist

# Black configuration
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
extend-exclude = '''
/(
  # directories
  \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | build
  | dist
)/
'''

# Pytest configuration
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "-v --cov=app --cov-report=html --cov-report=term-missing"
```

#### Git Workflow

```bash
# Branch naming convention
feature/user-authentication
bugfix/fix-login-issue
hotfix/security-patch
release/v2.0.0

# Commit message format
type(scope): description

# Examples
feat(auth): add JWT token refresh functionality
fix(api): resolve rate limiting issue
docs(api): update API documentation
test(auth): add unit tests for authentication
```

### Testing Strategy

#### Test Structure

```
tests/
├── unit/
│   ├── test_auth.py
│   ├── test_health_data.py
│   └── test_compliance.py
├── integration/
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_external_apis.py
├── e2e/
│   ├── test_user_workflow.py
│   └── test_compliance_workflow.py
└── conftest.py
```

#### Test Configuration

```python
# conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import get_db, Base

# Test database
SQLALCHEMY_DATABASE_URL = "postgresql://test:test@localhost:5432/test_db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)
```

## 🔧 Troubleshooting Guide

### Common Issues

#### 1. Database Connection Issues

```bash
# Check database connectivity
psql -h localhost -U healthmate -d healthmate

# Check database logs
docker logs healthmate-postgres

# Common solutions
- Verify DATABASE_URL in .env
- Check if PostgreSQL is running
- Verify network connectivity
- Check firewall settings
```

#### 2. Redis Connection Issues

```bash
# Check Redis connectivity
redis-cli -h localhost -p 6379 ping

# Check Redis logs
docker logs healthmate-redis

# Common solutions
- Verify REDIS_URL in .env
- Check if Redis is running
- Verify network connectivity
- Check memory usage
```

#### 3. API Performance Issues

```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health

# Check application logs
tail -f logs/healthmate.log | grep -E "(ERROR|WARNING)"

# Common solutions
- Check database query performance
- Verify cache hit rates
- Monitor resource usage
- Check for memory leaks
```

### Debugging Tools

#### Application Debugging

```python
# Enable debug mode
DEBUG = True

# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()

# Performance profiling
import cProfile
import pstats

def profile_function(func):
    profiler = cProfile.Profile()
    profiler.enable()
    result = func()
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
    return result
```

#### Database Debugging

```sql
-- Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check table sizes
SELECT schemaname, tablename, pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Check index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## 🛠️ Maintenance Procedures

### Regular Maintenance Tasks

#### Daily Tasks

```bash
# Check system health
curl -f http://localhost:8000/health

# Check database connectivity
psql -h localhost -U healthmate -d healthmate -c "SELECT 1;"

# Check Redis connectivity
redis-cli -h localhost -p 6379 ping

# Monitor log files
tail -f logs/healthmate.log | grep -E "(ERROR|CRITICAL)"
```

#### Weekly Tasks

```bash
# Database maintenance
psql -h localhost -U healthmate -d healthmate -c "VACUUM ANALYZE;"

# Log rotation
logrotate /etc/logrotate.d/healthmate

# Security updates
apt-get update && apt-get upgrade

# Backup verification
./scripts/verify_backup.sh
```

#### Monthly Tasks

```bash
# Performance analysis
./scripts/performance_analysis.sh

# Security audit
./scripts/security_audit.sh

# Compliance check
./scripts/compliance_check.sh

# Capacity planning
./scripts/capacity_analysis.sh
```

### Backup Procedures

#### Database Backup

```bash
#!/bin/bash
# scripts/backup_database.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/database"
DB_NAME="healthmate"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h localhost -U healthmate -d $DB_NAME | gzip > $BACKUP_DIR/backup_$DATE.sql.gz

# Keep only last 30 days of backups
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete

# Verify backup
gunzip -t $BACKUP_DIR/backup_$DATE.sql.gz

echo "Database backup completed: backup_$DATE.sql.gz"
```

#### Application Backup

```bash
#!/bin/bash
# scripts/backup_application.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/application"
APP_DIR="/app"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create application backup
tar -czf $BACKUP_DIR/app_backup_$DATE.tar.gz -C $APP_DIR .

# Keep only last 7 days of backups
find $BACKUP_DIR -name "app_backup_*.tar.gz" -mtime +7 -delete

echo "Application backup completed: app_backup_$DATE.tar.gz"
```

### Disaster Recovery

#### Recovery Procedures

```bash
#!/bin/bash
# scripts/disaster_recovery.sh

# 1. Stop application
docker-compose down

# 2. Restore database
gunzip -c /backups/database/backup_20240116_100000.sql.gz | psql -h localhost -U healthmate -d healthmate

# 3. Restore application
tar -xzf /backups/application/app_backup_20240116_100000.tar.gz -C /app

# 4. Run migrations
alembic upgrade head

# 5. Start application
docker-compose up -d

# 6. Verify recovery
curl -f http://localhost:8000/health
```

---

**Last Updated**: January 16, 2024  
**Documentation Version**: 1.0.0  
**Architecture Version**: 2.0.0 