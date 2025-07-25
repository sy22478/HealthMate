import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import random

def metrics_visualization():
    st.markdown("### Metrics Visualization")
    
    # Date Range Selector
    col1, col2 = st.columns([2, 1])
    with col1:
        date_range = st.selectbox("Time Range", ["Last 7 days", "Last 30 days", "Last 3 months", "Last year"])
    with col2:
        overlay = st.checkbox("Show Multiple Metrics")
    
    # Generate sample data
    if date_range == "Last 7 days":
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, 0, -1)]
        bp_systolic = [random.randint(110, 140) for _ in range(7)]
        bp_diastolic = [random.randint(70, 90) for _ in range(7)]
        weight_data = [random.uniform(149.5, 150.5) for _ in range(7)]
        heart_rate = [random.randint(65, 80) for _ in range(7)]
        mood_data = [random.randint(6, 9) for _ in range(7)]
    else:
        dates = [(datetime.now() - timedelta(days=i*7)).strftime('%Y-%m-%d') for i in range(12, 0, -1)]
        bp_systolic = [random.randint(110, 140) for _ in range(12)]
        bp_diastolic = [random.randint(70, 90) for _ in range(12)]
        weight_data = [random.uniform(149.0, 151.0) for _ in range(12)]
        heart_rate = [random.randint(65, 80) for _ in range(12)]
        mood_data = [random.randint(6, 9) for _ in range(12)]
    
    # Blood Pressure Chart
    st.markdown("**Blood Pressure Trend**")
    fig_bp = go.Figure()
    fig_bp.add_trace(go.Scatter(
        x=dates, y=bp_systolic, mode='lines+markers',
        name='Systolic', line=dict(color='#e76f51', width=3)
    ))
    fig_bp.add_trace(go.Scatter(
        x=dates, y=bp_diastolic, mode='lines+markers',
        name='Diastolic', line=dict(color='#2a9d8f', width=3)
    ))
    fig_bp.update_layout(
        title="Blood Pressure Over Time",
        xaxis_title="Date",
        yaxis_title="Blood Pressure (mmHg)",
        height=400,
        hovermode='x unified'
    )
    st.plotly_chart(fig_bp, use_container_width=True)
    
    # Weight Tracking Chart
    st.markdown("**Weight Tracking**")
    fig_weight = go.Figure()
    fig_weight.add_trace(go.Scatter(
        x=dates, y=weight_data, mode='lines+markers',
        name='Weight', line=dict(color='#e9c46a', width=3)
    ))
    fig_weight.update_layout(
        title="Weight Over Time",
        xaxis_title="Date",
        yaxis_title="Weight (lbs)",
        height=300
    )
    st.plotly_chart(fig_weight, use_container_width=True)
    
    # Heart Rate Chart
    st.markdown("**Heart Rate Variability**")
    fig_hr = go.Figure()
    fig_hr.add_trace(go.Scatter(
        x=dates, y=heart_rate, mode='lines+markers',
        name='Heart Rate', line=dict(color='#264653', width=3)
    ))
    fig_hr.update_layout(
        title="Heart Rate Over Time",
        xaxis_title="Date",
        yaxis_title="Heart Rate (bpm)",
        height=300
    )
    st.plotly_chart(fig_hr, use_container_width=True)
    
    # Mood Tracking Chart
    st.markdown("**Mood Tracking**")
    fig_mood = go.Figure()
    fig_mood.add_trace(go.Scatter(
        x=dates, y=mood_data, mode='lines+markers',
        name='Mood', line=dict(color='#f4a261', width=3)
    ))
    fig_mood.update_layout(
        title="Mood Over Time",
        xaxis_title="Date",
        yaxis_title="Mood (1-10)",
        height=300,
        yaxis=dict(range=[1, 10])
    )
    st.plotly_chart(fig_mood, use_container_width=True)
    
    # Export Options
    st.markdown("**Export Charts**")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Export as PNG"):
            st.success("(Demo) Charts exported as PNG")
    with col2:
        if st.button("Export as PDF"):
            st.success("(Demo) Charts exported as PDF")
    with col3:
        if st.button("Export Data"):
            st.success("(Demo) Data exported as CSV") 