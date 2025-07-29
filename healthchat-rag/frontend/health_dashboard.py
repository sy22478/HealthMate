"""
HealthMate Dashboard - Comprehensive Health Analytics Dashboard
Modern Streamlit-based dashboard for health data visualization and analytics
"""
import streamlit as st
import requests
import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from datetime import datetime, timedelta
import time
from typing import Dict, List, Any, Optional
import os

# Page configuration
st.set_page_config(
    page_title="HealthMate Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .health-score {
        font-size: 2rem;
        font-weight: bold;
        color: #2e7d32;
    }
    .warning {
        color: #f57c00;
    }
    .danger {
        color: #d32f2f;
    }
    .success {
        color: #388e3c;
    }
    .info-box {
        background-color: #e3f2fd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #2196f3;
    }
</style>
""", unsafe_allow_html=True)

class HealthMateDashboard:
    """Main dashboard class for HealthMate application"""
    
    def __init__(self):
        self.base_url = os.getenv("HEALTHMATE_API_URL", "https://healthmate-production.up.railway.app")
        self.session = requests.Session()
        self.auth_token = None
    
    def authenticate(self, email: str, password: str) -> bool:
        """Authenticate user and get access token"""
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"email": email, "password": password}
            )
            
            if response.status_code == 200:
                data = response.json()
                self.auth_token = data.get("access_token")
                self.session.headers.update({"Authorization": f"Bearer {self.auth_token}"})
                return True
            else:
                st.error(f"Authentication failed: {response.text}")
                return False
                
        except Exception as e:
            st.error(f"Authentication error: {str(e)}")
            return False
    
    def get_dashboard_data(self) -> Optional[Dict[str, Any]]:
        """Get comprehensive dashboard data"""
        try:
            response = self.session.get(f"{self.base_url}/advanced-analytics/dashboard")
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                st.error(f"Failed to get dashboard data: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Error fetching dashboard data: {str(e)}")
            return None
    
    def get_health_data(self, days: int = 30) -> Optional[List[Dict[str, Any]]]:
        """Get health data entries"""
        try:
            response = self.session.get(
                f"{self.base_url}/health-data/",
                params={"days": days, "limit": 100}
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                st.error(f"Failed to get health data: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Error fetching health data: {str(e)}")
            return None
    
    def get_analytics(self) -> Optional[Dict[str, Any]]:
        """Get analytics data"""
        try:
            response = self.session.get(f"{self.base_url}/analytics/health-score")
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to get analytics: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Error fetching analytics: {str(e)}")
            return None
    
    def get_visualization_data(self, chart_type: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Get visualization data for specific chart type"""
        try:
            response = self.session.get(
                f"{self.base_url}/visualization/chart/{chart_type}",
                params={"days": days}
            )
            
            if response.status_code == 200:
                return response.json()["data"]
            else:
                st.error(f"Failed to get visualization data: {response.text}")
                return None
                
        except Exception as e:
            st.error(f"Error fetching visualization data: {str(e)}")
            return None

def create_health_trends_chart(data: Dict[str, Any]) -> go.Figure:
    """Create health trends line chart"""
    fig = go.Figure()
    
    if "datasets" in data:
        for dataset in data["datasets"]:
            if "data" in dataset and dataset["data"]:
                df = pd.DataFrame(dataset["data"])
                fig.add_trace(
                    go.Scatter(
                        x=df["x"],
                        y=df["y"],
                        mode="lines+markers",
                        name=dataset.get("label", "Unknown"),
                        line=dict(color=dataset.get("borderColor", "#1f77b4")),
                        marker=dict(size=6)
                    )
                )
    
    fig.update_layout(
        title="Health Trends Over Time",
        xaxis_title="Date",
        yaxis_title="Value",
        height=400,
        showlegend=True,
        hovermode="x unified"
    )
    
    return fig

def create_symptom_distribution_chart(data: Dict[str, Any]) -> go.Figure:
    """Create symptom distribution pie chart"""
    if "datasets" in data and data["datasets"]:
        dataset = data["datasets"][0]
        labels = dataset.get("labels", [])
        values = dataset.get("data", [])
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.3,
            marker_colors=dataset.get("backgroundColor", px.colors.qualitative.Set3)
        )])
        
        fig.update_layout(
            title="Symptom Distribution",
            height=400,
            showlegend=True
        )
        
        return fig
    
    return go.Figure()

