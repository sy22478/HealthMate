#!/usr/bin/env python3
"""
Monitoring Setup Script for HealthMate

This script sets up comprehensive monitoring infrastructure including:
- Prometheus configuration
- Grafana dashboards and datasources
- Alerting rules
- Custom metrics collection
"""

import os
import sys
import json
import yaml
import shutil
from typing import Dict, Any, List
import argparse

class MonitoringSetup:
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.base_dir = "monitoring"
        self.grafana_dir = f"{self.base_dir}/grafana/{environment}"
        
    def create_directory_structure(self) -> None:
        """Create the monitoring directory structure."""
        directories = [
            self.base_dir,
            f"{self.base_dir}/grafana",
            f"{self.base_dir}/grafana/{self.environment}",
            f"{self.base_dir}/grafana/{self.environment}/dashboards",
            f"{self.base_dir}/grafana/{self.environment}/datasources",
            f"{self.base_dir}/alertmanager",
            f"{self.base_dir}/rules",
            f"{self.base_dir}/scripts"
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
            print(f"✅ Created directory: {directory}")
    
    def create_prometheus_config(self) -> None:
        """Create Prometheus configuration."""
        config = {
            "global": {
                "scrape_interval": "15s" if self.environment == "production" else "30s",
                "evaluation_interval": "15s" if self.environment == "production" else "30s",
                "external_labels": {
                    "cluster": f"healthmate-{self.environment}",
                    "environment": self.environment
                }
            },
            "rule_files": [
                f"{self.base_dir}/rules/healthmate_rules.yml"
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {
                                "targets": ["alertmanager:9093"]
                            }
                        ]
                    }
                ]
            },
            "scrape_configs": self._get_scrape_configs()
        }
        
        config_path = f"{self.base_dir}/prometheus.{self.environment}.yml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created Prometheus config: {config_path}")
    
    def _get_scrape_configs(self) -> List[Dict[str, Any]]:
        """Get scrape configurations based on environment."""
        base_configs = [
            {
                "job_name": "prometheus",
                "static_configs": [{"targets": ["localhost:9090"]}]
            }
        ]
        
        if self.environment == "production":
            base_configs.extend([
                {
                    "job_name": "healthmate-backend",
                    "static_configs": [{"targets": ["backend:8000"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "10s",
                    "scrape_timeout": "5s",
                    "honor_labels": True,
                    "relabel_configs": [
                        {
                            "source_labels": ["__address__"],
                            "target_label": "instance",
                            "regex": "([^:]+)(?::\d+)?",
                            "replacement": "${1}"
                        }
                    ]
                },
                {
                    "job_name": "healthmate-celery",
                    "static_configs": [{"targets": ["celery_worker:8000"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "15s",
                    "scrape_timeout": "5s",
                    "honor_labels": True
                },
                {
                    "job_name": "postgres",
                    "static_configs": [{"targets": ["postgres:5432"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "30s",
                    "scrape_timeout": "10s",
                    "honor_labels": True
                },
                {
                    "job_name": "redis",
                    "static_configs": [{"targets": ["redis:6379"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "15s",
                    "scrape_timeout": "5s",
                    "honor_labels": True
                }
            ])
        else:
            base_configs.extend([
                {
                    "job_name": "healthmate-backend-dev",
                    "static_configs": [{"targets": ["backend_dev:8000"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "30s",
                    "scrape_timeout": "10s",
                    "honor_labels": True
                },
                {
                    "job_name": "postgres-dev",
                    "static_configs": [{"targets": ["postgres_dev:5432"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "60s",
                    "scrape_timeout": "15s",
                    "honor_labels": True
                },
                {
                    "job_name": "redis-dev",
                    "static_configs": [{"targets": ["redis_dev:6379"]}],
                    "metrics_path": "/metrics",
                    "scrape_interval": "30s",
                    "scrape_timeout": "10s",
                    "honor_labels": True
                }
            ])
        
        return base_configs
    
    def create_alerting_rules(self) -> None:
        """Create Prometheus alerting rules."""
        rules = {
            "groups": [
                {
                    "name": "healthmate_alerts",
                    "rules": self._get_alert_rules()
                }
            ]
        }
        
        rules_path = f"{self.base_dir}/rules/healthmate_rules.yml"
        with open(rules_path, 'w') as f:
            yaml.dump(rules, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created alerting rules: {rules_path}")
    
    def _get_alert_rules(self) -> List[Dict[str, Any]]:
        """Get alert rules based on environment."""
        rules = [
            {
                "alert": "ApplicationDown",
                "expr": f"up{{job=\"healthmate-backend{'-dev' if self.environment != 'production' else ''}\"}} == 0",
                "for": "1m",
                "labels": {
                    "severity": "critical",
                    "service": "healthmate"
                },
                "annotations": {
                    "summary": "HealthMate application is down",
                    "description": "HealthMate backend application has been down for more than 1 minute"
                }
            },
            {
                "alert": "HighCPUUsage",
                "expr": "100 - (avg by(instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100) > 80",
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "service": "healthmate"
                },
                "annotations": {
                    "summary": "High CPU usage on {{ $labels.instance }}",
                    "description": "CPU usage is above 80% for more than 5 minutes on {{ $labels.instance }}"
                }
            },
            {
                "alert": "HighMemoryUsage",
                "expr": "(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100 > 85",
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "service": "healthmate"
                },
                "annotations": {
                    "summary": "High memory usage on {{ $labels.instance }}",
                    "description": "Memory usage is above 85% for more than 5 minutes on {{ $labels.instance }}"
                }
            },
            {
                "alert": "HighResponseTime",
                "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2",
                "for": "5m",
                "labels": {
                    "severity": "warning",
                    "service": "healthmate"
                },
                "annotations": {
                    "summary": "High response time detected",
                    "description": "95th percentile response time is above 2 seconds for more than 5 minutes"
                }
            },
            {
                "alert": "HighErrorRate",
                "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100 > 5",
                "for": "5m",
                "labels": {
                    "severity": "critical",
                    "service": "healthmate"
                },
                "annotations": {
                    "summary": "High error rate detected",
                    "description": "Error rate is above 5% for more than 5 minutes"
                }
            }
        ]
        
        if self.environment == "production":
            rules.extend([
                {
                    "alert": "DatabaseConnectionIssues",
                    "expr": "pg_stat_database_numbackends > 80",
                    "for": "2m",
                    "labels": {
                        "severity": "warning",
                        "service": "healthmate"
                    },
                    "annotations": {
                        "summary": "High database connections",
                        "description": "Number of database connections is above 80 for more than 2 minutes"
                    }
                },
                {
                    "alert": "CeleryWorkerDown",
                    "expr": "up{job=\"healthmate-celery\"} == 0",
                    "for": "2m",
                    "labels": {
                        "severity": "critical",
                        "service": "healthmate"
                    },
                    "annotations": {
                        "summary": "Celery worker is down",
                        "description": "Celery worker has been down for more than 2 minutes"
                    }
                }
            ])
        
        return rules
    
    def create_grafana_datasources(self) -> None:
        """Create Grafana datasource configuration."""
        datasources = {
            "apiVersion": 1,
            "datasources": [
                {
                    "name": "Prometheus",
                    "type": "prometheus",
                    "access": "proxy",
                    "url": "http://prometheus:9090" if self.environment == "production" else "http://prometheus_dev:9090",
                    "isDefault": True,
                    "editable": True,
                    "jsonData": {
                        "timeInterval": "15s" if self.environment == "production" else "30s",
                        "queryTimeout": "60s",
                        "httpMethod": "POST"
                    },
                    "secureJsonData": {}
                }
            ]
        }
        
        datasources_path = f"{self.grafana_dir}/datasources/prometheus.yml"
        with open(datasources_path, 'w') as f:
            yaml.dump(datasources, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created Grafana datasources: {datasources_path}")
    
    def create_grafana_dashboards_config(self) -> None:
        """Create Grafana dashboard provisioning configuration."""
        dashboards_config = {
            "apiVersion": 1,
            "providers": [
                {
                    "name": f"HealthMate {self.environment.title()} Dashboards",
                    "orgId": 1,
                    "folder": f"HealthMate {self.environment.title()}",
                    "type": "file",
                    "disableDeletion": False,
                    "updateIntervalSeconds": 30,
                    "allowUiUpdates": True,
                    "options": {
                        "path": "/etc/grafana/provisioning/dashboards"
                    }
                }
            ]
        }
        
        dashboards_config_path = f"{self.grafana_dir}/dashboards/dashboards.yml"
        with open(dashboards_config_path, 'w') as f:
            yaml.dump(dashboards_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created Grafana dashboards config: {dashboards_config_path}")
    
    def create_sample_dashboard(self) -> None:
        """Create a sample Grafana dashboard."""
        dashboard = {
            "dashboard": {
                "id": None,
                "title": f"HealthMate {self.environment.title()} Overview",
                "tags": ["healthmate", self.environment, "overview"],
                "style": "dark",
                "timezone": "browser",
                "panels": self._get_dashboard_panels(),
                "time": {
                    "from": "now-1h",
                    "to": "now"
                },
                "refresh": "30s"
            }
        }
        
        dashboard_path = f"{self.grafana_dir}/dashboards/healthmate-overview.json"
        with open(dashboard_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        print(f"✅ Created sample dashboard: {dashboard_path}")
    
    def _get_dashboard_panels(self) -> List[Dict[str, Any]]:
        """Get dashboard panels based on environment."""
        job_suffix = "-dev" if self.environment != "production" else ""
        
        panels = [
            {
                "id": 1,
                "title": "Application Health Status",
                "type": "stat",
                "targets": [
                    {
                        "expr": f"up{{job=\"healthmate-backend{job_suffix}\"}}",
                        "legendFormat": "{{instance}}"
                    }
                ],
                "fieldConfig": {
                    "defaults": {
                        "color": {"mode": "thresholds"},
                        "thresholds": {
                            "steps": [
                                {"color": "red", "value": 0},
                                {"color": "green", "value": 1}
                            ]
                        },
                        "mappings": [
                            {"options": {"0": {"text": "DOWN"}}, "type": "value"},
                            {"options": {"1": {"text": "UP"}}, "type": "value"}
                        ]
                    }
                },
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
            },
            {
                "id": 2,
                "title": "Request Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(http_requests_total[5m])",
                        "legendFormat": "{{method}} {{endpoint}}"
                    }
                ],
                "yAxes": [{"label": "Requests/sec", "min": 0}],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
            },
            {
                "id": 3,
                "title": "Response Time (95th percentile)",
                "type": "graph",
                "targets": [
                    {
                        "expr": "histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))",
                        "legendFormat": "{{method}} {{endpoint}}"
                    }
                ],
                "yAxes": [{"label": "Seconds", "min": 0}],
                "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
            },
            {
                "id": 4,
                "title": "Error Rate",
                "type": "graph",
                "targets": [
                    {
                        "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m]) * 100",
                        "legendFormat": "{{method}} {{endpoint}}"
                    }
                ],
                "yAxes": [{"label": "Error %", "min": 0}],
                "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
            }
        ]
        
        return panels
    
    def create_alertmanager_config(self) -> None:
        """Create Alertmanager configuration."""
        config = {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": "alertmanager@healthmate.com"
            },
            "route": {
                "group_by": ["alertname", "cluster", "service"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "healthmate-team"
            },
            "receivers": [
                {
                    "name": "healthmate-team",
                    "email_configs": [
                        {
                            "to": "alerts@healthmate.com",
                            "send_resolved": True
                        }
                    ],
                    "webhook_configs": [
                        {
                            "url": "http://webhook:5000/alert",
                            "send_resolved": True
                        }
                    ]
                }
            ]
        }
        
        config_path = f"{self.base_dir}/alertmanager/alertmanager.yml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created Alertmanager config: {config_path}")
    
    def create_custom_metrics_collector(self) -> None:
        """Create custom metrics collector script."""
        metrics_collector = '''
"""
Custom Metrics Collector for HealthMate

This script collects custom business metrics and exposes them to Prometheus.
"""

import time
import psutil
import redis
import psycopg2
from prometheus_client import start_http_server, Gauge, Counter, Histogram
import logging

logger = logging.getLogger(__name__)

# Custom metrics
ACTIVE_USERS = Gauge('healthmate_active_users_total', 'Number of active users')
HEALTH_DATA_POINTS = Counter('healthmate_health_data_points_total', 'Total health data points processed')
API_REQUESTS = Counter('healthmate_api_requests_total', 'Total API requests', ['method', 'endpoint', 'status'])
RESPONSE_TIME = Histogram('healthmate_response_time_seconds', 'Response time in seconds', ['method', 'endpoint'])
DATABASE_CONNECTIONS = Gauge('healthmate_database_connections', 'Number of database connections')
REDIS_MEMORY_USAGE = Gauge('healthmate_redis_memory_bytes', 'Redis memory usage in bytes')
CELERY_QUEUE_LENGTH = Gauge('healthmate_celery_queue_length', 'Celery queue length', ['queue'])

class MetricsCollector:
    def __init__(self, db_url: str, redis_url: str):
        self.db_url = db_url
        self.redis_url = redis_url
        
    def collect_system_metrics(self):
        """Collect system-level metrics."""
        try:
            # CPU and memory usage
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            
            # Database connections
            conn = psycopg2.connect(self.db_url)
            cursor = conn.cursor()
            cursor.execute("SELECT count(*) FROM pg_stat_activity")
            db_connections = cursor.fetchone()[0]
            DATABASE_CONNECTIONS.set(db_connections)
            cursor.close()
            conn.close()
            
            # Redis metrics
            r = redis.from_url(self.redis_url)
            redis_info = r.info()
            REDIS_MEMORY_USAGE.set(redis_info['used_memory'])
            
            logger.info(f"Collected system metrics - CPU: {cpu_percent}%, Memory: {memory.percent}%")
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
    
    def collect_business_metrics(self):
        """Collect business-specific metrics."""
        try:
            # This would typically query your application database
            # For now, we'll use placeholder values
            ACTIVE_USERS.set(100)  # Placeholder
            HEALTH_DATA_POINTS.inc(10)  # Increment by 10
            
            logger.info("Collected business metrics")
            
        except Exception as e:
            logger.error(f"Error collecting business metrics: {e}")
    
    def start_collection(self, port: int = 8001):
        """Start the metrics collection server."""
        start_http_server(port)
        logger.info(f"Metrics server started on port {port}")
        
        while True:
            self.collect_system_metrics()
            self.collect_business_metrics()
            time.sleep(15)  # Collect metrics every 15 seconds

if __name__ == "__main__":
    import os
    
    db_url = os.getenv("HEALTHMATE_POSTGRES_URI")
    redis_url = os.getenv("HEALTHMATE_REDIS_URL")
    
    if not db_url or not redis_url:
        logger.error("Database or Redis URL not provided")
        sys.exit(1)
    
    collector = MetricsCollector(db_url, redis_url)
    collector.start_collection()
'''
        
        collector_path = f"{self.base_dir}/scripts/metrics_collector.py"
        with open(collector_path, 'w') as f:
            f.write(metrics_collector)
        
        print(f"✅ Created metrics collector: {collector_path}")
    
    def create_docker_compose_monitoring(self) -> None:
        """Create Docker Compose file for monitoring stack."""
        services = {
            "prometheus": {
                "image": "prom/prometheus:latest",
                "container_name": f"healthmate_prometheus_{self.environment}",
                "volumes": [
                    f"./{self.base_dir}/prometheus.{self.environment}.yml:/etc/prometheus/prometheus.yml:ro",
                    f"./{self.base_dir}/rules:/etc/prometheus/rules:ro",
                    "prometheus_data:/prometheus"
                ],
                "command": [
                    "--config.file=/etc/prometheus/prometheus.yml",
                    "--storage.tsdb.path=/prometheus",
                    "--web.console.libraries=/etc/prometheus/console_libraries",
                    "--web.console.templates=/etc/prometheus/consoles",
                    "--storage.tsdb.retention.time=200h",
                    "--web.enable-lifecycle"
                ],
                "ports": [f"{'9091' if self.environment != 'production' else '9090'}:9090"],
                "networks": [f"healthmate_{self.environment}_network"],
                "restart": "unless-stopped"
            },
            "grafana": {
                "image": "grafana/grafana:latest",
                "container_name": f"healthmate_grafana_{self.environment}",
                "environment": {
                    "GF_SECURITY_ADMIN_PASSWORD": "admin" if self.environment != "production" else "${GRAFANA_PASSWORD}",
                    "GF_USERS_ALLOW_SIGN_UP": "true" if self.environment != "production" else "false"
                },
                "volumes": [
                    "grafana_data:/var/lib/grafana",
                    f"./{self.grafana_dir}/dashboards:/etc/grafana/provisioning/dashboards:ro",
                    f"./{self.grafana_dir}/datasources:/etc/grafana/provisioning/datasources:ro"
                ],
                "ports": [f"{'3001' if self.environment != 'production' else '3000'}:3000"],
                "networks": [f"healthmate_{self.environment}_network"],
                "restart": "unless-stopped"
            }
        }
        
        if self.environment == "production":
            services["alertmanager"] = {
                "image": "prom/alertmanager:latest",
                "container_name": "healthmate_alertmanager",
                "volumes": [
                    f"./{self.base_dir}/alertmanager:/etc/alertmanager:ro",
                    "alertmanager_data:/alertmanager"
                ],
                "command": [
                    "--config.file=/etc/alertmanager/alertmanager.yml",
                    "--storage.path=/alertmanager"
                ],
                "ports": ["9093:9093"],
                "networks": [f"healthmate_{self.environment}_network"],
                "restart": "unless-stopped"
            }
        
        compose_config = {
            "version": "3.8",
            "services": services,
            "volumes": {
                "prometheus_data": {"driver": "local"},
                "grafana_data": {"driver": "local"}
            },
            "networks": {
                f"healthmate_{self.environment}_network": {"driver": "bridge"}
            }
        }
        
        if self.environment == "production":
            compose_config["volumes"]["alertmanager_data"] = {"driver": "local"}
        
        compose_path = f"{self.base_dir}/docker-compose.monitoring.{self.environment}.yml"
        with open(compose_path, 'w') as f:
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
        
        print(f"✅ Created monitoring Docker Compose: {compose_path}")
    
    def setup_monitoring(self) -> bool:
        """Complete monitoring setup process."""
        print(f"🚀 Setting up monitoring for HealthMate ({self.environment})...")
        
        try:
            self.create_directory_structure()
            self.create_prometheus_config()
            self.create_alerting_rules()
            self.create_grafana_datasources()
            self.create_grafana_dashboards_config()
            self.create_sample_dashboard()
            self.create_custom_metrics_collector()
            
            if self.environment == "production":
                self.create_alertmanager_config()
            
            self.create_docker_compose_monitoring()
            
            print(f"\n🎉 Monitoring setup completed for {self.environment} environment!")
            print("\n📋 Next steps:")
            print("1. Start the monitoring stack:")
            print(f"   docker-compose -f {self.base_dir}/docker-compose.monitoring.{self.environment}.yml up -d")
            print("2. Access Grafana at http://localhost:3000 (admin/admin)")
            print("3. Access Prometheus at http://localhost:9090")
            if self.environment == "production":
                print("4. Access Alertmanager at http://localhost:9093")
            print("5. Configure your application to expose metrics at /metrics endpoint")
            print("6. Import the sample dashboard in Grafana")
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to setup monitoring: {e}")
            return False

def main():
    parser = argparse.ArgumentParser(description="Setup monitoring for HealthMate")
    parser.add_argument("--environment", choices=["production", "development"], 
                       default="production", help="Environment to setup monitoring for")
    
    args = parser.parse_args()
    
    monitoring_setup = MonitoringSetup(args.environment)
    success = monitoring_setup.setup_monitoring()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 