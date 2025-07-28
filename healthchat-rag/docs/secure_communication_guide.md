# Secure Communication Guide

This guide covers the secure communication features implemented in HealthMate, including HTTPS/TLS enforcement, CORS configuration, security headers, and request/response validation.

## Table of Contents

1. [Overview](#overview)
2. [HTTPS/TLS Configuration](#https-tls-configuration)
3. [CORS Configuration](#cors-configuration)
4. [Security Headers](#security-headers)
5. [Request/Response Validation](#request-response-validation)
6. [Environment Configuration](#environment-configuration)
7. [Testing](#testing)
8. [Production Deployment](#production-deployment)
9. [Troubleshooting](#troubleshooting)

## Overview

The secure communication system in HealthMate provides comprehensive protection for API endpoints through:

- **HTTPS/TLS Enforcement**: Automatic redirection to HTTPS in production
- **Security Headers**: Protection against common web vulnerabilities
- **CORS Configuration**: Controlled cross-origin resource sharing
- **Request/Response Validation**: Data integrity and consistency
- **HSTS**: HTTP Strict Transport Security for enhanced security

## HTTPS/TLS Configuration

### Development Setup

For local development with HTTPS:

1. **Generate SSL certificates**:
   ```bash
   cd healthchat-rag
   python scripts/generate_ssl_cert.py
   ```

2. **Update environment variables**:
   ```bash
   # Add to .env file
   HEALTHMATE_SSL_KEYFILE=ssl/key.pem
   HEALTHMATE_SSL_CERTFILE=ssl/cert.pem
   ```

3. **Run with SSL**:
   ```bash
   uvicorn app.main:app --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem
   ```

### Production Setup

For production environments, use a reverse proxy (recommended):

1. **Nginx Configuration**:
   ```bash
   # Generate nginx config
   python scripts/generate_ssl_cert.py
   # Copy nginx-ssl.conf to your nginx sites-available
   ```

2. **Environment Variables**:
   ```bash
   HEALTHMATE_ENVIRONMENT=production
   HEALTHMATE_SSL_KEYFILE=/path/to/production/key.pem
   HEALTHMATE_SSL_CERTFILE=/path/to/production/cert.pem
   ```

### SSL Certificate Management

#### Self-Signed Certificates (Development)
```bash
# Generate development certificates
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem -out ssl/cert.pem \
  -subj "/CN=localhost"
```

#### Let's Encrypt (Production)
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## CORS Configuration

### Environment Variables

Configure CORS through environment variables:

```bash
# Allow all origins (development only)
HEALTHMATE_CORS_ALLOW_ORIGINS="*"

# Restrict to specific domains (production)
HEALTHMATE_CORS_ALLOW_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Additional CORS settings
HEALTHMATE_CORS_ALLOW_CREDENTIALS=true
HEALTHMATE_CORS_ALLOW_METHODS="GET,POST,PUT,DELETE,OPTIONS"
HEALTHMATE_CORS_ALLOW_HEADERS="Content-Type,Authorization"
HEALTHMATE_CORS_EXPOSE_HEADERS="X-Total-Count"
HEALTHMATE_CORS_MAX_AGE=600
```

### Security Considerations

- **Never use `*` in production** for `CORS_ALLOW_ORIGINS`
- **Be specific about allowed methods** and headers
- **Use HTTPS origins** in production
- **Consider credentials carefully** when allowing cross-origin requests

## Security Headers

The application automatically adds the following security headers:

### HSTS (HTTP Strict Transport Security)
```
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

### Content Security Policy
```
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';
```

### XSS Protection
```
X-XSS-Protection: 1; mode=block
```

### Frame Options
```
X-Frame-Options: DENY
```

### Content Type Options
```
X-Content-Type-Options: nosniff
```

### Referrer Policy
```
Referrer-Policy: strict-origin-when-cross-origin
```

### Additional Headers
```
X-Permitted-Cross-Domain-Policies: none
X-Download-Options: noopen
X-DNS-Prefetch-Control: off
```

## Request/Response Validation

### Automatic Validation

The application includes middleware for automatic request/response validation:

- **Request validation**: Validates incoming data against Pydantic schemas
- **Response validation**: Ensures consistent response format
- **Error handling**: Standardized error responses for validation failures

### Custom Validation

Add custom validation to endpoints:

```python
from app.utils.request_response_validation import validate_request_body, validate_response
from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    email: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

@validate_request_body(UserCreate)
@validate_response(UserResponse)
async def create_user(user_data: UserCreate):
    # Your logic here
    pass
```

## Environment Configuration

### Development Environment

```bash
# .env file for development
HEALTHMATE_ENVIRONMENT=development
HEALTHMATE_DEBUG=true
HEALTHMATE_CORS_ALLOW_ORIGINS="*"
HEALTHMATE_SECURITY_HEADERS_ENABLED=true
HEALTHMATE_RATE_LIMIT_ENABLED=false
HEALTHMATE_REQUEST_VALIDATION_ENABLED=true
HEALTHMATE_RESPONSE_VALIDATION_ENABLED=true
```

### Production Environment

```bash
# .env file for production
HEALTHMATE_ENVIRONMENT=production
HEALTHMATE_DEBUG=false
HEALTHMATE_CORS_ALLOW_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"
HEALTHMATE_SECURITY_HEADERS_ENABLED=true
HEALTHMATE_HSTS_MAX_AGE=31536000
HEALTHMATE_HSTS_INCLUDE_SUBDOMAINS=true
HEALTHMATE_CONTENT_SECURITY_POLICY="default-src 'self'; script-src 'self'; style-src 'self';"
HEALTHMATE_RATE_LIMIT_ENABLED=true
HEALTHMATE_RATE_LIMIT_REQUESTS_PER_MINUTE=60
HEALTHMATE_RATE_LIMIT_REQUESTS_PER_HOUR=1000
```

## Testing

### Run Security Tests

```bash
# Run all security tests
pytest healthchat-rag/tests/test_secure_communication.py -v

# Run specific test categories
pytest healthchat-rag/tests/test_secure_communication.py::TestSecurityMiddleware -v
pytest healthchat-rag/tests/test_secure_communication.py::TestCORSConfiguration -v
pytest healthchat-rag/tests/test_secure_communication.py::TestSecurityHeaders -v
```

### Manual Testing

1. **Test HTTPS enforcement**:
   ```bash
   # Should redirect to HTTPS in production
   curl -I http://localhost:8000/api/endpoint
   ```

2. **Test CORS headers**:
   ```bash
   # Check CORS headers
   curl -H "Origin: http://localhost:3000" -I http://localhost:8000/
   ```

3. **Test security headers**:
   ```bash
   # Check security headers
   curl -I http://localhost:8000/
   ```

4. **Test health endpoint**:
   ```bash
   # Health check
   curl http://localhost:8000/health
   ```

5. **Test security info**:
   ```bash
   # Security configuration info
   curl http://localhost:8000/security-info
   ```

## Production Deployment

### Docker Deployment

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# Create SSL directory
RUN mkdir -p /app/ssl

# Expose ports
EXPOSE 8000 443

# Run with SSL
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--ssl-keyfile", "/app/ssl/key.pem", "--ssl-certfile", "/app/ssl/cert.pem"]
```

### Kubernetes Deployment

```yaml
# deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: healthmate-api
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
        - name: HEALTHMATE_ENVIRONMENT
          value: "production"
        - name: HEALTHMATE_CORS_ALLOW_ORIGINS
          value: "https://yourdomain.com"
        volumeMounts:
        - name: ssl-certs
          mountPath: /app/ssl
      volumes:
      - name: ssl-certs
        secret:
          secretName: ssl-certificates
```

### Load Balancer Configuration

```yaml
# ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: healthmate-ingress
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - yourdomain.com
    secretName: healthmate-tls
  rules:
  - host: yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: healthmate-service
            port:
              number: 8000
```

## Troubleshooting

### Common Issues

#### SSL Certificate Errors
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout

# Check certificate dates
openssl x509 -in ssl/cert.pem -noout -dates
```

#### CORS Issues
```bash
# Check CORS configuration
curl -H "Origin: https://yourdomain.com" -H "Access-Control-Request-Method: POST" -H "Access-Control-Request-Headers: Content-Type" -X OPTIONS http://localhost:8000/api/endpoint
```

#### Security Header Issues
```bash
# Check security headers
curl -I http://localhost:8000/ | grep -E "(X-|Strict-|Content-Security)"
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
HEALTHMATE_DEBUG=true
HEALTHMATE_LOG_LEVEL=DEBUG
```

### Log Analysis

```bash
# Check application logs
tail -f logs/healthmate.log | grep -E "(SECURITY|CORS|SSL)"

# Check nginx logs (if using reverse proxy)
tail -f /var/log/nginx/access.log | grep healthmate
tail -f /var/log/nginx/error.log | grep healthmate
```

### Performance Monitoring

Monitor security-related metrics:

```bash
# Check response times with security headers
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/

# Monitor SSL handshake times
openssl s_time -connect localhost:443 -new
```

## Security Best Practices

1. **Always use HTTPS in production**
2. **Regularly update SSL certificates**
3. **Monitor security headers**
4. **Restrict CORS origins**
5. **Use strong CSP policies**
6. **Enable HSTS**
7. **Monitor for security vulnerabilities**
8. **Regular security audits**

## Compliance

The secure communication features help meet various compliance requirements:

- **HIPAA**: Data encryption in transit
- **GDPR**: Secure data transmission
- **SOC 2**: Security controls
- **PCI DSS**: Secure communication protocols

For specific compliance requirements, consult with your security team and legal advisors. 