def create_medication_adherence_chart(data: Dict[str, Any]) -> go.Figure:
    """Create medication adherence line chart"""
    fig = go.Figure()
    
    if "datasets" in data:
        for dataset in data["datasets"]:
            if "data" in dataset and dataset["data"]:
                df = pd.DataFrame(dataset["data"])
                fig.add_trace(
                    go.Scatter(
                        x=df["x"],
                        y=df["y"],
                        mode="lines+markers",
                        name=dataset.get("label", "Adherence Rate"),
                        line=dict(color=dataset.get("borderColor", "#2196f3")),
                        fill="tonexty",
                        fillcolor="rgba(33, 150, 243, 0.1)"
                    )
                )
    
    fig.update_layout(
        title="Medication Adherence Over Time",
        xaxis_title="Date",
        yaxis_title="Adherence Rate (%)",
        yaxis=dict(range=[0, 100]),
        height=400,
        showlegend=True,
        hovermode="x unified"
    )
    
    return fig

def create_data_completeness_chart(data: Dict[str, Any]) -> go.Figure:
    """Create data completeness doughnut chart"""
    if "datasets" in data and data["datasets"]:
        dataset = data["datasets"][0]
        labels = dataset.get("labels", [])
        values = dataset.get("data", [])
        
        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.6,
            marker_colors=dataset.get("backgroundColor", px.colors.qualitative.Pastel)
        )])
        
        fig.update_layout(
            title="Data Completeness by Type",
            height=400,
            showlegend=True
        )
        
        return fig
    
    return go.Figure()

def create_correlation_heatmap(data: Dict[str, Any]) -> go.Figure:
    """Create correlation matrix heatmap"""
    if "labels" in data and "data" in data:
        labels = data["labels"]
        correlation_matrix = data["data"]
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            x=labels,
            y=labels,
            colorscale="RdYlBu",
            zmid=0,
            text=[[f"{val:.2f}" for val in row] for row in correlation_matrix],
            texttemplate="%{text}",
            textfont={"size": 10},
            hoverongaps=False
        ))
        
        fig.update_layout(
            title="Health Data Correlations",
            height=500,
            xaxis_title="Data Types",
            yaxis_title="Data Types"
        )
        
        return fig
    
    return go.Figure()

def main():
    """Main dashboard application"""
    
    # Initialize dashboard
    dashboard = HealthMateDashboard()
    
    # Header
    st.markdown('<h1 class="main-header">🏥 HealthMate Dashboard</h1>', unsafe_allow_html=True)
    
    # Sidebar for authentication and navigation
    with st.sidebar:
        st.header("🔐 Authentication")
        
        # Check if already authenticated
        if "authenticated" not in st.session_state:
            st.session_state.authenticated = False
        
        if not st.session_state.authenticated:
            email = st.text_input("Email", key="email_input")
            password = st.text_input("Password", type="password", key="password_input")
            
            if st.button("Login", key="login_btn"):
                if email and password:
                    if dashboard.authenticate(email, password):
                        st.session_state.authenticated = True
                        st.success("Authentication successful!")
                        st.rerun()
                    else:
                        st.error("Authentication failed!")
                else:
                    st.warning("Please enter email and password")
        
        if st.session_state.authenticated:
            st.success("✅ Authenticated")
            
            if st.button("Logout", key="logout_btn"):
                st.session_state.authenticated = False
                st.rerun()
            
            st.header("📊 Dashboard Sections")
            section = st.selectbox(
                "Choose Section",
                ["Overview", "Health Trends", "Analytics", "Visualizations", "Data Management"]
            )
            
            st.header("⚙️ Settings")
            days_filter = st.slider("Data Period (Days)", 7, 365, 30)
            
            st.header("ℹ️ Info")
            st.info("""
            **HealthMate Dashboard**
            
            This dashboard provides comprehensive health analytics and visualization capabilities.
            
            **Features:**
            - Real-time health data monitoring
            - Advanced analytics and insights
            - Interactive visualizations
            - Trend analysis and predictions
            """)
    
    # Main content area
    if st.session_state.authenticated:
        if section == "Overview":
            show_overview_section(dashboard, days_filter)
        elif section == "Health Trends":
            show_health_trends_section(dashboard, days_filter)
        elif section == "Analytics":
            show_analytics_section(dashboard, days_filter)
        elif section == "Visualizations":
            show_visualizations_section(dashboard, days_filter)
        elif section == "Data Management":
            show_data_management_section(dashboard, days_filter)
    else:
        st.info("👋 Welcome to HealthMate Dashboard! Please login to access your health data and analytics.")
        
        # Show demo information
        st.markdown("""
        ### 🚀 Features Overview
        
        **Health Analytics Dashboard:**
        - 📊 Real-time health metrics monitoring
        - 📈 Trend analysis and predictions
        - 🏥 Symptom tracking and analysis
        - 💊 Medication adherence monitoring
        - 📋 Comprehensive health insights
        - 🎨 Interactive data visualizations
        
        **Advanced Capabilities:**
        - 🤖 AI-powered health recommendations
        - 🔍 Correlation analysis between health metrics
        - 📱 Responsive design for all devices
        - 🔐 Secure authentication and data protection
        - 📤 Data export and sharing capabilities
        """)

