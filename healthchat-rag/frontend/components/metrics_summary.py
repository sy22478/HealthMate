import streamlit as st
import random

def metrics_summary_cards():
    st.markdown("### Current Metrics Overview")
    
    # Sample latest readings
    latest_metrics = [
        {
            "name": "Blood Pressure",
            "value": "135/85",
            "unit": "mmHg",
            "status": "Elevated",
            "trend": "up",
            "normal_range": "120/80",
            "color": "#e76f51"
        },
        {
            "name": "Heart Rate",
            "value": "72",
            "unit": "bpm",
            "status": "Normal",
            "trend": "stable",
            "normal_range": "60-100",
            "color": "#2a9d8f"
        },
        {
            "name": "Weight",
            "value": "150.2",
            "unit": "lbs",
            "status": "Normal",
            "trend": "down",
            "normal_range": "140-160",
            "color": "#e9c46a"
        },
        {
            "name": "Temperature",
            "value": "98.6",
            "unit": "°F",
            "status": "Normal",
            "trend": "stable",
            "normal_range": "97-99",
            "color": "#264653"
        }
    ]
    
    # Display metrics cards
    cols = st.columns(len(latest_metrics))
    for i, metric in enumerate(latest_metrics):
        with cols[i]:
            # Determine trend icon
            if metric["trend"] == "up":
                trend_icon = "📈"
            elif metric["trend"] == "down":
                trend_icon = "📉"
            else:
                trend_icon = "➡️"
            
            # Determine status color
            if metric["status"] == "Normal":
                status_color = "#2a9d8f"
            elif metric["status"] == "Elevated":
                status_color = "#e76f51"
            else:
                status_color = "#e9c46a"
            
            st.markdown(f"""
            <div style='background: #fff; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border-left: 4px solid {metric['color']};'>
                <div style='font-weight: bold; font-size: 1.1rem;'>{metric['name']}</div>
                <div style='font-size: 1.5rem; font-weight: bold; color: {metric['color']};'>{metric['value']} {metric['unit']}</div>
                <div style='color: {status_color}; font-size: 0.9rem;'>{metric['status']} {trend_icon}</div>
                <div style='color: #888; font-size: 0.8rem;'>Normal: {metric['normal_range']}</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Alert notifications for abnormal values
    st.markdown("### Alerts & Notifications")
    alerts = [
        {
            "type": "warning",
            "message": "Blood pressure is elevated. Consider lifestyle changes.",
            "icon": "⚠️"
        },
        {
            "type": "info",
            "message": "Weight trending down - great progress!",
            "icon": "✅"
        }
    ]
    
    for alert in alerts:
        if alert["type"] == "warning":
            st.warning(f"{alert['icon']} {alert['message']}")
        else:
            st.info(f"{alert['icon']} {alert['message']}")
    
    # Trend summary
    st.markdown("### Trend Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Improving", "2", "📈")
    with col2:
        st.metric("Stable", "1", "➡️")
    with col3:
        st.metric("Needs Attention", "1", "⚠️") 