"""
HealthMate Dashboard Configuration
Configuration settings for the frontend dashboard
"""
import os
from typing import Dict, Any

class DashboardConfig:
    """Configuration class for HealthMate Dashboard"""
    
    # API Configuration
    API_BASE_URL = os.getenv("HEALTHMATE_API_URL", "https://healthmate-production.up.railway.app")
    API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))
    
    # Dashboard Configuration
    DASHBOARD_TITLE = "HealthMate Dashboard"
    DASHBOARD_ICON = "🏥"
    DASHBOARD_LAYOUT = "wide"
    
    # Chart Configuration
    CHART_HEIGHT = 400
    CHART_WIDTH = "100%"
    CHART_COLORS = {
        "primary": "#1f77b4",
        "secondary": "#ff7f0e",
        "success": "#2ca02c",
        "warning": "#d62728",
        "info": "#9467bd",
        "light": "#8c564b",
        "dark": "#e377c2"
    }
    
    # Data Configuration
    DEFAULT_DAYS_FILTER = 30
    MAX_DAYS_FILTER = 365
    MIN_DAYS_FILTER = 7
    
    # Authentication Configuration
    SESSION_TIMEOUT = int(os.getenv("SESSION_TIMEOUT", "3600"))  # 1 hour
    REFRESH_TOKEN_INTERVAL = int(os.getenv("REFRESH_TOKEN_INTERVAL", "300"))  # 5 minutes
    
    # Export Configuration
    EXPORT_FORMATS = ["csv", "json", "excel"]
    MAX_EXPORT_RECORDS = 10000
    
    # Visualization Configuration
    AVAILABLE_CHARTS = [
        {
            "type": "health_trends",
            "name": "Health Trends Over Time",
            "description": "Line chart showing health data trends",
            "category": "trends",
            "icon": "📈"
        },
        {
            "type": "symptom_distribution",
            "name": "Symptom Distribution",
            "description": "Pie chart showing symptom frequency and severity",
            "category": "symptoms",
            "icon": "🤒"
        },
        {
            "type": "medication_adherence",
            "name": "Medication Adherence",
            "description": "Line chart showing medication adherence over time",
            "category": "medications",
            "icon": "💊"
        },
        {
            "type": "data_completeness",
            "name": "Data Completeness",
            "description": "Doughnut chart showing data completeness by type",
            "category": "overview",
            "icon": "📊"
        },
        {
            "type": "health_score_timeline",
            "name": "Health Score Timeline",
            "description": "Line chart showing health score over time",
            "category": "overview",
            "icon": "🏥"
        },
        {
            "type": "correlation_matrix",
            "name": "Health Data Correlations",
            "description": "Heatmap showing correlations between health data types",
            "category": "analytics",
            "icon": "🔗"
        }
    ]
    
    # Health Score Configuration
    HEALTH_SCORE_WEIGHTS = {
        "vital_signs": 0.25,
        "symptoms": 0.20,
        "medication_adherence": 0.20,
        "lifestyle": 0.15,
        "lab_results": 0.20
    }
    
    # Alert Configuration
    ALERT_THRESHOLDS = {
        "health_score_low": 50,
        "health_score_medium": 70,
        "medication_adherence_low": 80,
        "symptom_severity_high": 7,
        "data_completeness_low": 60
    }
    
    # UI Configuration
    UI_THEME = {
        "primaryColor": "#1f77b4",
        "backgroundColor": "#ffffff",
        "secondaryBackgroundColor": "#f0f2f6",
        "textColor": "#262730",
        "font": "sans serif"
    }
    
    # Performance Configuration
    CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes
    MAX_CONCURRENT_REQUESTS = int(os.getenv("MAX_CONCURRENT_REQUESTS", "10"))
    
    @classmethod
    def get_chart_config(cls, chart_type: str) -> Dict[str, Any]:
        """Get configuration for specific chart type"""
        for chart in cls.AVAILABLE_CHARTS:
            if chart["type"] == chart_type:
                return chart
        return {}
    
    @classmethod
    def get_charts_by_category(cls, category: str) -> list:
        """Get charts filtered by category"""
        return [chart for chart in cls.AVAILABLE_CHARTS if chart["category"] == category]
    
    @classmethod
    def get_all_categories(cls) -> list:
        """Get all available chart categories"""
        return list(set(chart["category"] for chart in cls.AVAILABLE_CHARTS)) 