def show_overview_section(dashboard: HealthMateDashboard, days: int):
    """Show overview section with key metrics"""
    st.header("📊 Health Overview")
    
    # Get dashboard data
    with st.spinner("Loading dashboard data..."):
        dashboard_data = dashboard.get_dashboard_data()
    
    if dashboard_data:
        overview = dashboard_data.get("overview", {})
        
        # Key metrics in columns
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            health_score = overview.get("health_score", 0)
            st.metric(
                label="🏥 Health Score",
                value=f"{health_score:.1f}%",
                delta=f"{health_score - 75:.1f}%" if health_score > 75 else f"{health_score - 75:.1f}%"
            )
        
        with col2:
            data_points = overview.get("total_health_data_points", 0)
            st.metric(
                label="📈 Data Points",
                value=data_points,
                delta=f"+{data_points // 10}" if data_points > 0 else "0"
            )
        
        with col3:
            symptoms = overview.get("total_symptoms", 0)
            st.metric(
                label="🤒 Symptoms",
                value=symptoms,
                delta=f"+{symptoms // 5}" if symptoms > 0 else "0"
            )
        
        with col4:
            adherence = overview.get("medication_adherence_rate", 0)
            st.metric(
                label="💊 Adherence",
                value=f"{adherence:.1f}%",
                delta=f"{adherence - 80:.1f}%" if adherence > 80 else f"{adherence - 80:.1f}%"
            )
        
        # Health insights
        st.subheader("🔍 Health Insights")
        insights = dashboard_data.get("health_insights", {})
        
        if insights:
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🎯 Key Recommendations:**")
                recommendations = insights.get("recommendations", [])
                if recommendations:
                    for i, rec in enumerate(recommendations[:5], 1):
                        st.markdown(f"{i}. {rec}")
                else:
                    st.info("No specific recommendations available")
            
            with col2:
                st.markdown("**⚠️ Risk Factors:**")
                risk_factors = insights.get("risk_factors", [])
                if risk_factors:
                    for factor in risk_factors[:5]:
                        st.markdown(f"• {factor}")
                else:
                    st.info("No significant risk factors identified")
        
        # Recent activity
        st.subheader("📅 Recent Activity")
        health_data = dashboard.get_health_data(days)
        
        if health_data:
            df = pd.DataFrame(health_data)
            if not df.empty:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df.sort_values('timestamp', ascending=False)
                
                st.dataframe(
                    df[['data_type', 'value', 'timestamp']].head(10),
                    use_container_width=True
                )
            else:
                st.info("No recent health data available")
        else:
            st.info("Unable to load recent health data")

def show_health_trends_section(dashboard: HealthMateDashboard, days: int):
    """Show health trends section"""
    st.header("📈 Health Trends")
    
    # Get health trends data
    with st.spinner("Loading health trends..."):
        trends_data = dashboard.get_visualization_data("health_trends", days)
    
    if trends_data:
        st.plotly_chart(create_health_trends_chart(trends_data), use_container_width=True)
        
        # Trend analysis
        st.subheader("📊 Trend Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**📈 Improving Trends:**")
            improving = trends_data.get("improving_trends", [])
            if improving:
                for trend in improving:
                    st.markdown(f"✅ {trend}")
            else:
                st.info("No improving trends identified")
        
        with col2:
            st.markdown("**📉 Concerning Trends:**")
            concerning = trends_data.get("concerning_trends", [])
            if concerning:
                for trend in concerning:
                    st.markdown(f"⚠️ {trend}")
            else:
                st.info("No concerning trends identified")
    else:
        st.error("Unable to load health trends data")

