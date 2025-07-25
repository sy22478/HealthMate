import streamlit as st
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

def chat_analytics():
    st.markdown("### Chat Analytics")
    
    # Date Range Selector
    col1, col2 = st.columns([2, 1])
    with col1:
        date_range = st.selectbox("Date Range", ["Last 7 days", "Last 30 days", "Last 3 months", "Last year"])
    with col2:
        view_type = st.selectbox("View", ["Daily", "Weekly", "Monthly"])
    
    # Chat Frequency Chart
    st.markdown("**Conversation Frequency Over Time**")
    
    # Generate sample data
    if date_range == "Last 7 days":
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(7, 0, -1)]
        conversations = [random.randint(1, 5) for _ in range(7)]
    elif date_range == "Last 30 days":
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(30, 0, -1)]
        conversations = [random.randint(0, 3) for _ in range(30)]
    else:
        dates = [(datetime.now() - timedelta(days=i*7)).strftime('%Y-%m-%d') for i in range(12, 0, -1)]
        conversations = [random.randint(5, 15) for _ in range(12)]
    
    # Create line chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=conversations,
        mode='lines+markers',
        name='Conversations',
        line=dict(color='#2a9d8f', width=3),
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Chat Frequency Over Time",
        xaxis_title="Date",
        yaxis_title="Number of Conversations",
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Topic Analysis
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Topic Categories**")
        topics = {
            "Health Concerns": 35,
            "Medication Questions": 25,
            "Lifestyle Advice": 20,
            "Emergency Situations": 10,
            "General Health": 10
        }
        
        for topic, percentage in topics.items():
            st.write(f"{topic}: {percentage}%")
            st.progress(percentage / 100)
    
    with col2:
        st.markdown("**Trending Topics**")
        trending = [
            "Blood pressure management",
            "Diabetes diet",
            "Medication side effects",
            "Exercise recommendations",
            "Sleep quality"
        ]
        
        for i, topic in enumerate(trending, 1):
            st.write(f"{i}. {topic}")
    
    # Word Cloud Placeholder
    st.markdown("**Common Keywords**")
    st.write("(Word cloud visualization would appear here)")
    keywords = ["blood pressure", "medication", "diet", "exercise", "symptoms", "doctor", "health", "monitoring"]
    st.write("Most common words: " + ", ".join(keywords[:5])) 