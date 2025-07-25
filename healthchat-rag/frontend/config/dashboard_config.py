# Dashboard configuration for HealthChat RAG

DASHBOARD_THEME = "light"  # Options: 'light', 'dark'
CHART_COLOR_PALETTE = [
    "#2a9d8f",  # Primary
    "#e9c46a",  # Accent
    "#f4a261",  # Secondary
    "#264653",  # Dark
    "#e76f51"   # Alert
]
REFRESH_INTERVAL = 60  # seconds

DEFAULT_CHART_CONFIG = {
    "showlegend": True,
    "margin": dict(l=40, r=40, t=40, b=40),
    "plot_bgcolor": "#fff",
    "paper_bgcolor": "#fff",
    "font": dict(family="Inter, Arial, sans-serif", size=14, color="#222")
}

THEMES = {
    "light": {
        "background": "#f4f4f4",
        "text": "#222",
        "primary": "#2a9d8f",
        "secondary": "#264653",
        "accent": "#e9c46a"
    },
    "dark": {
        "background": "#222",
        "text": "#f4f4f4",
        "primary": "#2a9d8f",
        "secondary": "#264653",
        "accent": "#e9c46a"
    }
} 