def show_analytics_section(dashboard: HealthMateDashboard, days: int):
    """Show analytics section"""
    st.header("📊 Advanced Analytics")
    
    # Get analytics data
    with st.spinner("Loading analytics..."):
        analytics_data = dashboard.get_analytics()
    
    if analytics_data:
        # Health score breakdown
        st.subheader("🏥 Health Score Breakdown")
        
        col1, col2 = st.columns(2)
        
        with col1:
            score_details = analytics_data.get("score_breakdown", {})
            if score_details:
                for category, score in score_details.items():
                    st.metric(
                        label=category.replace("_", " ").title(),
                        value=f"{score:.1f}%"
                    )
        
        with col2:
            # Health score chart
            if "score_history" in analytics_data:
                history = analytics_data["score_history"]
                if history:
                    df = pd.DataFrame(history)
                    fig = px.line(df, x="date", y="score", title="Health Score Timeline")
                    st.plotly_chart(fig, use_container_width=True)
        
        # Symptom analysis
        st.subheader("🤒 Symptom Analysis")
        
        symptom_data = dashboard.get_visualization_data("symptom_distribution", days)
        if symptom_data:
            st.plotly_chart(create_symptom_distribution_chart(symptom_data), use_container_width=True)
        
        # Medication adherence
        st.subheader("💊 Medication Adherence")
        
        adherence_data = dashboard.get_visualization_data("medication_adherence", days)
        if adherence_data:
            st.plotly_chart(create_medication_adherence_chart(adherence_data), use_container_width=True)
    else:
        st.error("Unable to load analytics data")

def show_visualizations_section(dashboard: HealthMateDashboard, days: int):
    """Show visualizations section"""
    st.header("🎨 Data Visualizations")
    
    # Chart type selector
    chart_type = st.selectbox(
        "Select Chart Type",
        ["health_trends", "symptom_distribution", "medication_adherence", 
         "data_completeness", "health_score_timeline", "correlation_matrix"]
    )
    
    # Get visualization data
    with st.spinner(f"Loading {chart_type} data..."):
        viz_data = dashboard.get_visualization_data(chart_type, days)
    
    if viz_data:
        if chart_type == "health_trends":
            st.plotly_chart(create_health_trends_chart(viz_data), use_container_width=True)
        elif chart_type == "symptom_distribution":
            st.plotly_chart(create_symptom_distribution_chart(viz_data), use_container_width=True)
        elif chart_type == "medication_adherence":
            st.plotly_chart(create_medication_adherence_chart(viz_data), use_container_width=True)
        elif chart_type == "data_completeness":
            st.plotly_chart(create_data_completeness_chart(viz_data), use_container_width=True)
        elif chart_type == "correlation_matrix":
            st.plotly_chart(create_correlation_heatmap(viz_data), use_container_width=True)
        else:
            st.plotly_chart(create_health_trends_chart(viz_data), use_container_width=True)
        
        # Chart information
        st.subheader("📋 Chart Information")
        st.json(viz_data)
    else:
        st.error(f"Unable to load {chart_type} data")

def show_data_management_section(dashboard: HealthMateDashboard, days: int):
    """Show data management section"""
    st.header("📋 Data Management")
    
    # Data completeness
    st.subheader("📊 Data Completeness")
    
    completeness_data = dashboard.get_visualization_data("data_completeness", days)
    if completeness_data:
        st.plotly_chart(create_data_completeness_chart(completeness_data), use_container_width=True)
    
    # Health data table
    st.subheader("📈 Health Data Records")
    
    health_data = dashboard.get_health_data(days)
    if health_data:
        df = pd.DataFrame(health_data)
        if not df.empty:
            # Add filters
            col1, col2 = st.columns(2)
            
            with col1:
                data_types = df['data_type'].unique()
                selected_types = st.multiselect("Filter by Data Type", data_types, default=data_types[:3])
            
            with col2:
                date_range = st.date_input(
                    "Date Range",
                    value=(datetime.now() - timedelta(days=days), datetime.now()),
                    max_value=datetime.now()
                )
            
            # Filter data
            if selected_types:
                df = df[df['data_type'].isin(selected_types)]
            
            if len(date_range) == 2:
                start_date, end_date = date_range
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df = df[(df['timestamp'].dt.date >= start_date) & (df['timestamp'].dt.date <= end_date)]
            
            # Display filtered data
            st.dataframe(df, use_container_width=True)
            
            # Export options
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📥 Export as CSV"):
                    csv = df.to_csv(index=False)
                    st.download_button(
                        label="Download CSV",
                        data=csv,
                        file_name=f"health_data_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
            
            with col2:
                if st.button("📊 Export as JSON"):
                    json_data = df.to_json(orient="records", date_format="iso")
                    st.download_button(
                        label="Download JSON",
                        data=json_data,
                        file_name=f"health_data_{datetime.now().strftime('%Y%m%d')}.json",
                        mime="application/json"
                    )
        else:
            st.info("No health data available for the selected period")
    else:
        st.error("Unable to load health data")

if __name__ == "__main__":
    main() 