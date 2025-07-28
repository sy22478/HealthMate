# Phase 5.2: Scalability & Deployment - Implementation Guide

This guide covers the complete implementation of Phase 5.2: Scalability & Deployment for the HealthMate application, including containerization, orchestration, monitoring, and observability.

## Table of Contents

1. [Overview](#overview)
2. [Containerization & Orchestration](#containerization--orchestration)
3. [Monitoring & Observability](#monitoring--observability)
4. [Development Environment](#development-environment)
5. [Production Deployment](#production-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [Monitoring Setup](#monitoring-setup)
8. [Alerting Configuration](#alerting-configuration)
9. [Performance Optimization](#performance-optimization)
10. [Troubleshooting](#troubleshooting)

## Overview

Phase 5.2 focuses on making the HealthMate application production-ready with comprehensive monitoring, observability, and scalable deployment capabilities. This phase includes:

- ✅ Docker containerization with multi-stage builds
- ✅ Development and production Docker Compose configurations
- ✅ Kubernetes deployment configurations
- ✅ Prometheus metrics collection
- ✅ Grafana dashboards and visualization
- ✅ Alerting and notification systems
- ✅ Performance monitoring and optimization

## Containerization & Orchestration

### Docker Configuration

#### Production Dockerfile
The production Dockerfile (`Dockerfile`) uses multi-stage builds for optimization:

```dockerfile
# Multi-stage Dockerfile for HealthMate Backend
FROM python:3.11-slim as builder
# Build stage with dependencies
FROM python:3.11-slim as production
# Production stage with minimal footprint
```

#### Development Dockerfile
The development Dockerfile (`Dockerfile.dev`) includes debugging tools and hot reloading:

```dockerfile
# Development stage with debugging tools
FROM python:3.11-slim as development
# Includes debugpy, ipython, pytest, and development tools
```

### Docker Compose Configurations

#### Production Environment (`docker-compose.prod.yml`)
- PostgreSQL database with health checks
- Redis cache with persistence
- HealthMate backend API
- Nginx reverse proxy with SSL
- Prometheus monitoring
- Grafana dashboards
- Celery workers for background tasks

#### Development Environment (`docker-compose.dev.yml`)
- Development database and cache
- Hot reloading backend
- Development monitoring stack
- Mailhog for email testing
- Relaxed rate limiting for development

## Monitoring & Observability

### Prometheus Configuration

#### Production Prometheus (`monitoring/prometheus.yml`)
- 15-second scrape intervals
- Comprehensive service monitoring
- Kubernetes integration
- Custom metrics collection

#### Development Prometheus (`monitoring/prometheus.dev.yml`)
- 30-second scrape intervals
- Simplified monitoring for development
- Basic service coverage

### Grafana Dashboards

#### Production Dashboard (`monitoring/grafana/prod/dashboards/healthmate-overview.json`)
- Application health status
- Request rate and response time
- Error rate monitoring
- System resource usage
- Database and Redis metrics
- Custom business metrics

#### Development Dashboard (`monitoring/grafana/dev/dashboards/healthmate-dev-overview.json`)
- Simplified metrics for development
- Basic application monitoring
- Development-specific visualizations

### Alerting Rules

Comprehensive alerting rules in `monitoring/healthmate_rules.yml`:

- **Application Health**: Service down detection
- **Performance**: High CPU, memory, and response time
- **Errors**: High error rates and failed requests
- **Infrastructure**: Database connections, Redis issues
- **Business Metrics**: Custom application metrics

## Development Environment

### Quick Start

1. **Clone and setup**:
```bash
cd healthchat-rag
```

2. **Start development environment**:
```bash
docker-compose -f docker-compose.dev.yml up -d
```

3. **Access services**:
- Backend API: http://localhost:8000
- Grafana: http://localhost:3001 (admin/admin)
- Prometheus: http://localhost:9091
- Mailhog: http://localhost:8025

4. **View logs**:
```bash
docker-compose -f docker-compose.dev.yml logs -f backend_dev
```

### Development Features

- **Hot Reloading**: Code changes automatically restart the server
- **Debugging**: Integrated debugging tools and breakpoints
- **Testing**: Automated test suite with pytest
- **Monitoring**: Real-time metrics and dashboards
- **Email Testing**: Mailhog for email functionality testing

## Production Deployment

### Environment Setup

1. **Create environment file**:
```bash
cp .env.example .env.prod
# Edit .env.prod with production values
```

2. **Generate SSL certificates**:
```bash
python scripts/generate_ssl_cert.py
```

3. **Start production stack**:
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Production Features

- **SSL/TLS**: Secure communication with Let's Encrypt
- **Load Balancing**: Nginx with rate limiting and caching
- **Health Checks**: Comprehensive health monitoring
- **Logging**: Structured logging with correlation IDs
- **Security**: Non-root containers and security headers

## Kubernetes Deployment

### Deployment Configuration

The Kubernetes deployment (`k8s/deployment.yaml`) includes:

- **Horizontal Pod Autoscaler**: Automatic scaling based on CPU/memory
- **Rolling Updates**: Zero-downtime deployments
- **Health Checks**: Liveness and readiness probes
- **Resource Limits**: CPU and memory constraints
- **Security**: Non-root containers and security contexts

### Auto-scaling Policies

Comprehensive auto-scaling configuration (`k8s/autoscaling-policies.yaml`):

- **Application Scaling**: CPU/memory-based scaling
- **Database Scaling**: Read replica auto-scaling
- **Redis Scaling**: Cluster auto-scaling
- **Vertical Scaling**: Resource optimization

### Deployment Commands

```bash
# Create namespace
kubectl create namespace healthmate

# Apply configurations
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/autoscaling-policies.yaml
kubectl apply -f k8s/database-replicas.yaml

# Check deployment status
kubectl get pods -n healthmate
kubectl get hpa -n healthmate
```

## Monitoring Setup

### Automated Setup

Use the monitoring setup script:

```bash
# Production monitoring
python scripts/setup_monitoring.py --environment production

# Development monitoring
python scripts/setup_monitoring.py --environment development
```

### Manual Setup

1. **Prometheus Configuration**:
```bash
# Copy configuration
cp monitoring/prometheus.yml /etc/prometheus/
# Restart Prometheus
systemctl restart prometheus
```

2. **Grafana Configuration**:
```bash
# Copy dashboards and datasources
cp -r monitoring/grafana/prod/* /etc/grafana/provisioning/
# Restart Grafana
systemctl restart grafana-server
```

3. **Alerting Rules**:
```bash
# Copy alerting rules
cp monitoring/healthmate_rules.yml /etc/prometheus/rules/
# Reload Prometheus configuration
curl -X POST http://localhost:9090/-/reload
```

### Custom Metrics

The application exposes custom metrics at `/metrics`:

- **Business Metrics**: Active users, health data points
- **Performance Metrics**: Response times, request rates
- **System Metrics**: Database connections, Redis usage
- **Error Metrics**: Error rates, failed requests

## Alerting Configuration

### Alertmanager Setup

1. **Install Alertmanager**:
```bash
# Using Docker
docker run -d --name alertmanager \
  -p 9093:9093 \
  -v $(pwd)/monitoring/alertmanager:/etc/alertmanager \
  prom/alertmanager
```

2. **Configure Notifications**:
Edit `monitoring/alertmanager/alertmanager.yml`:
```yaml
receivers:
  - name: healthmate-team
    email_configs:
      - to: alerts@healthmate.com
    webhook_configs:
      - url: http://webhook:5000/alert
```

### Alert Rules

Key alerting rules include:

- **Critical Alerts**: Application down, high error rates
- **Warning Alerts**: High resource usage, slow response times
- **Info Alerts**: Certificate expiry, maintenance windows

## Performance Optimization

### Database Optimization

1. **Connection Pooling**:
```python
# Configure SQLAlchemy connection pool
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True
)
```

2. **Query Optimization**:
- Add database indexes for common queries
- Use query result caching
- Implement database read replicas

### Caching Strategy

1. **Redis Configuration**:
```python
# Configure Redis with connection pooling
redis_client = redis.from_url(
    REDIS_URL,
    max_connections=50,
    retry_on_timeout=True
)
```

2. **Cache Invalidation**:
- Time-based cache expiration
- Event-driven cache invalidation
- Cache warming strategies

### Load Balancing

1. **Nginx Configuration**:
```nginx
upstream healthmate_backend {
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
    keepalive 32;
}
```

2. **Health Checks**:
- Active health checks
- Passive health checks
- Circuit breaker patterns

## Troubleshooting

### Common Issues

1. **Container Won't Start**:
```bash
# Check logs
docker logs <container_name>

# Check resource usage
docker stats

# Verify environment variables
docker exec <container_name> env
```

2. **Database Connection Issues**:
```bash
# Test database connectivity
docker exec <container_name> python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Connected successfully')
"
```

3. **Monitoring Issues**:
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Grafana datasources
curl http://localhost:3000/api/datasources

# Verify metrics endpoint
curl http://localhost:8000/metrics
```

### Performance Debugging

1. **Slow Response Times**:
```bash
# Check database queries
docker exec postgres psql -U healthmate_user -d healthmate -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"
```

2. **High Memory Usage**:
```bash
# Check memory usage
docker stats --no-stream

# Analyze memory usage in Python
docker exec <container_name> python -c "
import psutil
print(f'Memory usage: {psutil.virtual_memory().percent}%')
"
```

3. **High CPU Usage**:
```bash
# Check CPU usage by process
docker exec <container_name> top

# Profile Python code
docker exec <container_name> python -m cProfile -o profile.stats app/main.py
```

### Log Analysis

1. **Structured Logging**:
```bash
# Search for errors
docker logs <container_name> | grep ERROR

# Search by correlation ID
docker logs <container_name> | grep "correlation_id=abc123"

# Search by time range
docker logs <container_name> --since "2024-01-01T00:00:00"
```

2. **Log Aggregation**:
```bash
# Using ELK stack
# Configure logstash to parse application logs
# Create Kibana dashboards for log analysis
```

## Security Considerations

### Container Security

1. **Non-root Containers**:
```dockerfile
# Create non-root user
RUN groupadd -r healthmate && useradd -r -g healthmate healthmate
USER healthmate
```

2. **Security Scanning**:
```bash
# Scan for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image healthmate/backend:latest
```

3. **Secrets Management**:
```bash
# Use Kubernetes secrets
kubectl create secret generic healthmate-secrets \
  --from-literal=postgres-uri="$POSTGRES_URI" \
  --from-literal=redis-url="$REDIS_URL"
```

### Network Security

1. **Network Policies**:
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: healthmate-network-policy
spec:
  podSelector:
    matchLabels:
      app: healthmate-backend
  policyTypes:
  - Ingress
  - Egress
```

2. **TLS Configuration**:
```nginx
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
ssl_prefer_server_ciphers off;
```

## Backup and Recovery

### Database Backup

1. **Automated Backups**:
```bash
#!/bin/bash
# Daily backup script
pg_dump -h localhost -U healthmate_user healthmate > backup_$(date +%Y%m%d).sql
```

2. **Point-in-time Recovery**:
```bash
# Enable WAL archiving
# Configure continuous archiving
# Test recovery procedures
```

### Application Backup

1. **Configuration Backup**:
```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz \
  monitoring/ k8s/ docker-compose*.yml
```

2. **Disaster Recovery**:
```bash
# Create recovery playbook
# Test recovery procedures
# Document recovery steps
```

## Conclusion

Phase 5.2 provides a comprehensive, production-ready deployment infrastructure for the HealthMate application. The implementation includes:

- **Scalable Architecture**: Containerized application with auto-scaling
- **Comprehensive Monitoring**: Prometheus metrics, Grafana dashboards, and alerting
- **Development Tools**: Hot reloading, debugging, and testing capabilities
- **Security**: Non-root containers, SSL/TLS, and network policies
- **Performance**: Optimized database queries, caching, and load balancing
- **Observability**: Structured logging, metrics collection, and tracing

The system is now ready for production deployment with enterprise-grade monitoring, alerting, and scalability features.

## Next Steps

1. **Deploy to Production**: Use the provided configurations to deploy to production
2. **Monitor Performance**: Use Grafana dashboards to monitor application performance
3. **Set up Alerting**: Configure alerting rules and notification channels
4. **Scale Infrastructure**: Add more resources as needed based on monitoring data
5. **Optimize Performance**: Use monitoring data to identify and fix performance bottlenecks 